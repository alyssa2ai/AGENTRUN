"""Cross-checks between the committed result artifacts.

Every number stated in the README and the paper is recomputed here from the
per-task records in results/, independently of results/verify_results.py.
"""

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

CONDITIONS = {
    "Base": ("eval_results_base.json", 22),
    "V1": ("eval_results_v1.json", 18),
    "E4": ("eval_results_e4.json", 18),
    "V2": ("eval_results_v2.json", 23),
}


def _load(name: str) -> dict:
    with open(RESULTS / name, encoding="utf-8") as f:
        return json.load(f)


def _outcomes(d: dict) -> dict[str, bool]:
    return {r["task_id"]: bool(r.get("success", r.get("passed"))) for r in d["results"]}


@pytest.fixture(scope="module")
def outcomes() -> dict[str, dict[str, bool]]:
    return {c: _outcomes(_load(f)) for c, (f, _) in CONDITIONS.items()}


@pytest.mark.parametrize("cond", list(CONDITIONS))
def test_reported_totals_match_per_task_tally(cond):
    fname, expected = CONDITIONS[cond]
    d = _load(fname)
    tally = sum(_outcomes(d).values())
    assert len(d["results"]) == 23
    assert tally == d["passed"] == expected


def test_same_23_task_ids_in_every_condition(outcomes):
    from eval.tasks import TASKS

    ids = {t.id for t in TASKS}
    for cond, o in outcomes.items():
        assert set(o) == ids, cond


def test_parser_ablation_transitions(outcomes):
    """V1 -> E4: same adapter; parser (and, as run, evaluation client) changed."""
    v1, e4 = outcomes["V1"], outcomes["E4"]
    recovered = sorted(t for t in v1 if not v1[t] and e4[t])
    regressed = sorted(t for t in v1 if v1[t] and not e4[t])
    assert recovered == ["adversarial_false_premise", "multi_three_tools"]
    assert regressed == ["adversarial_chained_search_calc", "multi_search_weather"]


def test_e4_to_v2_transitions(outcomes):
    e4, v2 = outcomes["E4"], outcomes["V2"]
    assert all(v2.values())
    assert sorted(t for t in e4 if not e4[t]) == [
        "adversarial_chained_search_calc",
        "adversarial_division_by_zero",
        "chain_weather_then_calc",
        "multi_search_weather",
        "multi_wordcount_calc",
    ]


def test_base_only_failure(outcomes):
    assert [t for t, ok in outcomes["Base"].items() if not ok] == ["adversarial_division_by_zero"]


def test_v1_alias_file_is_identical():
    assert _load("eval_results_finetuned.json") == _load("eval_results_v1.json")


def test_raw_notebook_e4_export_agrees():
    raw = _load("eval_results_e4_notebook_raw.json")
    assert _outcomes(raw) == _outcomes(_load("eval_results_e4.json"))
    assert raw["passed"] == 18


def test_experiment_summary_agrees(outcomes):
    s = _load("experiment_summary.json")["results"]
    for key, cond in [("base", "Base"), ("v1_lora", "V1"), ("e4_lora_fixed_parser", "E4"), ("v2_lora", "V2")]:
        assert s[key]["passed"] == sum(outcomes[cond].values()), key
        assert sorted(s[key]["failed_tasks"]) == sorted(t for t, ok in outcomes[cond].items() if not ok), key


def test_verified_csv_agrees(outcomes):
    with open(RESULTS / "results_verified.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 23
    for row in rows:
        for cond in CONDITIONS:
            assert (row[cond] == "PASS") == outcomes[cond][row["task_id"]]
