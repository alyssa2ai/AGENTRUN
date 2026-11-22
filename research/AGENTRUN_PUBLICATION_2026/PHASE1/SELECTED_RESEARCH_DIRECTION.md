# Selected research direction

**Revised 14 November 2026** after the completed pilot (`PILOT_RESULTS.md`). The 13 November version is kept below as §B, for the record.

## A. Current direction (14 Nov)

### The question

> **What may a memory-reliability label assert, given the evidence behind it, and when must that assertion be enforced rather than merely shown, for small open-weight tool-using agents?**

Working title: *"Labels that know what they know: evidence-basis arbitration and capacity-dependent enforcement for agent memory."*

### Why the 13 Nov question ("tell or enforce?") was incomplete

1. **The label itself is a harm source on metadata-insufficient memory.**
   - When `recorded_on` cannot order two records (same-day correction; bulk import with validity dates in the text), the metadata gate labels them `conflicting`.
   - Models ≤ 8B then answer `conflict`, although *without* the label they read the text and answer correctly.
   - Qwen2.5-7B: S7 22/24 → 3/24; G − B on S7/S8 −50 pp, family p = 0.004. 14B is immune.
2. **Enforcement inherits that error** (R − G on S7/S8 ≈ 0). "Enforce more" cannot be the answer.
3. **Fixing what the label asserts works, and how it must be delivered depends on capacity** (greedy, exploratory; `PILOT_RESULTS.md` §5):
   - **3B:** needs enforcement. On p1dev, T 28/64, RT 53/64. On held-out p1hold, RT 35/48 against ≤ 23 for every other configuration.
   - **7B / 8B:** advice suffices. On p1dev, T 49/64 and 64/64. On p1hold, T is best (36/48 and 40/48).
4. **Enforcement amplifies label errors in both directions.**
   - With TEA's false resolutions (p1hold N3), RT produces 5–6 arbitrary picks per model, against 0–1 under T.
   - With the legacy label on back-filled entries (H9), R turns 5/6 3B false conflicts into stale answers.
   - Hence **basis-gated, capacity-aware enforcement** is the mechanism to test in Phase 2 (H5).

### The defensible contribution (scope agreed with `RELATED_WORK_DEEP_DIVE.md` §4)

- **Measurement 1: label-induced harm.** The cost of a confident metadata-derived reliability label when the metadata is insufficient or wrong, on 3B–14B agents. Prior enforcing systems (DISCERN, GPM, CUPMem) decide over a write-time structure and do not measure this.
- **Measurement 2: the capacity profile of enforcement.** Enforcement is needed at 3B (and helps at 7B), but is useless above about 8B, and harmful when the label is wrong.
- **Mechanism: evidence-basis labels with basis-gated enforcement (TEA + RT-gated).**
  - The temporal rules are standard, since valid time over transaction time is DISCERN's bitemporal design.
  - The new parts are a label that states its basis, enforcement conditioned on that basis, and an explicit accounting of the arbiter's own false resolutions (p1hold N3: a negated cue).

