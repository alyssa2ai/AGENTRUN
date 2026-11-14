# Candidate mechanisms

**13 November 2026.** Each candidate starts from a failure measured in `FAILURE_TAXONOMY.md` (M1–M7) and is checked against the full-text review (`RELATED_WORK_DEEP_DIVE.md`).

The brief's working title, "Adaptive Evidence-Gated Memory", had six components. Only those tied to a measured failure are kept; the others are listed at the end with the reason they were dropped.

## Candidate 1: Advisory-versus-enforced resolution (Resolution-Checked Submission, RCS)

**Targets.** M1 (resolution failure), M2 (labels ignored by small models), M3 (retrieval skipped).

**Research question.** When an agent is given reliability information about its memory (superseded, conflicting, current), at what model capacity does *telling* the model suffice, and when must the information be *enforced* at the terminal action? What does enforcement cost when the metadata is wrong or insufficient?

**Core algorithm** (`prototype/rcs.py`, about 60 lines of decision logic):

1. Records are labelled exactly as in config E (deterministic `(entity, attribute)` grouping, latest `recorded_on`).
2. When the agent submits, compare the submission with the labels of the records *the agent itself retrieved* whose entity is named in the question:
   - **R1:** the answer equals a superseded value and no current value.
   - **R2:** the agent reports "conflict" but no retrieved key has a same-date conflict.
   - **R3:** the agent submits without having searched memory and without a successful registry result.
3. If any rule fires, return **one** corrective notice that names the records. The next submission is final.
4. RCS never changes the answer itself and never sees ground truth.

Hard override (replace the answer with the resolved value) is the ablation, not the default.

**What is different from prior work.**
- DISCERN and GPM enforce resolution; CICM and PACMI give advisory reminders.
- None of them compares the two **with the same information**, **across model size**, in an **agent loop**, or measures the **cost of enforcement when metadata is insufficient**.
- The mechanism itself is not novel: R3 is DISCERN's EarnedAbstainGate. The contribution is the controlled comparison.

**Overlap.** DISCERN (gates, bounce-once renderer); GPM (fail-closed release); CICM (reminder versus internal routing).

**Expected advantages.**
- Closes the 3B resolution gap (3B v2 E: 27 of 64 memory-task failures with gold in hand).
- Removes skipped retrieval.
- No extra model call unless a rule fires.
- Unlike the same-model verifier, it cannot overturn an answer by itself.

**Potential disadvantages.**
- **Brittle when metadata is insufficient** (S7, S8): pushes toward "conflict" or toward the wrong record.
- **Anchoring is textual:** the entity must appear in the question. Pronouns or aliases defeat it.
- **R3 can disturb correct registry-only or abstain behaviour.**
- **Structured `(entity, attribute)` keys are required.**

**Required changes.** None to the frozen harness. One new loop function and two new configurations (G: gate without verifier; R: G + RCS), already implemented.

**Data.**
- Phase 1: the development-only stress split `p1dev` (S1–S6 regenerated, plus S7 same-day correction and S8 date-only-in-text).
- Phase 2: a new sealed split, and STALE as the external benchmark.

**Metrics.**
- success;
- false-conflict and over-abstention rates on answerable tasks;
- stale-value rate;
- conflict accuracy (S3);
- appropriate abstention (S5);
- intervention rate;
- fix rate and break rate of interventions;
- tool and model calls;
- latency.

**Ablations.**
- B (memory only);
- G (labels only);
- E (labels + same-model verifier);
- R (labels + RCS);
- R without R3, and R3 only;
- hard override instead of a notice;
- labels given as a value reminder (CICM style) instead of record statuses.

**Compute.** One pass of 64 tasks × 5 configurations takes about 13 min at 3B and about 25 min at 7B on one L40 (measured in Phase 1).

