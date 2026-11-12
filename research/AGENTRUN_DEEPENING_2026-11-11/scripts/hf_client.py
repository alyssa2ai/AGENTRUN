"""Local-GPU model client for the memlab ablation (SIT HPC, NVIDIA L40).

Same interface as memlab.ChatClient.chat(): takes OpenAI-style messages and
tool schemas, returns {"message", "usage", "finish_reason", "latency_s",
"wait_s", "error", "raw_text"}. The model is a Hugging Face causal LM with a
Hermes-style tool template (Qwen2.5 / Qwen3). Tool calls are parsed from the
raw generation with AGENTRUN's own parser (agentrun_v2.parser), so the raw
text, the parser version and the parse are all logged.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import memlab  # noqa: F401  (puts the repository root on sys.path)
from agentrun_v2.parser import PARSER_VERSION, parse_model_output

_END = re.compile(r"<\|im_end\|>|<\|endoftext\|>|<\|eot_id\|>")
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


class HFClient:
    def __init__(self, model_id: str, adapter: str | None = None, temperature: float = 0.0,
                 seed: int = 20261111, max_new_tokens: int = 700):
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.model_id, self.adapter, self.temperature, self.seed = model_id, adapter, temperature, seed
        self.max_new_tokens = max_new_tokens
        # Load straight from the local Hugging Face cache snapshot when there is one (no network needed).
        path = model_id
        if not Path(model_id).is_dir():
            snaps = sorted((Path.home() / ".cache/huggingface/hub" / ("models--" + model_id.replace("/", "--"))
                            / "snapshots").glob("*"))
            if snaps:
                path = str(snaps[-1])
        self.model_path = path
        self.tok = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16, device_map={"": 0})
        self.adapter_sha = None
        if adapter:
            import peft
            from peft import PeftModel
            self.adapter_sha = hashlib.sha256((Path(adapter) / "adapter_model.safetensors").read_bytes()).hexdigest()
            self.model = PeftModel.from_pretrained(self.model, adapter).merge_and_unload()
            self._peft = peft.__version__
        self.model.eval()
        torch.manual_seed(seed)
        self.n_requests = 0
        self._versions = {"torch": torch.__version__, "transformers": transformers.__version__,
                          "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
                          "gpu_mem_gib": round(torch.cuda.get_device_properties(0).total_memory / 2 ** 30, 1)}

    def describe(self) -> dict:
        return {"backend": "hf-local", "model": self.model_id, "model_path": self.model_path, "adapter": self.adapter,
                "adapter_sha256": self.adapter_sha, "temperature": self.temperature, "seed": self.seed,
                "max_new_tokens": self.max_new_tokens, "dtype": "bfloat16", "parser_version": PARSER_VERSION,
                "decoding": "greedy" if self.temperature == 0 else "sampling top_p=0.9",
                "thinking": "disabled via chat template where supported", **self._versions}

    @staticmethod
    def _for_template(messages: list[dict]) -> list[dict]:
        out = []
        for m in messages:
            m = dict(m)
            m.pop("tool_call_id", None)
            if m.get("tool_calls"):
                tcs = []
                for tc in m["tool_calls"]:
                    args = tc["function"]["arguments"]
                    try:
                        args = json.loads(args) if isinstance(args, str) else args
                    except json.JSONDecodeError:
                        args = {}
                    tcs.append({"type": "function", "function": {"name": tc["function"]["name"], "arguments": args}})
                m["tool_calls"] = tcs
            out.append(m)
        return out

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        torch = self.torch
        kw = {"add_generation_prompt": True, "tokenize": False, "enable_thinking": False}
        if tools:
            kw["tools"] = tools
        prompt = self.tok.apply_chat_template(self._for_template(messages), **kw)
        enc = self.tok(prompt, return_tensors="pt").to(self.model.device)
        gen = {"max_new_tokens": self.max_new_tokens, "pad_token_id": self.tok.eos_token_id}
        if self.temperature > 0:
            gen.update({"do_sample": True, "temperature": self.temperature, "top_p": 0.9})
        else:
            gen.update({"do_sample": False, "temperature": None, "top_p": None, "top_k": None})
        t0 = time.monotonic()
        with torch.no_grad():
            out = self.model.generate(**enc, **gen)
        lat = time.monotonic() - t0
        self.n_requests += 1
        new = out[0, enc["input_ids"].shape[1]:]
        raw = _END.split(self.tok.decode(new, skip_special_tokens=False))[0].strip()
        text = _THINK.sub("", raw).strip()
        parsed = parse_model_output(text)
        usage = {"prompt_tokens": int(enc["input_ids"].shape[1]), "completion_tokens": int(new.shape[0]),
                 "total_tokens": int(enc["input_ids"].shape[1] + new.shape[0])}
        base = {"usage": usage, "latency_s": round(lat, 4), "wait_s": 0.0, "raw_text": raw,
                "parse_path": parsed.get("parse_path")}
        if parsed["tool_calls"]:
            tcs = [{"id": f"call_{self.n_requests}_{i}", "type": "function",
                    "function": {"name": str(tc.get("name")), "arguments": json.dumps(tc.get("arguments", {}))}}
                   for i, tc in enumerate(parsed["tool_calls"])]
            return {"message": {"role": "assistant", "content": "", "tool_calls": tcs},
                    "finish_reason": "tool_calls", "error": None, **base}
        if "<tool_call>" in text:  # the model tried to call a tool but the call did not parse
            return {"message": {"role": "assistant", "content": ""}, "finish_reason": "api_error",
                    "error": "malformed_tool_call:" + text[:300], **base}
        return {"message": {"role": "assistant", "content": text}, "finish_reason": "stop", "error": None, **base}
