"""memlab: controlled memory-reliability ablation for AGENTRUN (2026-11-11).

One file on purpose: fixtures, memory store, tools, agent loop, verifier and
scoring live together so the experiment can be audited in a single read.

Reuses the repository's own retrieval maths (memory.embed_text and
memory.cosine_similarity) and calculator (tools.calculator). Nothing in the
existing code base is modified.

Only task["prompt"] is ever sent to the model directly. Memory records and
registry facts reach the model only through tool results. task["expected"]
and task["gold_record_ids"] are used by the scorer alone.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from memory import cosine_similarity, embed_text  # noqa: E402  (existing AGENTRUN retrieval)
from tools import calculator as _calculator  # noqa: E402  (existing AGENTRUN tool)

MEMLAB_VERSION = "memlab-1.0"
TOP_K = 4
MIN_SIM = 0.2  # same threshold as memory.VectorMemory.search
MAX_STEPS = 6
TODAY = "2026-11-11"

# ----------------------------------------------------------------------------
# Configurations
# ----------------------------------------------------------------------------
CONFIGS = {
    "A": {"label": "A: stateless baseline", "memory": False, "verify": False, "provenance": False,
          "reliability": False},
    "B": {"label": "B: retrieval", "memory": True, "verify": False, "provenance": False, "reliability": False},
    "C": {"label": "C: verified retrieval", "memory": True, "verify": True, "provenance": False,
          "reliability": False},
    "D": {"label": "D: + provenance", "memory": True, "verify": True, "provenance": True, "reliability": False},
    "E": {"label": "E: + reliability gate", "memory": True, "verify": True, "provenance": True,
          "reliability": True},
}

# ----------------------------------------------------------------------------
# Fixture world (fictional, seeded)
# ----------------------------------------------------------------------------
ATTRS = {
    "budget_usd": {"q": "What is the approved budget, in USD, for {e}?",
                   "t": "The approved budget for {e} is {v} USD.", "kind": "num"},
    "team_size": {"q": "How many people are on the team for {e}?",
                  "t": "{e} has a team of {v} people.", "kind": "num"},
    "port": {"q": "Which port does the staging server for {e} listen on?",
             "t": "The staging server for {e} listens on port {v}.", "kind": "num"},
    "lead": {"q": "Who is the lead of {e}?", "t": "{e} is led by {v}.", "kind": "text"},
    "region": {"q": "In which cloud region is {e} hosted?",
               "t": "{e} is hosted in the {v} cloud region.", "kind": "text"},
    "deadline": {"q": "What is the delivery deadline for {e}? Give the date as YYYY-MM-DD.",
                 "t": "The delivery deadline for {e} is {v}.", "kind": "text"},
}
_ON = ["br", "c", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z", "th", "qu", "sk", "tr", "dr"]
_NU = ["a", "e", "i", "o", "u", "ae", "io", "ou"]
_CO = ["n", "r", "l", "x", "th", "nd", "rk", "sh", "m", "v", "st", "lt"]
_FIRST = ["Asha", "Bruno", "Chiara", "Dmitri", "Elif", "Farah", "Goran", "Hana", "Ines", "Jonah", "Kavya", "Lior",
          "Mira", "Nikhil", "Oona", "Pavel", "Rhea", "Soren", "Tara", "Umar", "Vera", "Wim", "Yara", "Zeno"]
_REGIONS = ["north-fjord-2", "east-mesa-1", "south-delta-3", "west-ridge-1", "mid-basin-4", "upper-vale-2",
            "low-marsh-1", "far-cape-5"]
_SOURCES = ["meeting_notes", "imported_doc", "user_statement"]
NAME_SEED = 20261111
N_DEV_NAMES = 150


def _name_pool() -> list[str]:
    rng = random.Random(NAME_SEED)
    seen, out = set(), []
    while len(out) < 1600:
        n = "".join(rng.choice(_ON) + rng.choice(_NU) for _ in range(2)) + rng.choice(_CO)
        if n not in seen and len(n) >= 6:
            seen.add(n)
            out.append(n.capitalize())
    return out


class _World:
    """Hands out unique fictional names and values for one split."""

    def __init__(self, split: str, seed: int):
        pool = _name_pool()
        self.names = pool[:N_DEV_NAMES] if split == "dev" else pool[N_DEV_NAMES:]
        self.rng = random.Random(seed)
        self.rng.shuffle(self.names)
        self._i = 0

    def name(self) -> str:
        self._i += 1
        return self.names[self._i - 1]

    def project(self) -> str:
        return "Project " + self.name()

    def value(self, attr: str, avoid=None):
        r = self.rng
        while True:
            if attr == "budget_usd":
                v = r.randrange(20, 900) * 1000 + r.randrange(1, 10) * 100
            elif attr == "team_size":
                v = r.randrange(3, 41)
            elif attr == "port":
                v = r.randrange(3000, 9999)
            elif attr == "lead":
                v = r.choice(_FIRST) + " " + self.name()
            elif attr == "region":
                v = r.choice(_REGIONS)
            else:
                v = (date(2027, 1, 1) + timedelta(days=r.randrange(0, 360))).isoformat()
            if v != avoid:
                return v

    def day(self, lo=0, hi=120) -> str:
        return (date(2026, 5, 1) + timedelta(days=self.rng.randrange(lo, hi))).isoformat()


def _rec(e, a, v, d, source, dated_text=False, role="distractor"):
    text = ATTRS[a]["t"].format(e=e, v=v)
    if dated_text:
        text = f"As of {d}: {text}"
    return {"entity": e, "attribute": a, "value": v, "recorded_on": d, "source": source, "text": text,
            "role": role}


def _distractors(w: _World, n: int, attrs=None) -> list[dict]:
    out = []
    for _ in range(n):
        a = w.rng.choice(attrs or list(ATTRS))
        out.append(_rec(w.project(), a, w.value(a), w.day(), w.rng.choice(_SOURCES)))
    return out


def _finish(w: _World, task: dict) -> dict:
    """Shuffle memory, assign record ids, derive gold ids, drop helper fields."""
    recs = task.pop("_records")
    w.rng.shuffle(recs)
    gold = []
    for i, r in enumerate(recs, 1):
        r["record_id"] = f"m-{i:02d}"
        if r.pop("role") == "gold":
            gold.append(r["record_id"])
    task["memory"] = recs
    task["gold_record_ids"] = gold
    task.setdefault("registry", {"facts": [], "plan": ["NOT_FOUND"]})
    return task


def _expected(kind, attr=None, value=None, **extra):
    out = {"kind": kind}
    if kind == "answer":
        num = isinstance(value, (int, float))
        out.update({"value": value, "value_kind": "num" if num else "text", "tol": 0.011 if num else None})
    out.update(extra)
    return out


def build_split(split: str, seed: int, per_scenario: int) -> list[dict]:
    """Build the task list for one split. per_scenario must be even (and a
    multiple of 4 for S6 to cover its four variants evenly)."""
    w = _World(split, seed)
    tasks = []
    attrs = list(ATTRS)

    def add(scenario, variant, i, **kw):
        t = {"task_id": f"{split}-{scenario}-{i:02d}", "split": split, "scenario": scenario, "variant": variant}
        t.update(kw)
        tasks.append(_finish(w, t))

    # S1 context loss: facts were stated in an earlier session; multi-step answer.
    for i in range(per_scenario):
        if i % 2 == 0:
            e = w.project()
            b, n = w.value("budget_usd"), w.value("team_size")
            d = w.day()
            recs = [_rec(e, "budget_usd", b, d, "user_statement", role="gold"),
                    _rec(e, "team_size", n, d, "user_statement", role="gold")]
            prompt = (f"In an earlier session I told you the approved budget and the team size for {e}. "
                      "What is the budget per team member in USD? Round to 2 decimals.")
            exp = _expected("answer", value=round(b / n, 2))
            variant = "per_member"
        else:
            e1, e2 = w.project(), w.project()
            b1, b2 = w.value("budget_usd"), w.value("budget_usd")
            recs = [_rec(e1, "budget_usd", b1, w.day(), "user_statement", role="gold"),
                    _rec(e2, "budget_usd", b2, w.day(), "user_statement", role="gold")]
            prompt = (f"In earlier sessions I told you the approved budgets for {e1} and {e2}. "
                      "What is their combined budget in USD?")
            exp = _expected("answer", value=b1 + b2)
            variant = "combined"
        add("S1_context_loss", variant, i, prompt=prompt, expected=exp,
            _records=recs + _distractors(w, 5, ["budget_usd", "team_size"]),
            needed_tools=["memory_search", "calculator"])

    # S2 relevant retrieval among hard distractors.
    for i in range(per_scenario):
        a = attrs[i % len(attrs)]
        e = w.project()
        v = w.value(a)
        recs = [_rec(e, a, v, w.day(), w.rng.choice(_SOURCES), role="gold")]
        others = [x for x in attrs if x != a]
        recs += [_rec(e, x, w.value(x), w.day(), w.rng.choice(_SOURCES)) for x in w.rng.sample(others, 3)]
        recs += [_rec(w.project(), a, w.value(a, avoid=v), w.day(), w.rng.choice(_SOURCES)) for _ in range(4)]
        recs += _distractors(w, 4)
        add("S2_retrieval", a, i, prompt=ATTRS[a]["q"].format(e=e), expected=_expected("answer", value=v),
            _records=recs, needed_tools=["memory_search"])

    # S3 conflicting memory: same fact, same day, two sources, two values.
    for i in range(per_scenario):
        a = attrs[(i + 1) % len(attrs)]
        e = w.project()
        v1 = w.value(a)
        v2 = w.value(a, avoid=v1)
        d = w.day()
        recs = [_rec(e, a, v1, d, "meeting_notes", role="gold"), _rec(e, a, v2, d, "imported_doc", role="gold")]
        add("S3_conflict", a, i, prompt=ATTRS[a]["q"].format(e=e),
            expected=_expected("conflict", conflict_values=[v1, v2]), _records=recs + _distractors(w, 5),
            needed_tools=["memory_search"])

    # S4 stale memory: an older and a newer value. Half carry the date in the
    # record text, half only in metadata.
    for i in range(per_scenario):
        a = attrs[(i + 2) % len(attrs)]
        e = w.project()
        old = w.value(a)
        new = w.value(a, avoid=old)
        d_old = w.day(0, 60)
        d_new = (date.fromisoformat(d_old) + timedelta(days=w.rng.randrange(30, 120))).isoformat()
        in_text = i % 2 == 0
        src = w.rng.choice(_SOURCES)
        recs = [_rec(e, a, old, d_old, src, dated_text=in_text, role="gold"),
                _rec(e, a, new, d_new, src, dated_text=in_text, role="gold")]
        add("S4_stale", "date_in_text" if in_text else "date_in_metadata_only", i,
            prompt=ATTRS[a]["q"].format(e=e), expected=_expected("answer", value=new, stale_value=old),
            _records=recs + _distractors(w, 5), needed_tools=["memory_search"])

    # S5 unsupported: the asked fact is nowhere; near-miss records are.
    for i in range(per_scenario):
        a = attrs[(i + 3) % len(attrs)]
        e = w.project()
        others = [x for x in attrs if x != a]
        recs = [_rec(e, x, w.value(x), w.day(), w.rng.choice(_SOURCES)) for x in w.rng.sample(others, 2)]
        recs += [_rec(w.project(), a, w.value(a), w.day(), w.rng.choice(_SOURCES)) for _ in range(3)]
        recs += _distractors(w, 3)
        q = ATTRS[a]["q"].format(e=e)
        if i % 2:
            q = "You should have this from an earlier session. " + q
        add("S5_unsupported", "false_premise" if i % 2 else "plain", i, prompt=q, expected=_expected("abstain"),
            _records=recs, needed_tools=["memory_search"])

    # S6 tool failure and recovery (registry tool).
    variants = ["transient_timeout", "malformed_then_ok", "permanent_no_memory", "permanent_memory_fallback"]
    plans = {"transient_timeout": ["TIMEOUT", "OK"], "malformed_then_ok": ["MALFORMED", "OK"],
             "permanent_no_memory": ["UNAVAILABLE"], "permanent_memory_fallback": ["UNAVAILABLE"]}
    for i in range(per_scenario):
        var = variants[i % 4]
        a = attrs[(i + 4) % len(attrs)]
        e = w.project()
        v = w.value(a)
        recs = _distractors(w, 6)
        needed = ["registry_lookup"]
        if var == "permanent_memory_fallback":
            recs.append(_rec(e, a, v, w.day(), "tool:registry_lookup", role="gold"))
            needed.append("memory_search")
        exp = _expected("abstain") if var == "permanent_no_memory" else _expected("answer", value=v)
        add("S6_tool_failure", var, i, prompt=ATTRS[a]["q"].format(e=e) + " This fact is tracked in the registry.",
            expected=exp, _records=recs, needed_tools=needed,
            registry={"facts": [{"entity": e, "attribute": a, "value": v}], "plan": plans[var]})
    return tasks


# ----------------------------------------------------------------------------
# Memory store (persistent JSON, existing AGENTRUN embedding) + reliability gate
# ----------------------------------------------------------------------------
class MemoryStore:
    def __init__(self, records: list[dict], path: Path | None = None):
        entries = [{**r, "embedding": embed_text(r["text"])} for r in records]
        if path is not None:  # write, then reload from disk: the store the agent uses is the persisted one
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(entries), encoding="utf-8")
            entries = json.loads(path.read_text(encoding="utf-8"))
        self.entries = entries

    def search(self, query: str, top_k: int = TOP_K, min_similarity: float = MIN_SIM) -> list[dict]:
        q = embed_text(query)
        scored = sorted(((-cosine_similarity(q, e["embedding"]), e["record_id"], e) for e in self.entries),
                        key=lambda x: x[:2])
        return [e for s, _, e in scored[:top_k] if -s >= min_similarity]

    def same_key(self, rec: dict) -> list[dict]:
        return [e for e in self.entries if e["entity"] == rec["entity"] and e["attribute"] == rec["attribute"]]


def reliability_status(rec: dict, group: list[dict]) -> dict:
    """Deterministic status of one record against every stored record with
    the same (entity, attribute) key."""
    if len({str(g["value"]) for g in group}) <= 1:
        return {"status": "unchallenged"}
    latest = max(g["recorded_on"] for g in group)
    latest_recs = [g for g in group if g["recorded_on"] == latest]
    if rec["recorded_on"] < latest:
        if any(str(g["value"]) != str(rec["value"]) for g in latest_recs):
            return {"status": "superseded", "superseded_by": sorted(g["record_id"] for g in latest_recs)}
        return {"status": "current"}
    rivals = sorted(g["record_id"] for g in latest_recs if str(g["value"]) != str(rec["value"]))
    if rivals:
        return {"status": "conflicting", "conflicts_with": rivals}
    return {"status": "current"}


def memory_tool_result(store: MemoryStore, query: str, cfg: dict) -> tuple[str, list[str]]:
    """Return (observation shown to the model, record ids retrieved by similarity)."""
    hits = store.search(query)
    hit_ids = [h["record_id"] for h in hits]
    if not cfg["provenance"]:
        return json.dumps({"results": [{"text": h["text"]} for h in hits]}), hit_ids
    shown = list(hits)
    added = set()
    if cfg["reliability"]:
        for h in hits:
            for g in store.same_key(h):
                if g["record_id"] not in {s["record_id"] for s in shown}:
                    shown.append(g)
                    added.add(g["record_id"])
    results = []
    for h in shown:
        item = {"record_id": h["record_id"], "text": h["text"], "recorded_on": h["recorded_on"],
                "source": h["source"]}
        if cfg["reliability"]:
            item["reliability"] = reliability_status(h, store.same_key(h))
            if h["record_id"] in added:
                item["added_by_reliability_check"] = True
        results.append(item)
    return json.dumps({"results": results}), hit_ids


# ----------------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------------
def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


class Registry:
    def __init__(self, spec: dict):
        self.facts, self.plan, self.n = spec["facts"], spec["plan"], 0

    def call(self, entity, attribute) -> tuple[str, str]:
        fact = next((f for f in self.facts if _norm(f["entity"]) in _norm(entity)
                     and f["attribute"] == attribute), None)
        if fact is None:
            return "NOT_FOUND", json.dumps({"found": False, "detail": "no registry entry for this entity/attribute"})
        step = self.plan[min(self.n, len(self.plan) - 1)]
        self.n += 1
        if step == "TIMEOUT":
            return step, "ERROR 504: registry upstream timeout"
        if step == "UNAVAILABLE":
            return step, "ERROR 503: registry service unavailable"
        if step == "MALFORMED":
            return step, '{"entity": "%s", "attribute": "%s", "val' % (fact["entity"], attribute)
        return "OK", json.dumps({"found": True, "entity": fact["entity"], "attribute": attribute,
                                 "value": fact["value"], "source": "registry", "retrieved_on": TODAY})


def _fn(name, desc, props, required):
    return {"type": "function", "function": {"name": name, "description": desc,
                                             "parameters": {"type": "object", "properties": props,
                                                            "required": required}}}


CALC_TOOL = _fn("calculator", "Evaluate a basic arithmetic expression, e.g. '12 * (3 + 4)'.",
                {"expression": {"type": "string"}}, ["expression"])
REG_TOOL = _fn("registry_lookup", "Look up a project fact in the live project registry (system of record).",
               {"entity": {"type": "string", "description": "Project name, e.g. 'Project Example'"},
                "attribute": {"type": "string", "enum": list(ATTRS)}}, ["entity", "attribute"])
SUBMIT_TOOL = _fn("submit_answer", "Submit the final answer. Call exactly once, when done.",
                  {"status": {"type": "string", "enum": ["answer", "abstain", "conflict"]},
                   "value": {"type": "string", "description": "The answer (numbers as digits); empty unless "
                             "status is answer"},
                   "evidence": {"type": "array", "items": {"type": "string"},
                                "description": "Record ids or tool names relied on"},
                   "note": {"type": "string", "description": "One short sentence"}}, ["status"])
MEM_TOOL = _fn("memory_search", "Search the persistent long-term memory of facts recorded in earlier sessions. "
               "Returns the most similar stored records.", {"query": {"type": "string"}}, ["query"])

SYSTEM_PROMPT = """You answer questions about the user's projects. You know no project facts yourself: every fact must come from a tool result in this conversation.

