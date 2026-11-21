"""Model-family adapters around the frozen HFClient (AGENTRUN_DEEPENING_2026-11-11/scripts/hf_client.py).

The frozen client was written for Hermes-style tool calls (Qwen2.5 / Qwen3): tool calls are
<tool_call>{"name": ..., "arguments": ...}</tool_call>, and an assistant turn may carry several
calls. Llama 3.1 / 3.2 differ in three ways that matter for the agent loop:

1. the model emits {"name": ..., "parameters": {...}} (optionally after <|python_tag|>, ended by
   <|eom_id|>), which the frozen parser's bare-JSON fallback does not accept ("arguments" only);
2. the chat template raises "This model only supports single tool-calls at once!" for an
   assistant message with more than one call;
3. tool results are rendered as the `ipython` role by the template (handled by the template).

FamilyClient fixes 1 by re-parsing the raw text when the frozen parser found no call, and 2 by
splitting a multi-call assistant turn into consecutive (assistant call, tool result) pairs when
building the prompt. Nothing changes for Qwen: the adapter is a no-op unless family == "llama".
Every re-parse is logged in the response (`parse_path` = "family_llama_json").
"""
from __future__ import annotations

import json
import re

from . import paths  # noqa: F401  (sys.path for the frozen harness)
from hf_client import HFClient  # noqa: E402

_EOM = re.compile(r"<\|eom_id\|>|<\|python_tag\|>")
_OBJ = re.compile(r"\{")


def family_of(model_id: str) -> str:
    m = model_id.lower()
    if "llama" in m:
        return "llama"
    if "qwen" in m:
        return "qwen"
    return "other"


def split_multicall(messages: list[dict]) -> list[dict]:
    """Assistant turn with n>1 tool calls + its n tool results -> n (assistant, tool) pairs."""
    out, i = [], 0
    while i < len(messages):
        m = messages[i]
        tcs = m.get("tool_calls") or []
        if m.get("role") == "assistant" and len(tcs) > 1:
            results = []
            j = i + 1
            while j < len(messages) and messages[j].get("role") == "tool":
                results.append(messages[j])
                j += 1
            by_id = {r.get("tool_call_id"): r for r in results}
            for k, tc in enumerate(tcs):
                out.append({**m, "content": m.get("content") if k == 0 else "", "tool_calls": [tc]})
                r = by_id.get(tc.get("id")) or (results[k] if k < len(results) else None)
                if r is not None:
                    out.append(r)
            i = j
            continue
        out.append(m)
        i += 1
    return out


def parse_llama_calls(text: str) -> list[dict]:
    """JSON objects with "name" and "parameters"/"arguments" anywhere in the text."""
    text = _EOM.sub(" ", text or "")
    dec = json.JSONDecoder()
    calls, pos = [], 0
    while True:
        m = _OBJ.search(text, pos)
        if not m:
            break
        try:
            obj, end = dec.raw_decode(text, m.start())
        except json.JSONDecodeError:
            pos = m.start() + 1
            continue
        pos = end
        if isinstance(obj, dict) and isinstance(obj.get("name"), str):
            args = obj.get("parameters", obj.get("arguments", {}))
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            calls.append({"name": obj["name"], "arguments": args if isinstance(args, dict) else {}})
    return calls


class FamilyClient(HFClient):
    def __init__(self, model_id: str, **kw):
        super().__init__(model_id, **kw)
        self.family = family_of(model_id)
        self.n_family_reparse = 0

    def describe(self) -> dict:
        return {**super().describe(), "family": self.family, "family_adapter": "evarb.clients.FamilyClient/1"}

    def _for_template(self, messages: list[dict]) -> list[dict]:  # noqa: D401 (overrides a staticmethod)
        msgs = split_multicall(messages) if self.family == "llama" else messages
        return HFClient._for_template(msgs)

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        resp = super().chat(messages, tools)
        if self.family != "llama" or (resp["message"].get("tool_calls")):
            return resp
        raw = resp.get("raw_text") or ""
        calls = parse_llama_calls(raw) if tools else []
        if not calls:
            if resp["message"].get("content"):
                resp["message"]["content"] = _EOM.sub("", resp["message"]["content"]).strip()
            return resp
        self.n_family_reparse += 1
        tcs = [{"id": f"call_{self.n_requests}_{i}", "type": "function",
                "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}} for i, c in enumerate(calls)]
        resp.update({"message": {"role": "assistant", "content": "", "tool_calls": tcs},
                     "finish_reason": "tool_calls", "error": None, "parse_path": "family_llama_json"})
        return resp
