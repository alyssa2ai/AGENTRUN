"""The calculator tool must behave exactly like the eval()-based version used
for the reported runs, except that huge exponents are rejected."""

import pytest

from tools import CALCULATOR_TOOL, calculator

EXPRESSIONS = [
    "128 * 47",
    "12 * (3 + 4)",
    "2 + 3 * 4 - 10 / 2",
    "-45 * 23",
    "1000 / 7",
    "0.15 * 2400",
    "7 // 2",
    "-(3 - 10)",
    "2 ** 10",
    "  6016  ",
    "(25 - 32) * 5 / 9",
    "1.5e3",
]


def _reference(expression: str) -> str:
    # The original implementation, kept here as the oracle.
    return str(eval(expression.strip(), {"__builtins__": {}}, {}))


@pytest.mark.parametrize("expr", [e for e in EXPRESSIONS if "e" not in e])
def test_matches_original_eval(expr):
    assert calculator(expr) == _reference(expr)


def test_invalid_characters_rejected_without_error_prefix():
    # Unchanged behaviour: returned as a plain observation, not an "ERROR" string.
    assert calculator("__import__('os')") == "Invalid characters in expression."
    assert calculator("1.5e3") == "Invalid characters in expression."


def test_division_by_zero_is_a_tool_error():
    # The benchmark's adversarial_division_by_zero task relies on this prefix.
    out = CALCULATOR_TOOL.run(expression="50 / 0")
    assert out.startswith("ERROR running tool 'calculator':")
    assert "division by zero" in out


def test_huge_exponent_is_rejected_quickly():
    out = CALCULATOR_TOOL.run(expression="9 ** 9 ** 9 ** 9")
    assert out.startswith("ERROR") and "exponent too large" in out


def test_syntax_error_is_a_tool_error():
    assert CALCULATOR_TOOL.run(expression="3 +* 4").startswith("ERROR")
