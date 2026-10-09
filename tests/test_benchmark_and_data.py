"""Benchmark-definition and training-data invariants.

These pin the facts the README and paper state about the benchmark and the
two training sets, so a silent edit to either is caught. CPU only; no model,
network, or API key needed.
"""

import json
from collections import Counter
from pathlib import Path

from eval.tasks import TASKS

ROOT = Path(__file__).resolve().parents[1]
TOOLS = {"calculator", "word_count", "web_search", "get_weather"}

EXPECTED_CATEGORIES = {
    "math": 3,
    "text": 1,
    "weather": 2,
    "search": 2,
    "multi_tool": 4,
    "chained_reasoning": 1,
    "time_sensitive": 1,
    "no_tool_expected": 2,
    "adversarial_math": 3,
    "adversarial_reasoning": 2,
    "adversarial_error_handling": 1,
    "adversarial_ambiguity": 1,
}


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def _load_jsonl(name: str) -> list[dict]:
    path = ROOT / "training" / name
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _user_prompts(rows: list[dict]) -> list[str]:
    return [m["content"] for r in rows for m in r["messages"] if m["role"] == "user"]


def test_benchmark_has_23_unique_tasks():
    ids = [t.id for t in TASKS]
    assert len(ids) == 23
    assert len(set(ids)) == 23


def test_benchmark_category_counts():
    assert Counter(t.category for t in TASKS) == EXPECTED_CATEGORIES


def test_required_tools_are_known():
    for t in TASKS:
        assert t.required_tools <= TOOLS, f"{t.id} requires unknown tool {t.required_tools - TOOLS}"


def test_predicate_strength_is_as_documented():
    """Pin how strong each task's scoring predicate is (see docs/benchmark.md).

    Every task also fails on hit_max_steps and on an unexpected tool error.
    Beyond that: 15 tasks check answer content; 7 check only that the
    required tools were called (live weather/search outputs are not
    verifiable offline); 1 (no_tool_needed_2) has no positive check at all.
    The benchmark is frozen, so this test documents rather than fixes that.
    """
    content = {t.id for t in TASKS if t.answer_contains or t.answer_contains_any or t.numeric_check}
    tool_only = {t.id for t in TASKS if t.required_tools and t.id not in content}
    unchecked = {t.id for t in TASKS if not t.required_tools and t.id not in content}
    assert len(content) == 15
    assert tool_only == {
        "weather_basic_1",
        "weather_basic_2",
        "search_basic_1",
        "multi_search_weather",
        "chain_weather_then_calc",
        "time_sensitive_1",
        "adversarial_ambiguous_city",
    }
    assert unchecked == {"no_tool_needed_2"}


def test_training_set_sizes():
    v1 = _load_jsonl("training_data.jsonl")
    v2 = _load_jsonl("training_data_augmented.jsonl")
    assert len(v1) == 35
    assert len(v2) == 46
    # V2 = the 35 V1 trajectories, unchanged and in order, plus 11 additions.
    assert v2[:35] == v1


def test_added_prompts_file_matches_augmented_set():
    from training.training_data_prompts_augmented import NEW_TRAINING_PROMPTS

    v2 = _load_jsonl("training_data_augmented.jsonl")
    assert len(NEW_TRAINING_PROMPTS) == 11
    assert _user_prompts(v2[35:]) == NEW_TRAINING_PROMPTS


def test_training_prompts_disjoint_from_benchmark_prompts():
    """Prompt-level disjointness only.

    This does NOT establish category- or template-level independence: several
    added V2 prompts follow the same template as a benchmark task (e.g.
    'What is 25 divided by 0?' vs. the benchmark's 'What is 50 divided by 0?').
    """
    eval_prompts = {_norm(t.prompt) for t in TASKS}
    for name in ("training_data.jsonl", "training_data_augmented.jsonl"):
        overlap = [p for p in _user_prompts(_load_jsonl(name)) if _norm(p) in eval_prompts]
        assert overlap == [], f"{name} reuses benchmark prompts: {overlap}"
