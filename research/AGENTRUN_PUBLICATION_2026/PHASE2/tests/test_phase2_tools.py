"""Tests for the Phase 2 completion tools: seal checks, component report statistics, power simulation."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

P2 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P2 / "scripts"))
sys.path.insert(0, str(P2 / "benchmark"))

import component_report as cr  # noqa: E402
import power_phase3 as pw  # noqa: E402


def test_seal_checks_pass_on_p2val(tmp_path):
    for f in (P2 / "data" / "p2val").glob("p2val_*.jsonl"):
        shutil.copy(f, tmp_path / f.name)
    r = subprocess.run([sys.executable, str(P2 / "benchmark" / "seal_checks.py"), "--split", "p2val", "--dir", str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads((tmp_path / "p2val_SEAL_CHECKS.json").read_text())
    c = out["checks"]
    assert out["hard_checks_pass"] and c["writer_input_leak"] == 0 and c["dup_entities_within"] == 0
    assert c["entities_in_own_slice"] == [88, 88]
    assert "Project" not in json.dumps(out)  # counts only, no entity names


def test_seal_checks_detect_leak(tmp_path):
    for f in (P2 / "data" / "p2val").glob("p2val_*.jsonl"):
        shutil.copy(f, tmp_path / f.name)
    wi = tmp_path / "p2val_writer_input.jsonl"
    rows = [json.loads(x) for x in wi.read_text(encoding="utf-8").splitlines() if x.strip()]
    rows[0]["gold"] = {"kind": "conflict"}
    wi.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(P2 / "benchmark" / "seal_checks.py"), "--split", "p2val", "--dir", str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 3


def test_paired_and_holm():
    a = {f"i{k}": 1 for k in range(10)}
    b = {f"i{k}": int(k < 2) for k in range(10)}
    fams = {f"i{k}": f"f{k}" for k in range(10)}
    res = cr.paired(a, b, fams)
    assert res["diff"] == 0.8 and res["n_families"] == 10
    assert res["p_signflip"] == round(2 / 2 ** 8, 5)  # 8 non-zero families, all positive, exact
    assert res["ci95"][0] <= 0.8 <= res["ci95"][1]
    assert cr.holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]


def test_power_simulation_monotone():
    by_cat = {"c1": {"t1": [("m", 0.0)], "t2": [("m", 1.0)]}, "c2": {"t3": [("m", 0.0)], "t4": [("m", 1.0)]}}
    hi = pw.simulate(by_cat, ["m"], 100, 2, 1.0, [0.05], 300, 1)["0.05"]
    lo = pw.simulate(by_cat, ["m"], 10, 2, 0.2, [0.05], 300, 1)["0.05"]
    assert hi > 0.95 and lo < hi


def test_generator_audit_hard_checks(tmp_path):
    r = subprocess.run([sys.executable, str(P2 / "benchmark" / "audit_generators.py"), "--out", str(tmp_path / "a.json")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    out = json.loads((tmp_path / "a.json").read_text())
    assert out["splits"]["eval3"]["skeleton_sha256"].startswith("(not reported")
    assert "by_gold_kind" not in out["splits"]["eval3"]


def test_dryrun_pipeline_end_to_end(tmp_path):
    r = subprocess.run([sys.executable, str(P2 / "scripts" / "dryrun_pipeline.py"), "--tasks",
                        str(P2 / "data" / "p2val" / "p2val_tasks.jsonl"), "--out", str(tmp_path), "--limit", "6",
                        "--n-perm", "500", "--drop", "0.05"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    assert '"loop_exceptions": 0' in r.stdout
    res = json.loads((tmp_path / "dryrun_analysis.json").read_text())
    c = res["contrasts"]["EBG-RT"]["ALL"]["success"]
    assert c["confirmatory"] and res["per_model"]["ALL"]["EBG"]["n"] == 18  # 6 tasks x 3 simulated models, missing included


def test_subset_tasks(tmp_path):
    ids = tmp_path / "ids.json"
    tasks = P2 / "data" / "p2val" / "p2val_tasks.jsonl"
    first = [json.loads(x)["task_id"] for x in tasks.read_text(encoding="utf-8").splitlines()[:5]]
    ids.write_text(json.dumps(first))
    r = subprocess.run([sys.executable, str(P2 / "scripts" / "subset_tasks.py"), "--tasks", str(tasks), "--ids", str(ids),
                        "--out", str(tmp_path / "p.jsonl")], capture_output=True, text=True)
    out = json.loads(r.stdout)
    assert out["n_primary"] == 5 and out["n_flagged"] == 72 and out["ids_without_task"] == 0
