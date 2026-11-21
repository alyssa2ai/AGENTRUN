"""Statistics helpers of the pre-registered analysis (scripts/analyze_p2.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import analyze_p2 as A  # noqa: E402


def row(model, dec, tid, cfg, ok, fam="f1"):
    return {"model": model, "decoding": dec, "task_id": tid, "config": cfg, "success": ok, "harmful": False,
            "scenario": fam, "variant": "v"}


def test_paired_averages_decodings_within_task_and_pairs_within_decoding():
    rows = [row("m", "greedy", "t1", "X", 1), row("m", "greedy", "t1", "Y", 0),
            row("m", "s1", "t1", "X", 0), row("m", "s1", "t1", "Y", 0),
            row("m", "s2", "t1", "X", 1)]  # s2 has no Y: not paired
    diffs, fam, _ = A.paired(rows, "X", "Y")
    assert diffs == {("m", "t1"): 0.5}


def test_signflip_exact_small():
    assert A.signflip({"a": 1.0, "b": 1.0, "c": 1.0}, 1000) == 2 / 8
    assert A.signflip({"a": 0.0}, 1000) is None


def test_holm_and_bh():
    h = A.holm({"x": 0.01, "y": 0.04, "z": 0.03})
    assert abs(h["x"] - 0.03) < 1e-12 and abs(h["z"] - 0.06) < 1e-12 and abs(h["y"] - 0.06) < 1e-12
    b = A.bh({"x": 0.01, "y": 0.04, "z": 0.03})
    assert abs(b["x"] - 0.03) < 1e-12 and abs(b["y"] - 0.04) < 1e-12


def test_boot_ci_contains_point_estimate():
    fam = {f"f{i}": (1.0 if i % 2 else 0.0) for i in range(20)}
    fam_n = {k: 1 for k in fam}
    lo, hi = A.boot_ci(fam, fam_n, n=2000)
    assert lo <= 50.0 <= hi
