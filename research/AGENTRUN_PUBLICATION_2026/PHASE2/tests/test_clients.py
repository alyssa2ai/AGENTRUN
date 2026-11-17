"""Model-family adapter: parsing and multi-call splitting (no model needed)."""
import json

from evarb.clients import family_of, parse_llama_calls, split_multicall


def test_family():
    assert family_of("meta-llama/Llama-3.1-8B-Instruct") == "llama"
    assert family_of("Qwen/Qwen2.5-7B-Instruct") == "qwen"


def test_llama_parameters_json():
    c = parse_llama_calls('{"name": "memory_search", "parameters": {"query": "budget Zalor"}}')
    assert c == [{"name": "memory_search", "arguments": {"query": "budget Zalor"}}]


def test_llama_python_tag_and_eom():
    c = parse_llama_calls('<|python_tag|>{"name": "submit_answer", "parameters": {"status": "abstain"}}<|eom_id|>')
    assert c[0]["name"] == "submit_answer" and c[0]["arguments"]["status"] == "abstain"


def test_llama_two_calls_and_string_args():
    t = '{"name": "a", "parameters": {"x": 1}}; {"name": "b", "parameters": "{\\"y\\": 2}"}'
    assert [x["name"] for x in parse_llama_calls(t)] == ["a", "b"]
    assert parse_llama_calls(t)[1]["arguments"] == {"y": 2}


def test_plain_text_is_not_a_call():
    assert parse_llama_calls("The budget is 12 USD.") == []
    assert parse_llama_calls('{"status": "answer", "value": "12"}') == []


def test_split_multicall_preserves_order_and_pairs():
    msgs = [{"role": "user", "content": "q"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "c1", "function": {"name": "a", "arguments": "{}"}},
                {"id": "c2", "function": {"name": "b", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "c1", "name": "a", "content": "r1"},
            {"role": "tool", "tool_call_id": "c2", "name": "b", "content": "r2"},
            {"role": "assistant", "content": "done"}]
    out = split_multicall(msgs)
    roles = [(m["role"], (m.get("tool_calls") or [{}])[0].get("id"), m.get("content")) for m in out]
    assert roles == [("user", None, "q"), ("assistant", "c1", ""), ("tool", None, "r1"),
                     ("assistant", "c2", ""), ("tool", None, "r2"), ("assistant", None, "done")]
    assert json.dumps(out)  # serialisable