**Falsified if:**
- (i) R − G ≤ 0 at 3B on a held-out split; or
- (ii) the R − G gain does not shrink with capacity, meaning it is a general prompt effect rather than an enforcement-for-weak-models effect; or
- (iii) R's break rate (correct submission turned wrong) is at least its fix rate on stress scenarios S7/S8 for every size.

## Candidate 2: Evidence-state signalling (missing versus negative evidence)

**Targets.** M5 (search loops) and M6 (missing-evidence handling).

**Research question.** Does an explicit, deterministic "coverage" signal in the retrieval result reduce search loops and over-abstention without increasing unsupported answers? The signal would say, for example: "no record for entity X, attribute Y exists in memory" versus "records about X exist, but none for Y".

**Core algorithm.** The memory tool reports, beside the top-k records, whether any stored record matches the queried entity and attribute (an exact-key index), plus a "searched before" counter.

**What is different.** Self-RAG, CRAG and adaptive-retrieval work decide *whether to retrieve*. This is about *what retrieval tells the agent when nothing is found*. DISCERN's "verified absence" for abstain is close.

**Advantages.** Directly targets loops (7–89 per 480 runs) and abstention behaviour.

**Disadvantages.**
- The measured size of the problem is smaller: unsupported claims are already rare (0–4 per 100).
- It needs the question's attribute, which the harness does not know without parsing.
- Overlaps with DISCERN.

**Required changes.** A new memory-tool result format; an attribute-extraction step.

**Data.** S5, S6 and new loop-prone tasks. **Metrics:** step-limit rate, tool calls, unsupported answers, over-abstention.

**Falsified if** loops are not reduced, or unsupported claims rise.

## Candidate 3: Text-aware temporal validity (beyond structured timestamps)

**Targets.** Metadata insufficiency (S7/S8), and the limit of every timestamp gate, including ours. STALE's "implicit conflict" sits here.

**Research question.** Can a small model extract temporal order from record text ("as of", "correction") at write time well enough that a deterministic gate stays correct when metadata is missing?

**Core algorithm.** At write time, an LLM extracts `(entity, attribute, value, valid_from, corrects?)` into structured fields. The gate then runs on the extracted fields.

**What is different.** This is CUPMem's and DISCERN's write-time extraction; the difference would only be the small-model and error-propagation study.

**Disadvantages.** Requires memory writes, which the harness does not have (`ARCHITECTURE_AND_FAILURE_ANALYSIS.md` item 12). Higher cost. Weak novelty.

**Falsified if** extraction errors cause more harm than the gate prevents.

## Components of "Adaptive Evidence-Gated Memory" not pursued now

| Component | Why not now |
|---|---|
| Retrieval necessity assessment (learned) | Skipped retrieval is real (M3) but fixed far more cheaply by R3. A learned policy is not justified by 6/64 cases |
| Provenance-aware evidence scoring | Retrieval is already near-perfect here (0–1 of 256 runs miss gold); no measured failure to fix |
| Bounded retrieval / termination | Candidate 2; second priority |
| Failure-driven memory updates | No write path in the harness; nothing to measure yet |

## Comparison

| | Measured failure size | Prior-work overlap | Novel *question*? | Cost | Phase 1 feasible |
|---|---|---|---|---|---|
| 1 RCS / advisory versus enforced | Large at 3B (27/64 failures with gold in hand) | High on mechanism, **none on the comparison** | Yes | Low | **Yes (implemented, piloted)** |
| 2 Evidence-state signalling | Medium (loops) | Medium | Partly | Low–medium | Partly |
| 3 Text-aware temporal validity | Unknown (S7/S8 pilot measures it) | High | Weak | High | No |

---

## Addendum, 14 November 2026: what the completed pilot changed

### Candidate 1 (RCS) after the full pilot

