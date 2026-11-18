"""End-to-end test of the Phase 3 analysis pipeline on development data (p2val2), including the multi-decoding path
that the dry run (greedy only) does not exercise: a second decoding cell is derived from a real p2val2 run with some
pairs removed, so the frozen analysis must average decodings within task and count missing pairs as failures.
No eval3 data is used.  Run:  python -m pytest PHASE3/tests -q
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

P3 = Path(__file__).resolve().parents[1]
P2 = P3.parent / "PHASE2"
TASKS = P2 / "data" / "p2val2" / "p2val2_tasks.jsonl"
SRC = P2 / "raw" / "p2val2_qwen25_3b_greedy"
pytestmark = pytest.mark.skipif(not SRC.exists() or not TASKS.exists(), reason="p2val2 development runs not present")


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=P3)


@pytest.fixture(scope="module")
def cells(tmp_path_factory):
    root = tmp_path_factory.mktemp("cells")
    a = root / "dev_qwen25_3b_greedy"
    shutil.copytree(SRC, a)
    b = root / "dev_qwen25_3b_T07_s1"
    b.mkdir()
    man = [json.loads(x) for x in (SRC / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    man[0]["temperature"], man[0]["seed"], man[0]["run_id"] = 0.7, 1, b.name
    (b / "manifest.jsonl").write_text(json.dumps(man[0]) + "\n", encoding="utf-8")
    lines = [x for x in (SRC / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    (b / "runs.jsonl").write_text("\n".join(lines[: len(lines) - 30]) + "\n", encoding="utf-8")  # 30 missing pairs
    (b / "DONE").write_text(json.dumps({"finished_utc": "2026-11-18T00:00:00Z", "runs": len(lines) - 30}))
    return root, [a, b]


def test_analysis_crosscheck_verify_and_reports(cells):
    root, dirs = cells
    out = root / "A"
    out.mkdir()
    r = run(P2 / "scripts" / "analyze_p2.py", "--tasks", TASKS, "--runs", *dirs, "--out", out / "CONFIRMATORY_primary_cells",
            "--holm", "EBG-RT,EBG-T,EBG-LG,EBG-B", "--n-perm", "500")
    assert r.returncode == 0, r.stderr
    res = json.loads((out / "CONFIRMATORY_primary_cells.json").read_text(encoding="utf-8"))
    assert res["per_model"]["ALL"]["EBG"]["n"] == 2 * 90
    assert sum(x["missing"] for x in res["per_model"]["ALL"].values()) == 30
    c = res["contrasts"]["EBG-RT"]["ALL"]["success"]
    assert c["n_task_pairs"] == 90 and c["confirmatory"] and c["p_holm"] is not None
    r = run("scripts/crosscheck_phase3.py", "--tasks", TASKS, "--runs", *dirs, "--analysis",
            out / "CONFIRMATORY_primary_cells.json", "--out", out / "CROSSCHECK")
    assert r.returncode == 0, r.stdout + r.stderr
    r = run("scripts/verify_phase3.py", "--tasks", TASKS, "--cells", *dirs, "--out", out / "COMPLETENESS", "--dry")
    assert r.returncode == 0, r.stdout + r.stderr
    comp = json.loads((out / "COMPLETENESS.json").read_text(encoding="utf-8"))
    assert [x["missing"] for x in comp["cells"]] == [0, 30]
    r = run("scripts/phase3_metrics.py", "--tasks", TASKS, "--runs", *dirs, "--out", out / "METRICS")
    assert r.returncode == 0, r.stderr
    met = json.loads((out / "METRICS.json").read_text(encoding="utf-8"))
    assert set(met["by_decoding"]["Qwen/Qwen2.5-3B-Instruct"]) == {"greedy", "T0.7_s1"}
    rep = root / "reports"
    r = run("scripts/build_reports.py", "--src", out, "--dest", rep, "--cells", *dirs, "--dry")
    assert r.returncode == 0, r.stderr
    for n in ("EXECUTION_LOG", "COMPARISON_TABLES", "ABLATION_RESULTS", "STATISTICAL_ANALYSIS", "FAILURE_TABLES"):
        assert (rep / f"PHASE3_{n}.md").stat().st_size > 200
    dec = json.loads((rep / "PHASE3_DECISIONS.json").read_text(encoding="utf-8"))
    assert set(dec["hypotheses"]) == {"H-primary", "S1", "S2", "S3", "S4"}
    assert (rep / "results" / "contrasts_primary_cells.csv").exists()


def test_execution_log_parses_start_and_exit_lines(tmp_path):
    sys.path.insert(0, str(P3 / "scripts"))
    import build_reports as B
    (tmp_path / "phase3_4259_16.out").write_text(
        "freeze evarb-0.2 mismatches []\n"
        "start 2026-11-18T08:58:22+00:00 job=4259_16 model=Qwen/Qwen2.5-14B-Instruct decoding=greedy CUDA_VISIBLE_DEVICES=1\n"
        "[ 10s] x B -> correct\nexit=0 2026-11-18T18:58:22+00:00 Qwen/Qwen2.5-14B-Instruct greedy\n", encoding="utf-8")
    seg = B.log_segments(tmp_path)
    s = seg[("Qwen/Qwen2.5-14B-Instruct", "greedy")][0]
    assert s["hours"] == 10.0 and s["gpu"] == "1" and s["rc"] == 0 and s["job"] == "4259_16"


def test_verdict_rules_follow_preregistration():
    sys.path.insert(0, str(P3 / "scripts"))
    import build_reports as B
    assert B.verdict({"p_holm": 0.01, "ci95_pp": [1.0, 5.0], "mean_diff_pp": 3.0}).startswith("SUPPORTED")
    assert B.verdict({"p_holm": 0.2, "ci95_pp": [-1.0, 5.0], "mean_diff_pp": 2.0}).startswith("NOT SUPPORTED")
    assert B.verdict({"p_holm": 0.01, "ci95_pp": [-6.0, -1.0], "mean_diff_pp": -3.0}).startswith("FALSIFIED")
    assert B.verdict({"p_holm": 0.03, "ci95_pp": [-5.0, 0.0], "mean_diff_pp": -2.0}).startswith("FALSIFIED")