Rules:
1. Never guess and never use outside knowledge.
2. If a tool call fails with an error or returns an unusable (for example truncated) result, retry the same call up to two more times before giving up on that tool. A "not found" or empty result is a valid result, not a failure: do not repeat that call.
3. If, after using the tools, the evidence does not establish the requested fact for the requested project, reply with status "abstain".
4. If the evidence gives different values for the requested fact: when you can establish which value is the most recent, answer with the most recent one; otherwise reply with status "conflict".
5. Use the calculator for any arithmetic.

When you are done, call submit_answer exactly once. Do not write the answer as plain text.
- status "answer": value is the answer.
- status "abstain": the evidence does not establish the answer (value empty).
- status "conflict": unresolved contradictory values (value empty)."""

VERIFIER_PROMPT = """You are a verification module. Decide whether the DRAFT ANSWER to the QUESTION is established by the EVIDENCE. The EVIDENCE is everything the agent's tools returned; nothing else may be assumed.

Verdicts:
- SUPPORTED: the evidence states the requested fact for the requested project with exactly this value (or arithmetic on stated values gives it), and any evidence with a different value is clearly older.
- UNSUPPORTED: the evidence does not state the requested fact for the requested project (for example it is about another project or another attribute), or the draft value does not match the evidence, or the draft relies on a value that the evidence shows to be outdated.
- CONFLICT: the evidence contains different values for the requested fact and it cannot be established which is the most recent.

