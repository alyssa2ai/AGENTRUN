# Architecture and failure analysis (memlab harness, as implemented)

**13 November 2026.** Everything below was read from the code, not from documentation:

- `research/AGENTRUN_DEEPENING_2026-11-11/scripts/memlab.py`, sha256 `dc28584c…`, identical on the laptop and on `sit-gpu`;
- `run_ablation.py`;
- `hf_client.py`;
- the repository's `memory.py`, sha256 `8d73adf3…`.

Line numbers refer to `memlab.py`.

## 1. The pipeline, step by step

```
user prompt ─▶ agent loop (≤ MAX_STEPS = 6 model calls, l.570)
               ├─ model emits tool calls (Hermes format, parsed by agentrun_v2.parser in hf_client)
               │   ├─ calculator        → tools.calculator
               │   ├─ registry_lookup   → scripted Registry (fault injection plan, l.359–377)
               │   └─ memory_search     → MemoryStore.search → memory_tool_result (l.299, l.326)
               ├─ model emits submit_answer {status: answer|abstain|conflict, value, evidence}
               └─ (v2 only) one repair turn if the model writes plain text instead of submitting (l.583)
         ─▶ optional same-model verifier on status=answer drafts only (configs C–E, l.641)
         ─▶ final answer ─▶ deterministic scorer (classify, l.690)
```

## 2. The 14 questions of the brief

| # | Question | What the code does | Evidence |
|---|---|---|---|
| 1 | Where is retrieval initiated? | Only when the model calls `memory_search` | `run_task` l.623 |
| 2 | Is retrieval unconditional? | No. It is model-initiated and optional. It is never forced, even when the prompt says the facts were given earlier | Same; Phase 1 failure data: Qwen2.5-7B v2 never searches on 6 of 64 memory tasks in **every** configuration |
| 3 | How is relevance scored? | Hashed bag-of-words embedding (`memory.embed_text`, 256 dims), cosine, top-k = 4, threshold 0.2 | l.299–303, `memory.py:29` |
| 4 | Timestamps / validity metadata? | Every record has `recorded_on`, `source`, `entity`, `attribute`, `value`. The model sees `recorded_on` and `source` only in D/E; `entity` and `attribute` are never shown as fields | l.333–345 |
| 5 | Contradictions? | Config E only. `reliability_status` groups records by exact `(entity, attribute)`, takes the latest `recorded_on` as current, and marks older differing values "superseded" and same-date differing values "conflicting". The status is **added to the tool result as text**; the model decides what to do with it | l.309–323, l.336–344 |
| 6 | Provenance representation | `record_id`, `recorded_on`, `source` fields in the JSON tool result (D, E) | l.341 |
| 7 | Stale detection | Only by the structured `recorded_on` comparison above; never from text. Records whose order is stated only in text (e.g., "Correction: …") are labelled "conflicting" | l.309 |
| 8 | When is verification triggered? | After the loop, only if the draft's status is `answer`. Abstentions and conflicts are never verified. The verifier can only downgrade (to abstain or conflict), never correct | l.641–656 |
| 9 | Same model as verifier? | Yes: `client.chat` with the verifier prompt, same model, same decoding. In C it sees the evidence without provenance | l.645 |
| 10 | Search termination | Only the step budget (6 calls) and a prompt rule (v2 rule 7: "never repeat a tool call that already returned a valid result"). No code-level loop detection | l.570, l.424 |
| 11 | Do tool failures affect future behaviour? | Only within one run, through the conversation. Nothing persists across tasks | `Registry` per run, l.562 |
| 12 | Memory writes, updates, deduplication, deletion | **None.** Stores are fixtures written once per task from the benchmark and reloaded; the agent has no write tool. "Failure-driven memory updates" (direction D of the brief) cannot be studied in the current harness | `MemoryStore.__init__` l.291 |
| 13 | Missing vs negative evidence | Not distinguished. An empty result (`{"results": []}`) is returned both when nothing exists and when everything falls under the similarity threshold. There is no "searched, no record for this entity/attribute" signal. Near-miss records (S5) look like evidence | l.299–303 |
| 14 | Extra latency / failure modes | The verifier adds one model call per answered draft (its latency is logged per run in `api_calls`, role `verifier`; not separately quantified here). Retrieval is under 1 ms per call. The verifier adds a new failure mode: overturning correct drafts (§3) | `score_run` timing fields |

## 3. Architectural weaknesses, ranked by measured impact

Counts come from `FAILURE_TAXONOMY.md` and `data/failure_attribution.json` (Campaign 2, eval2, greedy).

