#!/usr/bin/env python3
"""
test_parser.py - Test that v2 parser recovers from malformed output that v1 parser fails on

Tests the regex patterns from colab_server.py (v1, single-pass) and
colab_server_v2.py (v2, two-pass) to verify the parser fix handles
malformed tool-call output.
"""

import re
import json


def v1_parse(raw_text):
    """Single-pass regex from colab_server.py (line 55)"""
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


def v2_parse(raw_text):
    """Two-pass parser from colab_server_v2.py"""
    TOOL_CALL_CLOSED = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
    TOOL_CALL_OPEN = re.compile(r"<tool_call>\s*(\{.*?\})", re.DOTALL)

    # Pass 1: strict closed blocks
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

    # Pass 2: fallback — first JSON after any <tool_call> tag
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


# ── Test cases ────────────────────────────────────────────────────────────────

def test_well_formed_single_call():
    """Both parsers handle a well-formed single tool call."""
    raw = '<tool_call>\n{"name": "calculator", "arguments": {"expression": "2+2"}}\n</tool_call>'
    v1 = v1_parse(raw)
    v2 = v2_parse(raw)
    assert v1["tool_calls"][0]["name"] == "calculator", f"v1 failed: {v1}"
    assert v2["tool_calls"][0]["name"] == "calculator", f"v2 failed: {v2}"
    print("PASS test_well_formed_single_call")


def test_malformed_no_closing_tag():
    """v1 fails malformed output (no </tool_call>); v2 recovers via pass-2.

    Pass-2 limitation: only works when arguments are flat (empty dict or no
    nested objects) because the regex stops at the first '}'. See
    test_parser_fixed.py for the full documentation of this limitation.
    """
    # Model emits <tool_call> without closing tag — flat args case
    raw = '<tool_call>\n{"name": "word_count", "arguments": {}}\n<tool_call>\n<tool_call>\n'
    v1 = v1_parse(raw)
    v2 = v2_parse(raw)
    assert v1["tool_calls"] == [], f"v1 should fail: {v1}"
    assert v2["tool_calls"][0]["name"] == "word_count", f"v2 should recover: {v2}"
    print("PASS test_malformed_no_closing_tag")


def test_plain_text_no_tool_call():
    """Both parsers return text when no tool-call tags present."""
    raw = "The capital of France is Paris."
    v1 = v1_parse(raw)
    v2 = v2_parse(raw)
    assert v1["tool_calls"] == [] and v1["text"] == raw, f"v1 failed: {v1}"
    assert v2["tool_calls"] == [] and v2["text"] == raw, f"v2 failed: {v2}"
    print("PASS test_plain_text_no_tool_call")


def test_malformed_json_inside_tag():
    """Both parsers skip malformed JSON and fall back to text."""
    raw = "<tool_call>\nnot-json-at-all\n</tool_call>"
    v1 = v1_parse(raw)
    v2 = v2_parse(raw)
    # v1: malformed JSON -> no tool_calls, but text is raw_text.strip() (original text)
    assert v1["tool_calls"] == [], f"v1 failed: {v1}"
    # v2 pass 1 finds the closed block but JSON parse fails; pass 2 also fails -> text
    assert v2["tool_calls"] == [], f"v2 failed: {v2}"
    print("PASS test_malformed_json_inside_tag")


def test_word_count_tool_call():
    """Both parsers extract word_count call."""
    raw = '<tool_call>\n{"name": "word_count", "arguments": {"text": "hello world"}}\n</tool_call>'
    v1 = v1_parse(raw)
    v2 = v2_parse(raw)
    assert v1["tool_calls"][0]["arguments"]["text"] == "hello world", f"v1 failed: {v1}"
    assert v2["tool_calls"][0]["arguments"]["text"] == "hello world", f"v2 failed: {v2}"
    print("PASS test_word_count_tool_call")


def test_empty_string():
    """Both parsers handle empty input safely."""
    v1 = v1_parse("")
    v2 = v2_parse("")
    assert v1["tool_calls"] == [] and v1["text"] == "", f"v1 failed: {v1}"
    assert v2["tool_calls"] == [] and v2["text"] == "", f"v2 failed: {v2}"
    print("PASS test_empty_string")


if __name__ == "__main__":
    test_well_formed_single_call()
    test_malformed_no_closing_tag()
    test_plain_text_no_tool_call()
    test_malformed_json_inside_tag()
    test_word_count_tool_call()
    test_empty_string()
    print("\nAll tests passed.")
