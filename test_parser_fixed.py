#!/usr/bin/env python3
r"""
test_parser_fixed.py - Focused test for the two-pass parser fix in colab_server_v2.py
Tests that the v2 parser correctly handles malformed tool-call output that
would cause the v1 parser to fail.

IMPORTANT note on pass-2 scope:
  The v2 pass-2 regex is r"<tool_call>\s*(\{.*?\})" with re.DOTALL.
  Because \{.*?\} stops at the FIRST closing }, it can only recover
  tool calls whose JSON has no nested object at all — an "arguments"
  member is nested, so even "arguments": {} truncates the capture and
  fails json.loads. For nested args like {"arguments": {"query": "..."}}
  the same happens.
  Pass 1 (strict closed-block) handles nested args correctly.
"""

import os
import re
import json

# Transcribed from serving/colab_server.py and serving/colab_server_v2.py.
# Kept at module level so test_test_parsers_match_serving_sources can pin them.
TOOL_CALL_CLOSED = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
TOOL_CALL_OPEN = re.compile(r"<tool_call>\s*(\{.*?\})", re.DOTALL)


def v1_parse_model_output(raw_text: str) -> dict:
    """Extract from colab_server.py - single-pass regex"""
    TOOL_CALL_PATTERN = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
    matches = TOOL_CALL_PATTERN.findall(raw_text)
    if matches:
        tool_calls = []
        for m in matches:
            try:
                parsed = json.loads(m)
                tool_calls.append({
                    "name": parsed.get("name"),
                    "arguments": parsed.get("arguments", {}),
                })
            except json.JSONDecodeError:
                continue
        if tool_calls:
            return {"tool_calls": tool_calls, "text": None}
    return {"tool_calls": [], "text": raw_text.strip()}


def v2_parse_model_output(raw_text: str) -> dict:
    """Extract from colab_server_v2.py - two-pass parser"""
    matches = TOOL_CALL_CLOSED.findall(raw_text)
    if matches:
        tool_calls = []
        for m in matches:
            try:
                parsed = json.loads(m)
                name = parsed.get("name")
                if name:
                    tool_calls.append({"name": name, "arguments": parsed.get("arguments", {})})
            except json.JSONDecodeError:
                continue
        if tool_calls:
            return {"tool_calls": tool_calls, "text": None}

    first_open = TOOL_CALL_OPEN.search(raw_text)
    if first_open:
        json_str = first_open.group(1)
        try:
            parsed = json.loads(json_str)
            name = parsed.get("name")
            if name:
                return {
                    "tool_calls": [{"name": name, "arguments": parsed.get("arguments", {})}],
                    "text": None,
                }
        except json.JSONDecodeError:
            pass

    return {"tool_calls": [], "text": raw_text.strip()}


# ── Pass-1 tests ─────────────────────────────────────────────────────────────

def test_v1_succeeds_well_formed():
    """v1 handles a well-formed closed block with nested arguments."""
    raw = '<tool_call>\n{"name": "web_search", "arguments": {"query": "Paris population 2024"}}\n</tool_call>'
    result = v1_parse_model_output(raw)
    assert result["tool_calls"][0]["name"] == "web_search"
    assert result["tool_calls"][0]["arguments"]["query"] == "Paris population 2024"
    print("PASS test_v1_succeeds_well_formed")


def test_v2_pass1_succeeds_well_formed():
    """v2 pass-1 handles a well-formed closed block with nested arguments."""
    raw = '<tool_call>\n{"name": "calculator", "arguments": {"expression": "sqrt(144)"}}\n</tool_call>'
    result = v2_parse_model_output(raw)
    assert result["tool_calls"][0]["name"] == "calculator"
    assert result["tool_calls"][0]["arguments"]["expression"] == "sqrt(144)"
    print("PASS test_v2_pass1_succeeds_well_formed")


def test_v1_fails_malformed_no_closing_tag():
    """v1 returns no tool_calls when <tool_call> has no closing </tool_call>."""
    # Model emits opening tags without closing tags
    raw = '<tool_call>\n{"name": "word_count", "arguments": {}}\n<tool_call>\n'
    result = v1_parse_model_output(raw)
    assert result["tool_calls"] == [], f"Expected v1 to fail: {result}"
    print("PASS test_v1_fails_malformed_no_closing_tag")


# ── Pass-2 tests ─────────────────────────────────────────────────────────────

def test_v2_pass2_recovers_flat_args():
    """v2 pass-2 recovers a tool call whose JSON has no nested object.

    Pass-2 limitation: the regex r'<tool_call>\\s*(\\{.*?\\})' stops at the
    first '}', so it can only recover calls with no "arguments" member (or no
    arguments at all). Any nested object — including an EMPTY one such as
    "arguments": {} — truncates the capture and fails json.loads.
    test_v2_pass2_nested_args_also_fails pins that limitation.
    """
    raw = '<tool_call>\n{"name": "word_count"}\n<tool_call>\n<tool_call>\n'
    v1_result = v1_parse_model_output(raw)
    v2_result = v2_parse_model_output(raw)
    assert v1_result["tool_calls"] == [], f"v1 should fail: {v1_result}"
    # v2 pass-2 recovers the call (no nested arguments to truncate)
    assert v2_result["tool_calls"][0]["name"] == "word_count", f"v2 should recover: {v2_result}"
    assert v2_result["tool_calls"][0]["arguments"] == {}, f"arguments default to {{}}: {v2_result}"
    print("PASS test_v2_pass2_recovers_flat_args")