1. **Resolution is advisory.**
   - The gate labels records, but the model still makes the terminal decision.
   - Qwen2.5-7B follows the label (S4, config E: 16 of 16 correct). Qwen2.5-3B, shown the same label, still answers "conflict" on 14 of 16. Under config E, 3B's memory-task failures with all gold records in hand are 27 of 64.
   - **This is the largest remaining failure for small models, and nothing in the harness acts on it.**
2. **Retrieval is never forced.**
   - With memory available, models skip `memory_search` and either abstain or submit an invented draft. In one case the model cited tool calls it never made: Qwen2.5-7B v2, `eval2-S1_context_loss-00`, config E — draft "12500.00" with zero tool calls.
   - 7B v2: 6 of 64 memory tasks per configuration. 3B v2: 8 of 64. 1.5B: 256 of 256.
   - The v2 prompt rule 6 ("search memory before deciding that a fact is unavailable") did not remove it.
3. **Same-model verification overturns correct drafts.**
   - Precision is low: under v2, config C, 7 harmful drafts caught against 22 correct drafts rejected (7B + 8B). Qwen2.5-7B v2, C: 19 correct drafts rejected out of 150 verified.
   - The verifier never sees provenance in C, and it cannot fix an answer, only withdraw it.
4. **No code-level loop control.**
   - Step-limit failures are 7–89 per 480 runs.
   - The worst case is Qwen3-8B v1 (89/480). Its B/C runs on S3/S4 repeat `memory_search` and `registry_lookup` with the gold records already retrieved.
5. **Missing and negative evidence are not distinguished** (item 13). The agent cannot tell "no such record" from "retrieval missed it". This matters for S5 (unsupported) and S6.
6. **Stale detection relies entirely on structured timestamps.** Text-stated order (corrections, "as of" dates when metadata is equal) is invisible to the gate. Phase 1 adds stress scenarios S7/S8 to measure this.
7. **Benchmark-harness interaction** (construct-validity issue found in Phase 1).
   - In S4 `date_in_metadata_only` tasks, configurations B and C show the model no date at all, so two different values for the same fact *are* an unresolvable conflict from the model's point of view.
   - B/C "false conflicts" on those tasks are therefore not reasoning errors. This half of S4 can only be solved when provenance is visible (D/E).
   - Part of the measured B → D gain on S4 is by construction.
8. **No memory writes.** Directions D (failure-driven updates) and part of B (temporal validity at write time) cannot be studied without new code.

## 4. What the existing implementation can and cannot address

| Failure | Can the current harness fix it? |
|---|---|
| Advisory label ignored (small models) | No. Needs an enforcement point at the terminal action |
| Retrieval skipped | Only by prompt (already tried in v2; insufficient) |
| Verifier overturns correct answers | Only by removing it, or replacing it with a non-LLM check |
| Loops | Only by the step limit |
| Text-only temporal order | No (structured metadata only) |
| Write-time errors | Not applicable (no writes) |

The Phase 1 prototype (`prototype/rcs.py`) adds the smallest change that targets rows 1–3: a deterministic check at the terminal action with one corrective turn. Rows 4–6 are left for Phase 2.

## 5. Addendum (14 November 2026): where the Phase 1 mechanisms attach

```
memory_search ─▶ memlab.memory_tool_result ─▶ reliability_status(rec, group)   ◀── TEA swaps this function (configs T, RT)
                                                   │  labels shown to the model (G, R, T, RT)
submit_answer ─▶ rcs.check_submission (R, RT) ── reads the same reliability_status ──▶ one corrective notice (R1/R2/R3)
```

- **TEA** (`prototype/tea.py`) replaces `memlab.reliability_status` for the duration of one run (context manager `tea_labels()`). The frozen `memlab.py` (sha256 `dc28584c…`) and `rcs.py` (`9f0a838b…`) are unchanged.
- Because RCS reads the label through the same function, **R and RT differ only in what the labels assert**. That isolates label correctness from enforcement.

**Weaknesses this exposes in §3:**
- **Item 6** ("stale detection relies entirely on structured timestamps") is the root cause of failure M8 (`FAILURE_TAXONOMY.md` §6.2). Its cost is now measured: S7/S8 G − B = −23 to −50 pp at ≤ 8B.
- **Item 1** ("resolution is advisory") is only half the story. Enforcement (R) helps when the label is right and cannot help when it is wrong.

**New weakness found:**

15. **RCS notice text assumes metadata order.** The R2 notice says "no two different values on the same latest date". Under TEA's explicit-correction basis, that is false: the two values *are* on the same date. Phase 2 step 2.3 gives each basis its own notice.
