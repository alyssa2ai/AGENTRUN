"""Scoring predicates in eval/harness.py, exercised with synthetic traces.

score_task() reads only a handful of trace attributes, so a small stand-in
object is enough; the Gemini/MCP agent stack is not imported.
"""

from dataclasses import dataclass, field

from eval.harness import _extract_numbers, score_task
from eval.tasks import TASKS, Task

TASK_BY_ID = {t.id: t for t in TASKS}


@dataclass
class Call:
    tool_name: str
    is_error: bool = False


@dataclass
class Trace:
    final_answer: str
    tool_calls: list = field(default_factory=list)
    hit_max_steps: bool = False

    @property
    def tool_names_called(self) -> set:
        return {c.tool_name for c in self.tool_calls}

    @property
    def had_tool_error(self) -> bool:
        return any(c.is_error for c in self.tool_calls)


def test_extract_numbers_handles_commas_negatives_decimals():
    assert _extract_numbers("Total: 305,989 and -12.5, then 7") == [305989.0, -12.5, 7.0]
    assert _extract_numbers("no digits here") == []


def test_pass_when_tool_called_and_number_matches():
    task = TASK_BY_ID["calc_basic_1"]  # 128 * 47 = 6016
    r = score_task(task, Trace("The answer is 6,016.", [Call("calculator")]))
    assert r.success and r.failure_reasons == []


def test_correct_number_without_required_tool_fails():
    task = TASK_BY_ID["calc_basic_1"]
    r = score_task(task, Trace("6016"))
    assert not r.success
    assert any(x.startswith("missing_required_tools") for x in r.failure_reasons)


def test_numeric_tolerance_enforced():
    task = TASK_BY_ID["calc_basic_1"]
    r = score_task(task, Trace("about 6020", [Call("calculator")]))
    assert any(x.startswith("numeric_mismatch") for x in r.failure_reasons)


def test_unexpected_tool_error_fails():
    task = TASK_BY_ID["calc_basic_1"]
    r = score_task(task, Trace("6016", [Call("calculator", is_error=True)]))
    assert any(x.startswith("tool_execution_error") for x in r.failure_reasons)


def test_expected_tool_error_is_required():
    task = TASK_BY_ID["adversarial_division_by_zero"]
    assert task.expect_tool_error
    no_err = score_task(task, Trace("It is undefined.", [Call("calculator")]))
    assert "expected_tool_error_but_none_occurred" in no_err.failure_reasons
    # Answering directly without the tool also fails (this is why Base and V1 failed it).
    no_tool = score_task(task, Trace("Division by zero is undefined."))
    assert not no_tool.success


def test_hit_max_steps_is_a_failure_even_with_correct_answer():
    task = TASK_BY_ID["calc_basic_1"]
    r = score_task(task, Trace("6016", [Call("calculator")], hit_max_steps=True))
    assert r.failure_reasons == ["hit_max_steps"]


def test_all_failure_reasons_are_collected():
    task = Task(
        id="synthetic",
        prompt="p",
        required_tools={"calculator", "word_count"},
        answer_contains=["alpha"],
        answer_contains_any=["x", "y"],
        numeric_check=(10.0, 0.1),
    )
    r = score_task(task, Trace("nothing useful", hit_max_steps=True))
    kinds = {reason.split(":")[0] for reason in r.failure_reasons}
    assert kinds == {
        "missing_required_tools",
        "hit_max_steps",
        "missing_expected_content",
        "missing_expected_content_any",
        "numeric_mismatch",
    }


def test_substring_checks_are_case_insensitive():
    task = Task(id="s", prompt="p", answer_contains=["Paris"], answer_contains_any=["FRANCE", "eu"])
    assert score_task(task, Trace("paris, france")).success