Reply with one JSON object and nothing else: {"verdict": "SUPPORTED" | "UNSUPPORTED" | "CONFLICT", "reason": "<one short sentence>"}"""


MALFORMED_NOTICE = ("[harness notice] Your last output was rejected because it was not a valid tool call. "
                    "Continue by calling one of the available tools with valid JSON arguments.")


def prompts_sha256() -> str:
    blob = json.dumps({"system": SYSTEM_PROMPT, "malformed_notice": MALFORMED_NOTICE, "verifier": VERIFIER_PROMPT,
                       "tools": [CALC_TOOL, REG_TOOL, MEM_TOOL, SUBMIT_TOOL], "configs": CONFIGS, "top_k": TOP_K,
                       "min_sim": MIN_SIM, "max_steps": MAX_STEPS}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


# ----------------------------------------------------------------------------
# Model client (OpenAI-compatible chat completions; Groq)
# ----------------------------------------------------------------------------
class ChatClient:
    def __init__(self, model: str, extra: dict | None = None, base_url="https://api.groq.com/openai/v1",
                 key_env="GROQ_API_KEY", seed=20261111, min_tokens_left=2600):
        import requests
        self.s = requests.Session()
        self.model, self.extra, self.url, self.seed = model, extra or {}, base_url + "/chat/completions", seed
        self.key = os.environ[key_env]
        self.min_tokens_left = min_tokens_left
        self.n_requests = 0

    def describe(self) -> dict:
        return {"model": self.model, "endpoint": self.url, "temperature": 0, "seed": self.seed,
                "max_tokens": 1200, "extra": self.extra}

    @staticmethod
    def _secs(v: str | None) -> float:
        if not v:
            return 0.0
        m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?(?:([\d.]+)ms)?", v.strip())
        if not m:
            try:
                return float(v)
            except ValueError:
                return 5.0
        h, mi, s, ms = (float(x) if x else 0.0 for x in m.groups())
        return h * 3600 + mi * 60 + s + ms / 1000

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Return {"message", "usage", "latency_s", "wait_s", "error"}; wait_s is
        rate-limit sleeping and is excluded from latency_s."""
        body = {"model": self.model, "messages": messages, "temperature": 0, "seed": self.seed,
                "max_tokens": 1200, **self.extra}
        if tools:
            body["tools"] = tools
        wait = 0.0
        for attempt in range(10):
            t0 = time.monotonic()
            try:
                r = self.s.post(self.url, json=body, headers={"Authorization": "Bearer " + self.key}, timeout=120)
            except Exception as e:  # network error
                time.sleep(5)
                wait += 5
                err = f"network:{type(e).__name__}"
                continue
            lat = time.monotonic() - t0
            self.n_requests += 1
            if r.status_code == 200:
                j = r.json()
                left = r.headers.get("x-ratelimit-remaining-tokens")
                if left is not None and float(left) < self.min_tokens_left:
                    nap = min(self._secs(r.headers.get("x-ratelimit-reset-tokens")) + 0.5, 65)
                    time.sleep(nap)
                    wait += nap
                return {"message": j["choices"][0]["message"], "usage": j.get("usage", {}),
                        "finish_reason": j["choices"][0].get("finish_reason"), "latency_s": round(lat, 4),
                        "wait_s": round(wait, 2), "error": None}
            err = f"http{r.status_code}:{r.text[:300]}"
            if r.status_code == 429 or r.status_code >= 500:
                if "per day" in r.text or "(RPD)" in r.text or "(TPD)" in r.text:
                    raise RuntimeError("daily quota exhausted: " + r.text[:300])
                nap = min(self._secs(r.headers.get("retry-after")) + 1.0, 90) or 10
                time.sleep(nap)
                wait += nap
                continue
            # 400: typically a malformed tool call generated by the model. A model failure, not a harness one.
            return {"message": {"role": "assistant", "content": ""}, "usage": {}, "finish_reason": "api_error",
                    "latency_s": round(lat, 4), "wait_s": round(wait, 2), "error": err}
        raise RuntimeError("request failed after retries: " + err)