def test_v2_pass2_empty_arguments_object_not_recovered():
    """Document that an EMPTY nested "arguments" object also defeats pass-2.

    Because the pass-2 capture stops at the first '}', the string
    {"name": "word_count", "arguments": {}} is captured as
    {"name": "word_count", "arguments": {} — one closing brace short — so
    json.loads fails inside the parser. Pass 1 still handles this call when
    the block is properly closed.
    """
    raw = '<tool_call>\n{"name": "word_count", "arguments": {}}\n<tool_call>\n'
    v1_result = v1_parse_model_output(raw)
    v2_result = v2_parse_model_output(raw)
    assert v1_result["tool_calls"] == [], f"v1 should fail: {v1_result}"
    assert v2_result["tool_calls"] == [], (
        f"v2 pass-2 cannot recover an empty nested arguments object: {v2_result}"
    )
    closed = '<tool_call>\n{"name": "word_count", "arguments": {}}\n</tool_call>'
    assert v2_parse_model_output(closed)["tool_calls"][0]["name"] == "word_count"
    print("PASS test_v2_pass2_empty_arguments_object_not_recovered  (documents pass-2 limitation)")


def test_v2_pass2_nested_args_also_fails():
    """Document that v2 pass-2 does NOT recover nested arguments from malformed tags.

    The \\{.*?\\} regex stops at the first '}', producing invalid JSON for
    arguments like {"query": "..."}.  This is a known limitation of the v2
    pass-2 fallback — documented here to prevent future confusion.
    """
    raw = '<tool_call>\n{"name": "web_search", "arguments": {"query": "Paris 2024"}}\n<tool_call>\n'
    v1_result = v1_parse_model_output(raw)
    v2_result = v2_parse_model_output(raw)
    assert v1_result["tool_calls"] == [], "v1 fails as expected"
    # v2 pass-2 also cannot recover nested args — json.loads fails internally
    assert v2_result["tool_calls"] == [], (
        f"v2 pass-2 cannot recover nested args (regex limitation): {v2_result}"
    )
    print("PASS test_v2_pass2_nested_args_also_fails  (documents known pass-2 limitation)")


def test_final_answer_no_tool_tags():
    """Both parsers return the text unchanged when no tool tags are present."""
    raw = "The capital of France is Paris."
    assert v1_parse_model_output(raw)["text"] == raw
    assert v2_parse_model_output(raw)["text"] == raw
    print("PASS test_final_answer_no_tool_tags")


# ── Source-parity test ───────────────────────────────────────────────────────
# The parsers above are transcriptions of the Colab server code, which cannot
# be imported directly (those files are Colab cell scripts with shell
# magics). This test pins the regex literals so the transcriptions cannot
# silently drift away from the implementation they document.

CLOSED_PATTERN = r'r"<tool_call>\s*(\{.*?\})\s*</tool_call>"'
OPEN_PATTERN = r'r"<tool_call>\s*(\{.*?\})"'


def _read_serving(name: str) -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serving", name)
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_test_parsers_match_serving_sources():
    """The transcribed parsers use the same regexes as the serving code."""
    single_pass = ["colab_server.py", "colab_server_base.py"]
    two_pass = ["colab_server_v2.py", "colab_server_e4.py"]
    for name in single_pass:
        src = _read_serving(name)
        assert CLOSED_PATTERN in src, f"{name}: single-pass pattern missing"
        assert OPEN_PATTERN not in src, f"{name}: unexpected pass-2 fallback"
    for name in two_pass:
        src = _read_serving(name)
        assert CLOSED_PATTERN in src, f"{name}: pass-1 pattern missing"
        assert OPEN_PATTERN in src, f"{name}: pass-2 fallback missing"
    # The parsers exercised above must use those same patterns.
    assert TOOL_CALL_CLOSED.pattern == r"<tool_call>\s*(\{.*?\})\s*</tool_call>"
    assert TOOL_CALL_OPEN.pattern == r"<tool_call>\s*(\{.*?\})"
    print("PASS test_test_parsers_match_serving_sources")


if __name__ == "__main__":
    test_v1_succeeds_well_formed()
    test_v2_pass1_succeeds_well_formed()
    test_v1_fails_malformed_no_closing_tag()
    test_v2_pass2_recovers_flat_args()
    test_v2_pass2_empty_arguments_object_not_recovered()
    test_v2_pass2_nested_args_also_fails()
    test_final_answer_no_tool_tags()
    test_test_parsers_match_serving_sources()
    print("\nAll parser-fix tests passed.")
