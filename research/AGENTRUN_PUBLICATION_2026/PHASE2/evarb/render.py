"""Labels shown to the agent in memory_search results.

Mirrors memlab.memory_tool_result (same retrieval, same top-k, same "added_by_reliability_check"
records for every retrieved key) and replaces only the `reliability` object:

  {"status": current | superseded | historical | contradictory | unresolved | unchallenged,
   "evidence": <basis in words>, "certainty": established | likely | not established,
   "superseded_by"/"conflicts_with": [...], "valid_from": ..., "note": ...}

Wording follows the Phase 1 compliance asymmetry (FAILURE_TAXONOMY M13): small models follow a
cautionary label almost always. A group whose order the evidence cannot establish is therefore
labelled "unresolved ... read the record texts", not "conflicting"; "contradictory" is reserved
for the case where the evidence says the values really disagree.
"""
from __future__ import annotations

import json

from . import paths  # noqa: F401
from .arbiter import MODERATE, STRONG, Resolution

BASIS_WORDS = {
    "record_time": "ordered by recorded_on",
    "valid_time": "ordered by the validity dates stated in the record texts",
    "explicit_correction": "a record states it corrects the other",
    "explicit_supersession": "a record states it replaces the other",
    "same_day_correction": "same date; a record states it corrects the other",
    "source_authority": "same date; only the source type differs (system of record)",
    "genuine_contradiction": "same date, different values, no evidence which is current",
    "negated_correction": "a record says it does not replace the other, or that a change is not confirmed",
    "quoted_or_hypothetical": "a change is only reported or hypothetical",
    "insufficient_evidence": "the order is not established by metadata or text; read the record texts",
}
CERTAINTY = {STRONG: "established", MODERATE: "likely", "none": "not established"}


def label(rid: str, res: Resolution, intent: str = "current") -> dict:
    st = dict(res.statuses[rid])
    if st["status"] == "unchallenged":
        return {"status": "unchallenged"}
    out = {"status": st["status"]}
    if intent == "historical" and st["status"] == "superseded":
        out["status"] = "historical"
        out["note"] = "superseded later; may answer a question about an earlier time"
    if st.get("basis"):
        out["evidence"] = BASIS_WORDS.get(st["basis"], st["basis"])
    out["certainty"] = CERTAINTY.get(st.get("strength", "none"), "not established")
    for k in ("superseded_by", "conflicts_with", "valid_from"):
        if st.get(k):
            out[k] = st[k]
    if st.get("note") and "note" not in out:
        out["note"] = st["note"]
    return out


def memory_tool_result(store, query: str, resolve, intent: str = "current") -> tuple[str, list[str]]:
    """resolve(group) -> Resolution. Returns (observation, ids retrieved by similarity)."""
    hits = store.search(query)
    hit_ids = [h["record_id"] for h in hits]
    shown, seen, added = list(hits), {h["record_id"] for h in hits}, set()
    for h in hits:
        for g in store.same_key(h):
            if g["record_id"] not in seen:
                shown.append(g)
                seen.add(g["record_id"])
                added.add(g["record_id"])
    cache = {}
    results = []
    for h in shown:
        key = (h["entity"], h["attribute"])
        if key not in cache:
            cache[key] = resolve(store.same_key(h))
        item = {"record_id": h["record_id"], "text": h["text"], "recorded_on": h["recorded_on"], "source": h["source"],
                "reliability": label(h["record_id"], cache[key], intent)}
        if h["record_id"] in added:
            item["added_by_reliability_check"] = True
        results.append(item)
    return json.dumps({"results": results}), hit_ids