# ----------------------------------------------------------------------------
# Agent loop
# ----------------------------------------------------------------------------
# raw_text / parse_path are present only for the local-GPU backend (hf_client.py)
API_KEYS = ("usage", "latency_s", "wait_s", "error", "finish_reason", "raw_text", "parse_path")


def parse_final(text: str | None) -> dict | None:
    """Last JSON object in the text that carries a "status" (or "verdict") key."""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    dec = json.JSONDecoder()
    found = None
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = dec.raw_decode(text[m.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and ("status" in obj or "verdict" in obj):
            found = obj
    return found


def run_task(client, task: dict, config: str, store_dir: Path | None = None) -> dict:
    cfg = CONFIGS[config]
    store = None
    t_ret = 0.0
    if cfg["memory"]:
        path = store_dir / f"{task['task_id']}__{config}.json" if store_dir else None
        store = MemoryStore(task["memory"], path)
    registry = Registry(task["registry"])
    tools = [CALC_TOOL, REG_TOOL] + ([MEM_TOOL] if cfg["memory"] else []) + [SUBMIT_TOOL]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": task["prompt"]}]
    calls, api, evidence = [], [], []
    draft_text, hit_max = None, False
    t0 = time.monotonic()
    for step in range(1, MAX_STEPS + 1):
        resp = client.chat(messages, tools)
        api.append({"role": "agent", "step": step, **{k: resp.get(k) for k in API_KEYS}})
        msg = resp["message"]
        if resp["error"]:
            # The serving layer rejected the generation (malformed tool call). Same policy in every
            # configuration: tell the model and let it try again; this uses up one step.
            messages.append({"role": "user", "content": MALFORMED_NOTICE})
            continue
        tcs = msg.get("tool_calls") or []
        if not tcs and not (msg.get("content") or "").strip() and step < MAX_STEPS:
            messages.append({"role": "user", "content": MALFORMED_NOTICE})  # empty generation: same policy
            continue
        if not tcs:
            draft_text = msg.get("content") or ""
            messages.append({"role": "assistant", "content": draft_text})
            break
        sub = next((tc for tc in tcs if tc["function"]["name"] == "submit_answer"), None)
        if sub is not None:  # final answer given through the submit tool
            draft_text = sub["function"]["arguments"] or ""
            try:
                d = json.loads(draft_text)
                if isinstance(d, dict) and d.get("status") != "answer":
                    d["value"] = None
                draft_text = json.dumps(d)
            except Exception:
                pass
            messages.append({"role": "assistant", "content": draft_text})
            break
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tcs})
        for tc in tcs:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
                assert isinstance(args, dict)
            except Exception:
                args = None
            retrieved = None
            if args is None:
                status, obs = "VALIDATION_ERROR", f"ERROR: arguments for '{name}' are not a JSON object"
            elif name == "calculator" and isinstance(args.get("expression"), str):
                try:
                    obs = _calculator(args["expression"])
                    status = "OK" if obs != "Invalid characters in expression." else "TOOL_ERROR"
                except Exception as e:
                    status, obs = "TOOL_ERROR", f"ERROR running tool 'calculator': {e}"
            elif name == "registry_lookup" and isinstance(args.get("entity"), str) and "attribute" in args:
                status, obs = registry.call(args["entity"], args["attribute"])
            elif name == "memory_search" and store is not None and isinstance(args.get("query"), str):
                r0 = time.monotonic()
                obs, retrieved = memory_tool_result(store, args["query"], cfg)
                t_ret += time.monotonic() - r0
                status = "OK"
            else:
                status, obs = "VALIDATION_ERROR", f"ERROR: unknown tool or invalid arguments for '{name}'"
            calls.append({"step": step, "name": name, "arguments": args, "status": status, "observation": obs,
                          "retrieved_ids": retrieved})
            evidence.append({"tool": name, "arguments": args, "result": obs})
            messages.append({"role": "tool", "tool_call_id": tc.get("id"), "name": name, "content": obs})
    else:
        hit_max = True
    draft = parse_final(draft_text)
    final, verdict = draft, None
    if cfg["verify"] and draft and draft.get("status") == "answer":
        vmsg = [{"role": "system", "content": VERIFIER_PROMPT},
                {"role": "user", "content": "QUESTION:\n" + task["prompt"] + "\n\nEVIDENCE:\n"
                 + json.dumps(evidence, ensure_ascii=False) + "\n\nDRAFT ANSWER:\n"
                 + json.dumps(draft, ensure_ascii=False)}]
        vresp = client.chat(vmsg)
        api.append({"role": "verifier", "step": 0, **{k: vresp.get(k) for k in API_KEYS}})
        vraw = vresp["message"].get("content") or ""
        vparsed = parse_final(vraw) or {}
        v = str(vparsed.get("verdict", "")).upper()
        verdict = {"raw": vraw, "verdict": v if v in ("SUPPORTED", "UNSUPPORTED", "CONFLICT") else "UNPARSED",
                   "reason": vparsed.get("reason")}
        if v == "UNSUPPORTED":
            final = {"status": "abstain", "value": None, "evidence": [], "note": "verifier: unsupported"}
        elif v == "CONFLICT":
            final = {"status": "conflict", "value": None, "evidence": [], "note": "verifier: conflict"}
    wait = sum(a["wait_s"] for a in api)
    return {"record_type": "run", "task_id": task["task_id"], "config": config, "messages": messages,
            "tool_calls": calls, "api_calls": api, "draft_text": draft_text, "draft": draft, "verdict": verdict,
            "final": final, "hit_max_steps": hit_max,
            "timing": {"total_s": round(time.monotonic() - t0 - wait, 4), "rate_limit_wait_s": round(wait, 2),
                       "model_s": round(sum(a["latency_s"] for a in api), 4), "retrieval_s": round(t_ret, 6)}}


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------
def _num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"-?\d+(?:\.\d+)?", str(x).replace(",", ""))
    return float(m.group()) if m else None


