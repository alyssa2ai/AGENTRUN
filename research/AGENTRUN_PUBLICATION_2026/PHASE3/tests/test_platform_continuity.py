"""Tests for the reporting-only G5 platform-continuity check (scripts/platform_continuity.py)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

P3 = Path(__file__).resolve().parents[1]
SCRIPTS = P3 / "scripts"
sys.path.insert(0, str(SCRIPTS))

import platform_continuity as pc  # noqa: E402

EVIDENCE = P3 / "platform_evidence.json"
BOOT = "2026-11-20T10:11:58"


def write_cell(root, name, starts, rows_per_start, configs=("B", "G", "R")):
    d = root / f"eval3_{name}"
    d.mkdir(parents=True)
    with open(d / "manifest.jsonl", "w", encoding="utf-8") as f:
        done = 0
        for i, (job, started, mem) in enumerate(starts):
            f.write(json.dumps({"slurm_job_id": job, "started_utc": started, "resumed_with_done": done,
                                "client": {"gpu_mem_gib": mem}}) + "\n")
            done += rows_per_start[i]
    with open(d / "runs.jsonl", "w", encoding="utf-8") as f:
        n = 0
        total = sum(rows_per_start)
        t = 0
        while n < total:
            for c in configs:
                if n >= total:
                    break
                f.write(json.dumps({"task_id": f"t-{t:04d}", "config": c}) + "\n")
                n += 1
            t += 1
    (d / "DONE").write_text("{}")
    return d


def run_report(tmp_path, raw):
    oj, om = tmp_path / "pc.json", tmp_path / "pc.md"
    rc = subprocess.run([sys.executable, str(SCRIPTS / "platform_continuity.py"), "--raw", str(raw),
                         "--evidence", str(EVIDENCE), "--out-json", str(oj), "--out-md", str(om)],
                        capture_output=True, text=True)
    return rc, json.loads(oj.read_text(encoding="utf-8")), om.read_text(encoding="utf-8")


def test_evidence_file_declares_a_status_for_every_fact():
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    facts = {k: v for k, v in ev.items() if isinstance(v, dict)}
    assert facts, "no facts recorded"
    for k, v in facts.items():
        assert v.get("status") in ("verified", "inferred", "unknown"), (k, v.get("status"))
        if v["status"] == "inferred":
            assert v.get("reasoning"), f"{k}: an inferred fact must carry its reasoning"
        if v["status"] == "unknown":
            assert v.get("would_settle"), f"{k}: an unknown fact must say what would settle it"


def test_reports_a_straddling_cell_without_failing(tmp_path):
    raw = tmp_path / "raw"
    write_cell(raw, "clean", [("4100", "2026-11-18T00:00:00Z", 44.6)], [12])
    write_cell(raw, "straddler", [("4315", "2026-11-19T05:48:56Z", 44.6),
                                  ("4326", "2026-11-20T10:17:51Z", 44.4)], [6, 6])
    rc, out, md = run_report(tmp_path, raw)
    assert rc.returncode == 0, rc.stderr          # reporting only: never fails the pipeline
    assert out["reporting_only"] is True
    assert out["affected_cells"] == ["straddler"]
    assert out["cells_straddling_boot"] == 1 and out["cells_total"] == 2
    assert out["rows_after_boot"] == 6 and out["rows_total"] == 24
    assert "44.6" in md and "44.4" in md


def test_a_cell_restarted_before_the_boot_does_not_straddle(tmp_path):
    raw = tmp_path / "raw"
    write_cell(raw, "early_resume", [("4000", "2026-11-18T00:00:00Z", 44.6),
                                     ("4001", "2026-11-18T06:00:00Z", 44.6)], [6, 6])
    rc, out, _ = run_report(tmp_path, raw)
    assert rc.returncode == 0
    assert out["affected_cells"] == [] and out["rows_after_boot"] == 0


def test_markdown_separates_the_three_epistemic_statuses(tmp_path):
    raw = tmp_path / "raw"
    write_cell(raw, "clean", [("4100", "2026-11-18T00:00:00Z", 44.6)], [12])
    _, out, md = run_report(tmp_path, raw)
    assert "Directly verified" in md and "Inferred from historical records" in md and "Not established" in md
    assert out["facts_by_status"]["verified"], "no verified facts carried through"
    assert "nvidia_module_before" in out["facts_by_status"]["inferred"]
    assert "driver_effect_on_generation" in out["facts_by_status"]["unknown"]
    assert "would settle it" in md


RAW_CANDIDATES = [Path.home() / "AGENTRUN_HPC" / "phase3_raw", P3 / "RAW_RESULTS"]
RAW = next((p for p in RAW_CANDIDATES if p.exists() and any(p.glob("eval3_*/manifest.jsonl"))), None)


@pytest.mark.skipif(RAW is None, reason="campaign raw results not present on this machine")
def test_real_campaign_numbers(tmp_path):
    rc, out, _ = run_report(tmp_path, RAW)
    assert rc.returncode == 0
    assert out["cells_total"] == 18
    assert sorted(out["affected_cells"]) == sorted(["qwen3_8b_T07_s3", "llama32_3b_greedy"])
    assert out["rows_total"] == 57888
    assert out["rows_after_boot"] == 980
    by_cell = {c["cell"]: c for c in out["cells"]}
    assert by_cell["qwen3_8b_T07_s3"]["rows_after_boot"] == 871
    assert by_cell["llama32_3b_greedy"]["rows_after_boot"] == 109
    assert [t["task_id"] for t in by_cell["qwen3_8b_T07_s3"]["tasks_split_across_starts"]] == ["eval3-0202"]
    assert [t["task_id"] for t in by_cell["llama32_3b_greedy"]["tasks_split_across_starts"]] == ["eval3-0267"]
    for c in out["cells"]:
        if c["cell"] not in ("qwen3_8b_T07_s3", "llama32_3b_greedy"):
            assert c["starts"] == 1 and c["rows_after_boot"] == 0, c["cell"]