- **The enforcement benefit is real at 3B and 7B but conditional:** +18 and +12 pp R − G.
- **It inherits the label's errors.** It cannot repair metadata-insufficient cases (S7/S8: R − G ≈ 0), where the labels themselves cause −23 to −50 pp at ≤ 8B.
- **Its R3 rule** (DISCERN's EarnedAbstainGate) breaks correct abstentions at 3B.
- **RCS alone is not a defensible contribution.** It survives as the enforcement layer of Candidate 4.

### Candidate 3, revised and implemented as Candidate 4: Temporal Evidence Arbitration (TEA) with an evidence basis

**Targets.** M8 (label over-trust on wrong or incomplete metadata) and M9 (enforcement inheriting label errors), from `FAILURE_TAXONOMY.md` §6.2.

**Algorithm** (`prototype/tea.py`; deterministic, no LLM, about 120 lines). For each `(entity, attribute)` group, the order comes from the strongest available evidence:
1. validity dates stated in every record's text, which outrank `recorded_on`;
2. otherwise `recorded_on`;
3. on a tie, an explicit correction that names the rival value;
4. otherwise `conflicting`, with basis `no_ordering_evidence`;
5. a missing date gives `unordered`.

Each label carries its `basis`, and a `note` when the basis overrides metadata.

**Configurations:**
- **T**: G with TEA labels.
- **RT**: R with TEA labels.

The status function is the **only** difference. It is swapped in for the duration of a run, so `rcs.py` and the frozen memlab are unchanged.

**Change from version 1's Candidate 3.** No write-time LLM extraction and no memory writes. TEA runs at read time over stored text, so it fits the read-only harness.

**Offline arbiter accuracy** (`scripts/arbiter_offline_eval.py`, no GPU). Labels are counted correct if the resolution-relevant gold records get the right status:

| Split | Scenario | Legacy gate | TEA |
|---|---|---|---|
| p1dev | S3 conflict / S4 stale | 8/8, 8/8 | 8/8, 8/8 |
| p1dev | S7 same-day correction / S8 dates in text | 0/8, 0/8 | **8/8, 8/8** |
| p1hold (frozen before TEA) | H7a correction naming old value | 0/6 | 5/6: misses phrasing "Disregard … confirmed" |
| p1hold | H7b correction not naming old value | 0/6 | **0/6**: falls back to `conflicting` |
| p1hold | H8a validity dates, long form | 0/6 | 5/6: misses "As at" |
| p1hold | H9 back-filled entry (metadata order reversed) | 0/6 | 6/6 |
| p1hold | N1/N2 genuine conflicts | 12/12 | 12/12 |
| p1hold | **N3 genuine conflict with negated cue ("does not replace the 298600")** | 6/6 | **0/6: false resolution** |
| p1hold | C4 metadata-ordered control | 6/6 | 6/6 |
| eval2 (Campaign 2) | S3 / S4 | 16/16, 16/16 | 16/16, 16/16 |

**Regressions** (TEA changes a status without a text basis): **0** on all three splits.

**What is different from prior work.**
- Valid-time-over-transaction-time is DISCERN's bitemporal design and classical database practice, so it is **not novel**.
- What prior systems lack:
  - (i) a label that **states its evidence basis**, so that enforcement can be **gated on the basis**;
  - (ii) a measurement of the **downstream harm of wrong labels** on small agents;
  - (iii) a measurement of the **new harm the arbiter introduces** (false resolution: N3).
- See `RELATED_WORK_DEEP_DIVE.md` §4.

**Disadvantages.**
- The lexicon was written by the same author as the splits. Even after freezing p1hold first, generalisation to other people's phrasing is untested (Phase 2 step 2.6).
- Negation and hypotheticals defeat it.
- It needs the rival's value to appear in the correcting text.

**Falsified if:**
- (i) RT − R ≤ 0 on text-resolvable tasks at 3B on a sealed split; or
- (ii) TEA's false resolutions cause more harmful answers (arbitrary picks) than its correct resolutions remove; or
- (iii) an LLM arbiter (TEA-LLM) dominates it at comparable cost. In that case the contribution is the measurement, not the arbiter.
