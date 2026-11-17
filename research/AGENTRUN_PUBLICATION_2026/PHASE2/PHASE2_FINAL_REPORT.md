# Phase 2 report (interim — Phase 2 is not complete)

**16 November 2026.** This report states what Phase 2 has established and what it has not. Phase 2 is **not** complete: the three GPU jobs that finish it (p2val2, eval3 build and seal, agent-level validation) are queued but blocked by another user's job that holds all of the node's memory (`PHASE2_STATUS.md` §2). This document must be rewritten when they have run; until then, do not cite it as a completed phase.

## 1. What was built

- **evarb**, a deterministic evidence arbiter for conflicting memory records: clause-scoped cues with negation, quotation and modality scope; ten evidence bases with strength; precedence rules; basis-gated enforcement with one reversible notice and safe submission (`EVIDENCE_ARBITRATION_SPEC.md`, `SYSTEM_ARCHITECTURE.md`).
- Baselines under the same interface: legacy metadata labels, Phase 1 TEA, and an LLM evidence arbiter with the same output schema.
- A Llama-3.x adapter that leaves the frozen client unchanged (`MODEL_FAMILY_READINESS.md`).
- A benchmark pipeline in which the gold is fixed before any text exists, texts are written by a model that never sees the mechanism or the gold, and labels are checked by blind annotators; split-boundary and leakage checks that print counts only (`BENCHMARK_EVAL3_SPEC.md`).
- Phase 3 scripts with freeze and seal gates (`PHASE3_EXECUTION_PLAN.md`).

## 2. What the evidence shows so far

| Claim | Evidence | Strength |
|---|---|---|
| evarb implements the intended behaviour on negation, conflicts, conditional and quoted corrections, same-day changes, missing timestamps, historical questions and authority ties | 86 tests; 160/160 development groups; every Phase 1 failure family fixed (`NEGATION_AND_CONFLICT_TESTS.md`) | development only (tuned on) |
| On independently written text, evarb's arbitration is more accurate than legacy labels, TEA and an LLM arbiter (3B–14B) | p2val: 56/70 vs 35 (legacy), 34 (TEA), 25–39 (LLM); +24 to +44 pp, family-bootstrap CIs exclude 0 | **post hoc**: evarb-0.2 was revised after seeing p2val |
| evarb's errors are mostly not enforceable | p2val current-intent: 0 enforceable errors (legacy 28, TEA 29, LLM 12–33) | post hoc, component level |
| LLM arbiters falsely resolve genuine conflicts | p2val false resolutions: Llama-3.1-8B 24, Qwen2.5-7B 18, Qwen2.5-14B 14, evarb 7 (all 7 are v1/v2 semantic disagreements, moderate, never enforced) | component level |
| A long-range negation produces a strong false correction | constructed example, pinned in `tests/test_known_limitations.py` | known limitation of the frozen version; listed in `PREREGISTRATION.md` §12 |
| 6 of the 11 excluded p2val items were validator false negatives (long-form dates); 9 of 14 deadline items were lost | `data/p2val/P2VAL_EXCLUSION_REVIEW.md` | p2val is unbalanced over attributes; eval3 uses ISO value dates only |

**Not yet shown:** any result for the frozen evarb-0.2 on untouched data (p2val2), any agent-level result for evarb, and anything on eval3.

## 3. Decisions taken

- **Freeze:** evarb-0.2 is frozen (14 Nov) and was not modified in this session, even where a limitation was found (§2 last row). The p2val look is logged; p2val is development data.
- **Semantics v2:** a record that does not establish its own value (negated replacement without "both stand", reported claim, conditional) leaves the established value standing. Adopted after the blind annotation showed the v1 gold was inconsistent; eval3 and p2val2 use v2.
- **eval3 design:** 276 items, 23 categories, 138 families, no human validation (stated as such).
- **Phase 3 design:** Holm family {EBG−RT (primary), EBG−T, EBG−LG, EBG−B}, primary models Qwen2.5-3B/7B and Llama-3.1-8B with four decodings (`PREREGISTRATION.md`, draft).

## 4. Remaining work (all scripted)

See `PHASE2_STATUS.md` §5. Estimated: ≈ 7.5 GPU-hours for Phase 2 completion, then CPU analysis; Phase 3 ≈ 109 GPU-hours (recalculated from measured model-specific times; final figure from p2val2 timings).