def value_matches(value, kind: str, got, tol=None) -> bool:
    if got is None:
        return False
    if kind == "num":
        g = _num(got)
        return g is not None and abs(g - float(value)) <= (tol or 0.011)
    return _norm(value) != "" and _norm(value) in _norm(got)


HARMFUL = {"wrong_value", "stale_value", "unsupported_claim", "arbitrary_pick"}
OUTCOMES = ["correct", "over_abstain", "false_conflict", "wrong_value", "stale_value", "unsupported_claim",
            "arbitrary_pick", "format_error", "max_steps"]


def classify(expected: dict, ans: dict | None, hit_max=False) -> str:
    """Outcome of one answer object against the task's expected behaviour."""
    if hit_max:
        return "max_steps"
    status = (ans or {}).get("status")
    if status not in ("answer", "abstain", "conflict"):
        return "format_error"
    kind = expected["kind"]
    if kind == "answer":
        if status == "abstain":
            return "over_abstain"
        if status == "conflict":
            return "false_conflict"
        if value_matches(expected["value"], expected["value_kind"], ans.get("value"), expected.get("tol")):
            return "correct"
        if "stale_value" in expected and value_matches(expected["stale_value"], expected["value_kind"],
                                                       ans.get("value"), expected.get("tol")):
            return "stale_value"
        return "wrong_value"
    if kind == "abstain":
        return {"abstain": "correct", "answer": "unsupported_claim", "conflict": "false_conflict"}[status]
    return {"conflict": "correct", "answer": "arbitrary_pick", "abstain": "over_abstain"}[status]