**Not claimed:**
- deterministic gating;
- search-before-abstain (R3 = DISCERN's EarnedAbstainGate);
- bitemporal ordering;
- a staleness benchmark;
- "retrieval is solved, resolution is not".

### Answers to the brief's specific questions (pilot evidence)

| Question | Answer so far |
|---|---|
| Can metadata be wrong or incomplete? | Yes, by construction in S7/S8/H9. The legacy gate is wrong on 100% of these (0/16 p1dev, 0/18 p1hold H7a/H8a/H9) |
| Should source text override misleading metadata? | Only when the text carries explicit ordering evidence (validity dates for every record, or a correction naming the old value). Lexical cues alone over-fire: a negation turns a true conflict into a confident wrong order (N3 0/6) |
| Same-day correction vs true conflict? | Correction cue **plus** reference to the rival value. Without the value reference (H7b) TEA correctly declines to resolve; with a negated cue (N3) it wrongly resolves. Precision is the open problem |
| Source authority and temporal order? | Not used. In this benchmark a same-day two-source disagreement is defined as a genuine conflict (S3), so authority-based resolution would contradict the ground truth. Phase 2 needs tasks where authority is the intended tie-breaker before it can be studied |
| Reduce unnecessary abstention without more unsupported answers? | Over-abstention with memory is already low (≤ 13/138 at 3B, ≤ 2/138 at 7B). The bigger lever is false conflict. Unsupported answers stayed ≤ 2/30 in every configuration |
| Model- or uncertainty-dependent policy? | Model-dependent enforcement is supported (H2). Uncertainty-dependent in the sense of *evidence-basis* dependent (H5) is the Phase 2 test. Model-internal uncertainty was not measured |

### Hypotheses and Phase 2

H1–H6 and the Phase 2/3 plan are in `EXPERIMENTAL_RESEARCH_DESIGN.md` (v2).

---

## B. Direction as selected on 13 November (superseded; kept for the record)


## The question

> **When does an LLM agent need memory-reliability information *enforced* rather than merely *shown*, and what does enforcement cost when that information is wrong?**

Working title: *"Tell or enforce? Capacity-dependent compliance with memory-reliability signals in small LLM agents."*

## Why this question, and not the original "component ablation"

1. **It comes from a measured failure, not a design preference.**
   - In Campaign 2 the dominant failure on memory tasks is not hallucination. It is wrong terminal action with the evidence in hand (`FAILURE_TAXONOMY.md` §2).
   - The same advisory label fixes it at 7B (S4/E: 16 of 16 correct) and does not at 3B (2 of 16; 14 false conflicts with "superseded" visible).
2. **The mechanisms are published; the comparison is not.**
   - DISCERN and GPM *enforce* resolution with deterministic code on large backbones.
   - CICM and PACMI *advise* the model.
   - CICM finds that obeying an explicit reminder depends on the model family (Qwen2.5-3B 99% versus Llama-3.2-3B 69%), but in non-agentic dialogue.
   - No paper holds the reliability information fixed and varies only *how it is delivered*, across model size, in a tool-using agent. None measures the cost of enforcement when metadata is insufficient.
3. **It reframes earlier AGENTRUN findings into one account:**
   - the advisory gate helps 7B/8B (+16.7 pp) but not 3B or 14B;
   - the same-model verifier hurts (an LLM "enforcer" with low precision);
   - small models do not even query memory (1.5B: 0 of 256).
4. **The intervention is minimal and falsifiable.** One deterministic check at the terminal action and one corrective turn; no new architecture.

## What would count as new knowledge

- **A capacity curve of advisory compliance** (G − B) **and of enforcement benefit** (R − G) in one model family, then replicated in a second family.
- **A measured trade-off:** RCS's fix rate on metadata-sufficient tasks versus its break rate on metadata-insufficient tasks (S7, S8, and STALE-style implicit conflicts). This is a cost the enforcing systems do not report.
- **A practical rule:** the model size below which reliability logic must live in code, given clean metadata.

## Hypotheses (to be tested in Phase 2 on a sealed split; the Phase 1 pilot is exploratory)

- **H1.** Advisory compliance rises with capacity: the G − B gain on S3/S4-type tasks is near zero at 3B and positive at 7B/8B. Campaign 2 already shows this pattern once.
- **H2.** Enforcement benefit falls with capacity: R − G is positive at 3B and near zero at ≥7B.
- **H3.** Enforcement has a cost on metadata-insufficient tasks (S7/S8). R's break rate there exceeds G's error rate for capable models.
- **H4.** Rule R3 (search before submitting) removes skipped retrieval without raising unsupported answers.

**Falsification.**
- H2 fails if R − G is no larger at 3B than at 7B on the sealed split (family-level test).
- H3 fails if R does not lower success on S7/S8 relative to G at any size. In that case enforcement is "free" and the paper's trade-off claim disappears; the result becomes a simpler "always enforce" recommendation.

## Scope boundaries

- Thread 2 only; the October QLoRA work stays separate.
- No new benchmark of record: STALE is the external test, and memlab splits are development and validation material.
- RCS is not claimed as a novel mechanism.

## What Phase 2 should implement

1. Ablation configurations:
   - R-noR3, and R3-only;
   - hard override instead of a notice;
   - a value-reminder variant (CICM-style: "current value: V") versus a record-status label.
2. A new sealed memlab split (≥40 families, held-out templates, S7/S8 included), frozen and pre-registered before any run.
3. A second model family. The Llama snapshots on `<compute-node>` are incomplete (3.2-3B: 8.9 MB; 3.1-8B: 5.3 GB), so a complete download or another family is needed.
4. Three decoding seeds plus greedy.
5. A STALE subset adapter (State Resolution and Premise Resistance) with the record-status interface.