def value_in_evidence(run: dict) -> bool | None:
    """For a final status=answer: does the value literally occur in a tool
    result the agent saw (memory, registry or calculator output)?"""
    f = run.get("final") or {}
    if f.get("status") != "answer" or f.get("value") is None:
        return None
    v = f["value"]
    n = _num(v) if isinstance(v, (int, float)) or re.fullmatch(r"[\s$]*-?[\d,]+(?:\.\d+)?\s*(?:USD)?\s*", str(v)) \
        else None
    for c in run["tool_calls"]:
        obs = c["observation"]
        if n is not None:
            if any(abs(float(x) - n) <= 0.011 for x in re.findall(r"-?\d+(?:\.\d+)?", obs.replace(",", ""))):
                return True
        elif _norm(v) and _norm(v) in _norm(obs):
            return True
    return False


def score_run(task: dict, run: dict) -> dict:
    exp = task["expected"]
    outcome = classify(exp, run.get("final"), run.get("hit_max_steps"))
    draft_outcome = classify(exp, run.get("draft"), run.get("hit_max_steps"))
    gold = set(task["gold_record_ids"])
    retrieved = [i for c in run["tool_calls"] if c["retrieved_ids"] is not None for i in c["retrieved_ids"]]
    uniq = set(retrieved)
    mem_calls = [c for c in run["tool_calls"] if c["name"] == "memory_search" and c["retrieved_ids"] is not None]
    first = set(mem_calls[0]["retrieved_ids"]) if mem_calls else set()
    names = {c["name"] for c in run["tool_calls"]}
    reg = [c for c in run["tool_calls"] if c["name"] == "registry_lookup"]
    injected = [c for c in reg if c["status"] in ("TIMEOUT", "UNAVAILABLE", "MALFORMED")]
    return {
        "task_id": task["task_id"], "scenario": task["scenario"], "variant": task["variant"],
        "config": run["config"], "expected_kind": exp["kind"], "outcome": outcome,
        "success": outcome == "correct", "harmful": outcome in HARMFUL, "draft_outcome": draft_outcome,
        "final_status": (run.get("final") or {}).get("status"),
        "value_in_evidence": value_in_evidence(run),
        "verdict": (run.get("verdict") or {}).get("verdict"),
        "n_gold": len(gold), "n_memory_calls": len(mem_calls),
        "recall_union": (len(gold & uniq) / len(gold)) if gold and mem_calls else None,
        "precision_union": (len(gold & uniq) / len(uniq)) if gold and uniq else (0.0 if gold and mem_calls else None),
        "recall_at_k_first": (len(gold & first) / len(gold)) if gold and mem_calls else None,
        "precision_at_k_first": (len(gold & first) / TOP_K) if gold and mem_calls else None,
        "needed_tools_called": all(t in names for t in task["needed_tools"]),
        "n_tool_calls": len(run["tool_calls"]),
        "n_tool_ok": sum(c["status"] in ("OK", "NOT_FOUND") for c in run["tool_calls"]),
        "n_injected_failures": len(injected),
        "n_agent_tool_errors": sum(c["status"] in ("VALIDATION_ERROR", "TOOL_ERROR") for c in run["tool_calls"]),
        "retried_after_failure": bool(injected) and len(reg) > 1,
        "n_api_calls": len(run["api_calls"]),
        "prompt_tokens": sum(a["usage"].get("prompt_tokens", 0) for a in run["api_calls"]),
        "completion_tokens": sum(a["usage"].get("completion_tokens", 0) for a in run["api_calls"]),
        "total_s": run["timing"]["total_s"], "model_s": run["timing"]["model_s"],
        "retrieval_s": run["timing"]["retrieval_s"],
    }
