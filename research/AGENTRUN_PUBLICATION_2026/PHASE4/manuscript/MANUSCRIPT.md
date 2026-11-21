# Evidence-Basis Arbitration for Conflicting Persistent Memory in Small Tool-Using Agents: A Preregistered Evaluation of Gated Enforcement

## Abstract

Agents with persistent memory must act on records that contradict each other, and the usual remedy — attaching
reliability labels derived from record metadata and enforcing them at the terminal action — can make small models
worse rather than better. We ask whether arbitration that reports the *evidence basis* for each resolution, and
enforces only resolutions that basis supports, improves reliability, and whether enforcing resolutions
indiscriminately increases harmful answers.

We evaluate Evarb-0.2, a deterministic arbiter that assigns each record a status, an explicit evidence basis and a
strength, shows those labels to the agent, and at the terminal action issues one reversible notice but enforces only
strong-strength resolutions. The mechanism, the analysis and the hypotheses were frozen and preregistered before the
confirmatory data existed. The confirmatory campaign ran 18 model × decoding cells over 12 configurations on 268
sealed tasks in 135 families — 57,888 agent runs, with no missing pair, duplicate or harness error — using four
primary open-weight models from two families (3B–8B) and two secondary models, under family-clustered sign-flip
permutation inference with Holm correction.

All four preregistered contrasts are supported. Gated evidence-basis arbitration raised task success over enforced
record-and-temporal labels by 17.1 pp (95% CI [12.2, 22.1], Holm p = 4 × 10⁻⁵), over advisory temporal labels by
14.5 pp, over an LLM arbiter under the same gated policy by 15.9 pp, and over unlabelled memory by 15.3 pp. The
harmful-answer rate fell from 22.6% to 3.1% and arbitrary picks from 252 runs to 13. Ablations locate most of the
benefit in the labels themselves (+11.8 pp without any enforcement) rather than in enforcement (+6.0 pp), and the
development finding that metadata labels *hurt* small agents replicates on sealed data.

Two results qualify the contribution. Enforcing every arbitration rather than only strong ones scored 9.7 pp
*higher* than the gated mechanism while more than doubling harm and raising false resolution from 1.9% to 12.9%:
gating trades accuracy for safety rather than dominating. And the same gating machinery driven by an LLM arbiter
gave no success gain and 8.1 pp more harm, indicating that enforcement inherits the reliability of whatever supplies
its labels. Effects also differ by model family: the Llama models gain by converting abstentions into answers rather
than harmful answers into correct ones. We report the preregistered outcome, the exploratory trade that cuts against
our own design, and an unplanned mid-campaign platform transition affecting 1.69% of rows, whose removal moves the
pooled estimates by at most 0.1 pp.


# 1. Introduction

> Draft, 18 November 2026. Results-independent text only. Every statement about the confirmatory evaluation (eval3) is a placeholder until the Phase 3 outputs are verified. Citation keys refer to `references.bib`.

## 1.1 Persistent memory in small tool-using agents

Tool-using language-model agents increasingly keep a persistent memory: records written in earlier sessions that the agent can search before it answers [@packer2023memgpt; @chhikara2025mem0; @rasmussen2025zep]. Persistent memory is useful because the facts an agent is asked about change over time. A project's budget is revised, a server moves to a new port, a team lead is replaced. The same property makes memory hazardous. A memory store accumulates several records about the same attribute of the same entity, and these records can disagree. Some disagreements have a correct resolution: a later record supersedes an earlier one, a same-day erratum corrects a typo, or a record states the date from which its value is valid. Others have none: two records of equal standing assert different values and nothing in the evidence orders them. A third kind only looks like a disagreement: a record reports someone else's claim, states a hypothetical, or says explicitly that it does *not* replace the earlier value.

Recent work has established that this resolution step, rather than retrieval, is where memory-backed agents fail [@ahuja2026discern], and that agents may not use delivered memory at all [@xu2026delivered]. Benchmarks for stale and conflicting memory now exist [@chao2026stale; @hu2025memoryagentbench], and several systems resolve conflicts with provenance graphs, bitemporal stores or deterministic governance [@ahuja2026discern; @wang2026pacmi; @xu2026gpm; @wang2026toki]. Most of this work uses large hosted models as the agent backbone. Small open-weight models (here 3B–14B parameters), which are attractive for local and low-cost deployment, are less well characterised.

## 1.2 The problem addressed: false resolution and label-induced harm

This study is motivated by a specific failure observed during development, not by a general claim that memory safeguards help. In an exploratory pilot on development splits (Phase 1; one model family, mostly greedy decoding; never a confirmatory result), we gave small agents reliability labels derived only from record metadata (the date a record was written). When that metadata could not order the records, for example for a same-day correction or a pair ordered only by dates stated in the text, the labels declared the records "conflicting". The agents followed the label instead of the text. For Qwen2.5-7B on same-day corrections, correct runs fell from 22 of 24 without labels to 3 of 24 with metadata labels (`PHASE1/PHASE1_FINAL_REPORT.md` §1; `PHASE1/FAILURE_TAXONOMY.md` §6.2, mechanism M8). Enforcing the labels at the terminal action did not repair this, because enforcement reads the same labels (M9).

A follow-up arbiter that orders records from textual evidence (Phase 1's TEA) removed much of that harm on held-out development phrasings, but exposed the counterpart risk. When the arbiter itself resolved a genuine conflict wrongly (a negated cue read as a correction), enforcement turned 5–6 of 6 correct `conflict` answers per model into arbitrary picks (`FAILURE_TAXONOMY.md` §6.3, M11). We call this **false-resolution harm**: a mechanism confidently asserts an ordering that the evidence does not support, and the agent, or the harness acting for it, commits to a wrong value.

These pilot observations motivate the design tested here. They are development evidence: the splits were written by the mechanism's author and were used to build the mechanism. They do not support any claim about the frozen mechanism or about unseen data.

## 1.3 Approach

We test **evidence-basis arbitration** (Evarb). A deterministic arbiter, Evarb-0.2, assigns every record in a group of same-attribute records a status together with the *evidence basis* for that status (an explicit correction that names the rival value, a stated validity date, the record date, an authoritative source, a genuine contradiction, or insufficient evidence) and a *strength* (strong, moderate or none). The agent is shown these labels. At the terminal action, a policy may send one reversible notice when the submitted answer disagrees with the arbitration, but it enforces only resolutions of strong strength (**gating**). If the agent's response to a notice is unusable, the pre-notice answer stands (**safe submission**). The full configuration, EBG, also asks the agent to search memory before it submits when it has not done so (**search-before-submit**). Section 3 specifies the mechanism and the eleven comparison configurations.

The mechanism was frozen (`FREEZE_evarb.json`, 14 November 2026) before the confirmatory data set was built, and the confirmatory analysis was preregistered and frozen on 17 November 2026 before any confirmatory run (Section 4).

## 1.4 Research question

The research question is stated exactly as in the preregistration (`PHASE2/PREREGISTRATION.md` §1):

> For small open-weight tool-using agents with persistent memory: does evidence-basis arbitration of conflicting memory records, with enforcement gated on the strength of that evidence (EBG), give more correct terminal answers than enforcing a lexical temporal arbiter (RT), without adding harm on genuine conflicts?

## 1.5 What this study tests

We phrase the contributions as tests and artefacts. Whether any hypothesis is supported is unknown at the time of writing.

1. **A preregistered confirmatory comparison.** We test whether EBG yields higher task success than RT (H-primary), than advisory temporal labels T (S1), than an LLM arbiter under the same gated policy LG (S2), and than memory without labels B (S3), with Holm correction over these four contrasts; and whether EBG's harmful-answer rate is no higher than RT's (S4). The tests use family-clustered permutation inference on 268 sealed tasks in 135 families, four primary open-weight models from two families, and four decodings per primary model (Section 4).
2. **Component ablations, reported as exploratory.** The design isolates the value of enforcement (EBG − EB), of gating (EBG − EBG-all), of safe submission (EBG − EBG-unsafe) and of search-before-submit (EBG − EBG-noR3), with Benjamini–Hochberg control and no claim resting on them (E1–E5).
3. **A deterministic-versus-LLM arbiter comparison under one policy.** LA and LG fill the same output schema with the agent's own model as arbiter, so that the contrast EBG − LG separates *who arbitrates* from *what the policy does with the arbitration*.
4. **A sealed evaluation set whose gold is fixed before any text exists** (eval3; Section 5), written by a model that never saw the mechanism or the gold, with blind model annotation and no human validation. We do not present it as a benchmark of record.
5. **A pre-stated account of the mechanism's known failures** (Section 13), written before any confirmatory outcome.

**Results.** All four preregistered contrasts are supported: EBG raised task success over RT by 17.1 pp (95% CI [12.2, 22.1], Holm-adjusted p = 4 × 10⁻⁵), over T by 14.5 pp, over LG by 15.9 pp and over B by 15.3 pp, in the same direction for every model. S4 is not falsified: the harmful-answer rate was 3.1% under EBG against 22.6% under RT, and arbitrary picks fell from 252 runs to 13. The exploratory ablations place most of that benefit in the evidence-basis labels themselves rather than in enforcement, and one of them cuts against the design: enforcing every arbitration instead of only strong ones scored 9.7 pp higher while more than doubling harm. Sections 7 to 9 give the numbers, Section 12 the reading we take from them.

## 1.6 Scope

The study concerns small open-weight models (3B–14B) in one synthetic tool-use harness with templated records, English text and ISO-format value dates. It makes no claim about frontier models, natural memory logs, implicit conflicts without lexical cues, or other harnesses. Section 13 lists the limitations that were fixed before the confirmatory results existed.


# 2. Related work

> Draft, 18 November 2026. Sources: `RELATED_WORK_AND_NOVELTY.md` (abstract-level review of about 30 arXiv papers, 13 Nov 2026) and `PHASE1/RELATED_WORK_DEEP_DIVE.md` (full-text reading of six papers on 13 Nov, with DISCERN and STALE re-read on 14 Nov). Bibliographic data is from `literature/arxiv_metadata.json` and `literature/arxiv_title_search.json`. Unless a statement below is marked "full text", it rests on the paper's abstract only. The search covered arXiv only; Semantic Scholar rate-limited the session and no general web search was available, so non-arXiv venues are under-covered.

## 2.1 Memory architectures for agents

Persistent memory for language-model agents is usually built as a store outside the context window that the agent reads through retrieval or tool calls. MemGPT manages memory tiers by analogy with an operating system [@packer2023memgpt]; Mem0 extracts, consolidates and retrieves salient facts across sessions [@chhikara2025mem0]; Zep organises memory as a temporal knowledge graph [@rasmussen2025zep]. MEMOIR adds a training-free lifecycle with judge-gated consolidation [@anand2026memoir]. These systems are background for this study: our harness uses a deliberately simple store (hashed bag-of-words retrieval, top 4) so that the object of study is what happens *after* retrieval.

## 2.2 Staleness, conflict and resolution

**Resolution rather than retrieval.** DISCERN (full text) preserves an immutable event log at write time, derives a bitemporal fact store, and at read time lets the agent navigate with deterministic, LLM-free tools; the committed action (answer, update, abstain or clarify) is a decidable function of the graph, guarded by gates that include an *EarnedAbstainGate* that rejects abstaining without searching [@ahuja2026discern]. Its abstract reports that recall and currency are near-saturated and that resolution is the unsolved part. DISCERN's backbones are large hosted models (the smallest in its backbone comparison is 120B), its facts and validity intervals are LLM-extracted, and its ablations do not perturb extraction or timestamps.

**Provenance and invalidation.** PACMI (full text) propagates invalidation through a provenance graph with a four-state validity lattice and corrects outdated premises by adding old and current facts to the answer prompt, i.e. advisorily [@wang2026pacmi]. AMV-Guard (full text) treats re-verification of a memory premise before a state-changing action as a value-of-information stopping problem, evaluated on ToolSandbox and AppWorld with 27–35B cross-backbone checks [@wang2026amvguard]. Governed Persistent Memory (full text) uses a bitemporal state-transition model with deterministic, fail-closed release and reports that its governed lane outperforms an ungoverned local Qwen2.5-7B [@xu2026gpm]. TOKI formalises contradiction resolution as write-time concurrency control over bitemporal operators [@wang2026toki]. StateWise repairs invalid stored state before agent actions in coding agents [@peng2026statewise]. Security-oriented provenance work (PPMF, MemLineage) binds tool authority or lineage to the source of a memory [@xu2026ppmf; @ouyang2026memlineage]. Zhao et al. observe that outdated memory and poisoning call for opposite write decisions and propose an evidence-conditioned accuracy metric [@zhao2026accept]. Zhou et al. give a theory of when memory reuse is safe [@zhou2026manysteps].

**Benchmarks.** STALE (full text) provides 400 scenarios and 1,200 queries over three dimensions, including state resolution and premise resistance [@chao2026stale]. Its construction excludes explicit invalidation (surface negation, direct correction, explicit obsolescence marking), so it contains none of the lexically signalled cases that Evarb targets; it is the natural external test of what a lexical arbiter cannot do. MemoryAgentBench includes a conflict-resolution competency [@hu2025memoryagentbench]; Pakhomov and Nijkamp show that a frozen last-write rule answers a large share of its conflict split and that some gold answers are unreachable [@pakhomov2026bookkeeping]. LongMemEval and LoCoMo evaluate long-term conversational memory, including knowledge updates and abstention [@wu2024longmemeval; @maharana2024locomo].

**Why models fail on updates.** CICM (full text) studies in-context updates mechanistically. Probes still recover the updated value when the model answers with the old one ("stale binding"). The paper compares an explicit reminder with an internal attention intervention across Qwen2.5 and Llama sizes, and finds that how well models comply with the advisory reminder depends on the model family [@guo2026cicm]. This is the closest prior evidence on whether small models follow advisory signals about which value is current, although the setting is single-answer dialogue rather than an agent with a three-way terminal action.

**Use of memory.** Xu et al. find that delivered memory often does not change agent behaviour on SWE-bench Verified [@xu2026delivered]; Pathirage and Srijomkwan study when models decide to search beyond parametric memory [@pathirage2026confident]. Zhang and Sun issue deterministic answer/search/abstain decisions from sufficiency certificates in retrieval [@zhang2026horn].

## 2.3 Verification and self-correction

Same-model self-correction without external feedback often fails to improve reasoning and can degrade it [@huang2023selfcorrect; @kamoi2024survey]. Retrieval-side critique and correction are studied in Self-RAG and Corrective RAG [@asai2023selfrag; @yan2024crag]. Our LLM-arbiter baselines (LA, LG) use the agent's own model to arbitrate records. They are not self-correction of the answer, but their errors are of the same kind: an unaided small model judging evidence.

## 2.4 Comparison

Table 2.1 summarises the six papers read in full text against the design dimensions of this study. Entries for prior work are taken from `PHASE1/RELATED_WORK_DEEP_DIVE.md` §2 and §4. The last column describes what this study *tests*, not what it finds.

**Table 2.1.** Closest work, by design dimension.

| Dimension | DISCERN | PACMI | AMV-Guard | GPM | STALE / CUPMem | CICM | This study |
|---|---|---|---|---|---|---|---|
| Who makes the terminal decision | deterministic code over an LLM-built graph | LLM with prompt-level correction | decision-theoretic verification gate | deterministic services | LLM; constrained readout | the model (reminder or internal steering) | the agent; policy may send one reversible notice |
| Same information as advisory label vs enforced, compared | no | no | no (vs always/never/static policies) | no (governed vs ungoverned) | not directly | reminder vs routing | yes (T vs RT; EB vs EBG; LA vs LG) |
| Labels state their evidence basis; enforcement gated on it | no (uniform gates) | no | no | no | no | no | **tested** (EBG vs EBG-all) |
| Deterministic vs LLM arbiter under the same policy | no | no | no | no | no | no | **tested** (EBG vs LG) |
| Agents ≤ 14B, open weights | no | no | no | baseline only | partly (Qwen3.5-9B) | yes, not agentic | yes (3B–14B) |
| Cost of a wrong reliability label measured | no | partly | modelled | fail-closed by design | implicit conflicts | no | harmful-answer rates per configuration (S4) |
| Evaluation | ENT-310, LoCoMo | own (100 cases) | ToolSandbox, AppWorld | own, sealed | own, public | own | own, sealed, synthetic (eval3) |

## 2.5 What is new and what is not

**Not new, and not claimed.** The following are established by prior work or are true by construction:

1. Memory improves memory-dependent tasks.
2. Provenance, bitemporal ordering or deterministic gating improve staleness and conflict handling [@ahuja2026discern; @wang2026pacmi; @xu2026gpm; @wang2026toki]. On an existing conflict benchmark, a deterministic last-write rule already does well [@pakhomov2026bookkeeping].
3. Ordering by a stated validity date before the record date. This is standard bitemporal practice [@jensen1999temporal], and DISCERN's design.
4. Forcing a search before an abstention or answer. Our search-before-submit rule (R3/P3) is essentially DISCERN's EarnedAbstainGate.
5. Same-model verification without external signal can hurt [@huang2023selfcorrect; @kamoi2024survey].
6. Agents often fail to use delivered memory, and models can bind a stale value while still encoding the update [@xu2026delivered; @guo2026cicm].
7. A staleness or conflict benchmark. eval3 is synthetic, templated and model-annotated; STALE (400 expert-validated scenarios) and DISCERN's ENT-310 (human-vetted) are larger and have human validation, which eval3 lacks.
8. Combining known components into one system is not a contribution in itself.

**What may be defensible.** Among the papers we read, we found none that:

1. **exposes the evidence basis and strength of each resolution to the agent and gates enforcement on that strength,** so that an ordering inferred from record dates or an unreferenced correction is advised rather than enforced, while an explicit referenced correction is enforced. The enforcing systems we read apply their gates uniformly over the structure they build at write time;
2. **measures, on the same small open-weight models, what happens to the answer when the reliability structure is wrong.** We measure both the harm of following wrong labels and the harm of enforcing them; the systems we read decide over a write-time structure and do not report the answer-level cost of errors in that structure;
3. **compares a deterministic arbiter and an LLM arbiter under an identical downstream policy** on agents of 3B–14B, so that arbitration quality and policy are separated.

Whether these design choices are *useful* is the empirical question of this paper, and the answer is a qualified yes: the gated mechanism beat all four comparators on sealed confirmatory data, with most of the gain coming from the evidence-basis labels rather than from enforcement, and with ungated enforcement of the same labels scoring higher still at more than twice the harm (Sections 7 and 9). The novelty statement is narrow. The temporal rules themselves are standard. What we contribute is the measurement of label-induced and enforcement-induced harm on small agents, and a preregistered test of whether basis-gated enforcement reduces that harm without losing the benefit of enforcement. Because the literature search was limited to arXiv and stopped on 14 November 2026, and because most papers were read at abstract level only, the statement "we found none" should be read as "in the work we examined". A broader search of non-arXiv venues and of later work is listed as an open item before submission (Section 13).


# 3. Method: evidence-basis arbitration (Evarb-0.2)

> Draft, 18 November 2026. Sources: `PHASE2/SYSTEM_ARCHITECTURE.md`, `PHASE2/EVIDENCE_ARBITRATION_SPEC.md`, `PHASE2/FREEZE_evarb.json`, the frozen code in `PHASE2/evarb/` (where the specification and code disagree, the code is normative), and the Phase 1 prototypes `PHASE1/prototype/rcs.py` and `tea.py`. No result is reported in this section.

## 3.1 Overview

The system has three parts (Figure 3.1):

1. a frozen tool-use **harness** (memlab) that provides the memory store, the tools, the prompts and the scorer;
2. an **arbiter** that turns each group of records about the same entity and attribute into a resolution with an evidence basis and a strength;
3. a **policy** at the terminal action that may send one reversible notice, enforcing only resolutions whose strength permits it.

The arbiter is either Evarb-0.2 (deterministic) or an LLM arbiter with the same output schema. The policy is the same in both cases.

```
user question ─▶ agent loop (≤ 6 model steps, +1 when a notice is possible)
                 ├─ memory_search ─▶ MemoryStore.search (hashed bag-of-words, top 4)
                 │                  └─ same-(entity, attribute) records ─▶ ARBITER ─▶ labels in the tool result
                 ├─ registry_lookup, calculator
                 └─ submit_answer ─▶ POLICY.decide(question, resolutions, retrieved, calls)
                                      ENFORCE | REQUEST_EVIDENCE ─▶ one reversible notice
                                      ADVISE  | NO_ACTION        ─▶ submission stands
               ─▶ safe submission: unusable post-notice answer ⇒ pre-notice answer is final
               ─▶ frozen scorer
```
**Figure 3.1.** Where the mechanism sits (adapted from `SYSTEM_ARCHITECTURE.md` §1).

## 3.2 Harness (memlab)

All configurations run in the same frozen harness (`memlab.py`, sha256 `dc28584c…`; `FREEZE_evarb.json`, `frozen_dependencies`). The harness is never edited; its hash is checked at the start of every run.

**Task.** A task is a natural-language question about one attribute of one fictional entity (for example a project's approved budget, staging port, team size, lead, cloud region, or a date), together with a memory store, a tool registry, and an expected behaviour. The expected behaviour is one of three kinds: `answer` with a gold value (and, where relevant, a stale value), `conflict` (the evidence does not determine a value), or `abstain` (the memory contains no supporting record). Every memory store also contains distractor records about other entities.

**Tools.** The agent has four tools: `memory_search` (a query string; returns up to four records above a similarity threshold of 0.2 from a hashed bag-of-words store), `registry_lookup` (entity and attribute; may fail transiently or permanently by design), `calculator`, and `submit_answer`. A submission is a JSON object with `status` ∈ {`answer`, `conflict`, `abstain`}, a `value` for answers, and cited evidence.

**Agent loop.** The loop allows at most six model steps, plus one extra step in configurations whose policy can issue a notice. It uses the harness-v2 prompts, which include a one-time repair notice when the model's final message cannot be parsed and a notice after malformed tool calls. The Phase 2 loop (`evarb/loop.py`) is the Phase 1 loop with three hooks: labels from a resolver in the memory tool result, the policy at the terminal action, and reversible notices. Phase 1 configurations (B, G, R, T, RT) are dispatched to the unchanged Phase 1 code.

**Scoring.** The frozen scorer classifies the final submission as `correct`, `over_abstain`, `false_conflict`, `wrong_value`, `stale_value`, `unsupported_claim`, `arbitrary_pick`, `format_error` or `max_steps` (step budget exhausted). Task success is `correct`. An outcome is **harmful** if it is `wrong_value`, `stale_value`, `unsupported_claim` or `arbitrary_pick` (an answer on a task whose gold is `conflict`). Over-abstention, false conflict, format errors and step-limit hits are failures but not harmful answers. The outcome is computed from the expected behaviour and the final submission only.

## 3.3 Arbitration

### 3.3.1 Input and output

The arbiter receives the records of one (entity, attribute) group. Each record has an identifier, a value, a text, a source and a `recorded_on` date (possibly missing). It returns a resolution with a kind (`unchallenged`, `resolved`, `contradiction` or `unresolved`), an evidence basis, a strength (`strong`, `moderate` or `none`), the current value if any, and a per-record status (`current`, `superseded`, `contradictory`, `unresolved` or `unchallenged`).

### 3.3.2 Clause-level cues

Each record text is split into clauses at sentence ends, semicolons and dashes. Within a clause, Evarb looks for cues of seven kinds: correction (e.g. "corrected", "erratum", "was a mistake", "amended"), supersession ("replaces", "supersedes", "instead of", "no longer", "revised", "overrides"), dismissal ("disregard", "withdrawn", "retracted", "obsolete"), retention ("remains valid", "still stands", "unchanged"), unconfirmed ("not yet confirmed", "pending", "proposed", "draft", "under review"), contradiction ("both … stand", "until reconciled", "discrepancy", "disagree") and a hypothetical value. Each cue is qualified by its scope in the clause:

- **negated**, if a negator occurs among the four tokens before the cue;
- **quoted**, if the cue is in quotation marks or the clause contains a reporting verb ("said", "claimed", "according to", …);
- **hypothetical**, if the clause contains a conditional or modal marker ("if", "would", "might", "unless", …).

A clause **refers to a rival record** if it mentions the rival's value (token-bounded, numbers compared numerically) or uses an anaphor for an earlier value ("the earlier figure") when exactly one rival value exists. Validity dates are read after "as of", "effective", "valid from", "since", "starting from" and similar phrases (ISO, "3 March 2026", "March 3, 2026" and ordinal forms); a date equal to the record's own value is never treated as a validity date.

### 3.3.3 Evidence bases and strength

Every resolution carries one of ten evidence bases (Table 3.1). Strength is a function of the basis and its conditions.

**Table 3.1.** Evidence bases (`EVIDENCE_ARBITRATION_SPEC.md` §3).

| Basis | When it applies | Strength |
|---|---|---|
| `explicit_correction` | asserted correction or dismissal referring to the rival, at different dates | strong (moderate if the correcting record is older) |
| `explicit_supersession` | asserted replacement or revision referring to the rival, at different dates | strong (same caveat) |
| `same_day_correction` | asserted correction, dismissal or supersession between same-date records, referring to the rival | strong |
| | unreferenced correction or dismissal, used only to break a same-time tie | moderate |
| `valid_time` | every established record states a validity date; the latest is unique | strong |
| `record_time` | unique latest `recorded_on` | strong; moderate if the winner's text signals doubt ("proposed", "planned", "likely", …) |
| `source_authority` | same-time tie in which exactly one value comes from an authoritative source | moderate |
| `genuine_contradiction` | same time, different values, no ordering evidence | strong if no cue of any kind, else moderate |
| `negated_correction` | negated correction with an asserted "both stand / disagree" marker → contradiction | strong |
| | negated replacement without such a marker, retention of the rival, or the record's own change unconfirmed → that record is set aside, the rival is current | moderate |
| `quoted_or_hypothetical` | only ordering cue is reported speech → unresolved | none |
| | the record's change or value is hypothetical → record set aside, rival current | moderate |
| `insufficient_evidence` | missing dates without text dates; cyclic or inconsistent cues | none |

### 3.3.4 Precedence

The arbiter applies the following steps in order (`arbiter.arbitrate`):

1. One distinct value: `unchallenged`.
2. **Set aside records that do not establish their own value**: values that are unconfirmed or proposed, hypothetical changes, records stating that the rival remains valid, records saying they do not replace the rival (when no record says both stand), and records whose own value appears only in reported, conditional or negated clauses. If the remaining records share one value, it is current (moderate).
3. Negated pairs or an asserted contradiction marker: `contradiction`.
4. Asserted, referenced textual edges ("r supersedes q"): if they determine a unique winner, it is current with that basis; if they are inconsistent, `unresolved`.
5. Validity dates on every established record: order by them.
6. Otherwise, `recorded_on` on every established record: order by it, with the doubt guard.
7. A tie at the top of step 5 or 6 is broken by, in order: an unreferenced correction claimed by exactly one value (moderate); a reported or hypothetical cue among the tied records (`unresolved`); exactly one authoritative source (moderate); otherwise `contradiction`.
8. Missing dates with no text dates: `unresolved`.

The words "update" and "revised" never break a tie on their own, because they are often incidental ("Weekly status update: …").

Step 2 encodes the benchmark's v2 semantics: **a record that does not establish its own value leaves the established value standing.** These semantics were adopted after a blind annotation of the first validation split showed that the earlier (v1) gold for negated and reported claims was inconsistent (`FREEZE_evarb.json`, `history`).

### 3.3.5 Labels shown to the agent

Labels are added to each retrieved record in the `memory_search` result, with a status, the evidence basis in words, a certainty (`established`, `likely`, `not established`, mapped from strength), and where relevant `superseded_by`, `conflicts_with`, `valid_from` and a note. A superseded record is shown as `historical` when the question asks about an earlier time, since whether a record is historical depends on the question, not on the records. An order the evidence cannot establish is shown as `unresolved` with the instruction to read the record texts. It is never shown as "conflicting", because in the Phase 1 pilot small models followed wrong cautionary labels (Section 1.2).

## 3.4 Basis-gated policy

**Question intent.** A question is *historical* if it contains phrases such as "before the change", "previously", "originally", "used to", "prior to", or a date after "as of / on / at"; otherwise it is *current*.

**Rules.** The policy is evaluated when the agent submits. It applies only to *anchored* groups: groups the agent retrieved whose entity is named in the question. The first matching rule wins (Table 3.2). The policy never sees the gold answer, and model identity is not an input.

**Table 3.2.** Policy rules (`policy.decide`).

| Rule | Condition | Action |
|---|---|---|
| P3 (search-before-submit) | no `memory_search` and no successful registry result | REQUEST_EVIDENCE: search memory; if nothing relevant, the previous submission stands |
| P1 | current question; answer equals a superseded value and not the current one | ENFORCE if enforceable, else ADVISE |
| P2 | current question; status `conflict`; every anchored multi-value group is resolved | ENFORCE if all are enforceable, else ADVISE |
| P4 | answer equals a value of a contradictory group, and no registry result | ENFORCE toward `conflict` if enforceable, else ADVISE |
| — | anything else, including every unresolved group | NO_ACTION |

**Gating.** A resolution is *enforceable* in mode `gated` if its strength is strong; in mode `all` if it is strong or moderate; in mode `none`, never. ENFORCE and REQUEST_EVIDENCE send a notice; ADVISE and NO_ACTION let the submission stand (the advisory information is already in the labels).

**Notices.** A run receives at most one notice. The notice names the records involved and states the evidence basis truthfully (for example, a same-date correction is described as a correction, not as an ordering by date). The agent may resubmit. The policy never changes an answer itself.

**Safe submission.** If the submission after a notice is unparsable or missing, or the step budget runs out, the final answer reverts to the pre-notice submission. This bounds the cost of a notice: a notice can change a parsable answer into another parsable answer, but cannot turn a parsable answer into a format failure or a step-limit failure.

## 3.5 LLM arbiter baseline

The LLM arbiter (`llm_arbiter.py`) fills the same output schema. Its prompt states the same evidence rules in plain language; the model returns a status and basis for every record; strength is derived from the basis with the table above. Unparsable or inconsistent output (for example two different current values) becomes `unresolved` and is counted as a format failure. In Phase 3 the arbiter is the same model as the agent. The LLM arbiter's calls are logged and counted separately from the agent's.

## 3.6 Baselines from Phase 1

- **Legacy labels (G, R).** Metadata-only reliability labels that order records by `recorded_on` alone; same-date records with different values are labelled conflicting.
- **TEA (T, RT).** The Phase 1 temporal evidence arbiter: it orders by text validity dates where every competing record has one, otherwise by a unique latest `recorded_on`, and breaks ties by a correction cue that names the rival's value; otherwise it reports no ordering evidence. It has no negation, quotation or modality scope, and its labels carry no strength. TEA replaces only the status function of the legacy gate.
- **RCS enforcement (R, RT).** At submission, three rules each trigger one corrective notice: R1 (answer equals a superseded value and no current value), R2 (status `conflict` while no anchored key is in a same-date conflict) and R3 (no `memory_search` and no successful registry result). RCS enforces every label regardless of how it was derived, and has no safe submission.

## 3.7 Configurations

All twelve configurations are run in every cell (`SYSTEM_ARCHITECTURE.md` §4; `PREREGISTRATION.md` §4).

**Table 3.3.** Configurations.

| Config | Labels shown | Enforcement | Search-before-submit | Safe submission | Role |
|---|---|---|---|---|---|
| B | none (memory only) | — | — | — | no-label baseline |
| G | legacy (`recorded_on` only) | — | — | — | Phase 1 advisory baseline |
| R | legacy | RCS R1/R2, every label | R3 | no | Phase 1 enforcement |
| T | TEA | — | — | — | advisory temporal arbiter |
| RT | TEA | RCS, every label | R3 | no | **primary comparator**: enforced lexical temporal arbiter |
| EB | Evarb | — | — | — | evidence-basis labels, advisory |
| **EBG** | **Evarb** | **gated (strong only)** | **P3** | **yes** | **proposed** |
| EBG-all | Evarb | strong and moderate | P3 | yes | ablation: gating |
| EBG-unsafe | Evarb | gated | P3 | **no** | ablation: safe submission |
| EBG-noR3 | Evarb | gated | **no** | yes | ablation: search-before-submit |
| LA | LLM arbiter (agent's model) | — | — | — | LLM-arbiter baseline, advisory |
| LG | LLM arbiter (agent's model) | gated | P3 | yes | LLM-arbiter baseline under the EBG policy |

The contrasts are constructed so that each pair differs in one design element where possible: EBG vs EB (enforcement), EBG vs EBG-all (gating), EBG vs EBG-unsafe (safe submission), EBG vs EBG-noR3 (search-before-submit), EBG vs LG (who arbitrates), EB vs T and EBG vs RT (arbiter and policy together). The primary contrast, EBG − RT, compares the proposed configuration with the strongest Phase 1 enforcing configuration. It therefore changes the arbiter, the gating, the notice wording and safe submission together, and cannot attribute an effect to any one of them; the exploratory ablations address attribution.

## 3.8 Freeze and verification

Evarb-0.2 was frozen on 14 November 2026 at 08:14:16 UTC (`FREEZE_evarb.json`): nine mechanism files, the runner `run_p2.py`, the analysis script `analyze_p2.py` and the component evaluator, with three frozen dependencies (memlab, RCS, TEA). Hashes are of file content with CRLF normalised to LF; the freeze record lists 82 passing tests at the time of freezing. The development history before the freeze is recorded there: evarb-0.1 was tuned on the development fixtures, looked at once on the first validation split (p2val), and revised to 0.2 after a blind annotation showed the v1 semantics for negated and reported claims to be inconsistent. From that point p2val is development data. Behaviour of the frozen version, including its known failures (Section 13), is pinned by unit tests, among them `tests/test_known_limitations.py`. The model-family adapter for Llama models (`evarb/clients.py`) leaves the frozen model client unchanged.

Arbitration cost: Evarb is a deterministic function with no model calls. The LLM arbiter adds model calls per run; cost and latency per configuration are reported, not tested (Section 4.9).


# 4. Experimental design

> Draft, 18 November 2026. Source of record: `PHASE2/PREREGISTRATION.md` (frozen 17 November 2026). Supporting: `PHASE2/FREEZE_eval3.json`, `PHASE2/FREEZE_evarb.json`, `PHASE2/PHASE3_EXECUTION_PLAN.md`, `PHASE2/data/p2val2/PRIMARY_RULE_DECISION.md`, `PHASE3/LIMITATIONS.md`. Where this section paraphrases the preregistration, the preregistration is normative. No eval3 outcome is reported here.

## 4.1 Preregistration and freeze

The confirmatory evaluation was preregistered and frozen on **17 November 2026**, before the first Phase 3 submission and before any eval3 outcome existed. The freeze consists of:

| Item | Frozen as | Record |
|---|---|---|
| Mechanism | Evarb-0.2; 12 files and 3 frozen dependencies; frozen 2026-11-14T08:14:16Z | `FREEZE_evarb.json`; its LF-normalised sha256 `5ae8ebe3c2b110bd89348e113c3b0b7803efb6ec0020275a0dd1ab75fc2b7ad8` is recorded in the eval3 provenance (`FREEZE_eval3.json`, `provenance.freeze_evarb_sha256`) |
| Harness, prompts, scorer | `memlab.py`, sha256 `dc28584c518d18b6b2b6f684be77269f9ca00d502939ecf845985635d93b62df` | `FREEZE_evarb.json` |
| Runner and analysis | `scripts/run_p2.py` (`6be2011c…`), `scripts/analyze_p2.py` (`76fc67cc…`) | `FREEZE_evarb.json` |
| Evaluation data | eval3, built and sealed on the cluster by Slurm job 4200 (built 2026-11-16T10:46:42Z); 13 sealed files | `FREEZE_eval3.json` (`sealed_files`, `sha256sums_file_sha256` `c069d70f…`), written 2026-11-17T08:57:24Z |
| Preregistration | `PREREGISTRATION.md`, sha256 `221013b3cee87c003894ba1837e8a62b586e7acf02c22f0c6fbb59c34a6218d1` | `FREEZE_eval3.json` (`preregistration_sha256`) |

The preregistration states that nothing in it may be changed after the freeze in response to eval3 results, and that any later change is a documented protocol amendment. Any later modification of Evarb is a new development version (evarb-0.3 or later) and is not covered.

**Integrity gates.** At the start of every cell, the runner verifies the `FREEZE_evarb.json` hashes, checks the sealed eval3 files against their sha256 sums, and refuses a task file whose hash differs from the frozen one (`run_p2.py --expect-sha`) (`PHASE3_EXECUTION_PLAN.md` §3). The preregistration's own hash is checked inside each job (`PHASE3/LIMITATIONS.md`, execution notes).

## 4.2 Hypotheses

**Table 4.1.** Preregistered hypotheses (`PREREGISTRATION.md` §2).

| # | Hypothesis | Status in the analysis | Falsified if |
|---|---|---|---|
| **H-primary** | EBG − RT > 0 in task success on eval3 primary items, pooled over the primary models and decodings | confirmatory, Holm family | Holm-adjusted p ≥ 0.05, or the 95% CI lies at or below 0 (the latter reported as evidence against) |
| S1 | EBG − T > 0 (enforcement on Evarb vs advice on TEA) | confirmatory, Holm family | as above |
| S2 | EBG − LG > 0 (deterministic vs LLM arbiter under the same gated policy) | confirmatory, Holm family | as above |
| S3 | EBG − B > 0 (vs no labels) | confirmatory, Holm family | as above |
| S4 (harm) | harmful-answer rate EBG ≤ RT; and arbitrary-pick rate on genuine conflicts EBG ≤ RT | reported with CIs, one-sided interpretation | EBG's harmful rate exceeds RT's with a 95% CI excluding 0 |
| E1–E5 | EB − T; EBG − EB (enforcement); EBG − EBG-all (gating); EBG − EBG-unsafe (safe submission); EBG − EBG-noR3 (search-before-submit); per-model and per-category effects; LG − LA | exploratory, Benjamini–Hochberg within the exploratory set | not confirmatory; no claim rests on them |

The harmful outcomes are `wrong_value`, `stale_value`, `unsupported_claim` and `arbitrary_pick` (Section 3.2). The preregistration also lists outcomes that would falsify the contribution (§13): EBG − RT ≤ 0 (CI); EBG − LG ≤ 0; EBG harmful rate > RT harmful rate. All are to be reported whatever their sign.

## 4.3 Models

**Table 4.2.** Models and decodings (`PREREGISTRATION.md` §4).

| Role | Model | Decodings | Notes |
|---|---|---|---|
| primary | Qwen2.5-3B-Instruct [@qwen2024qwen25] | greedy; T = 0.7 with seeds 1, 2, 3 | |
| primary | Qwen2.5-7B-Instruct | greedy + 3 seeds | |
| primary | Qwen3-8B [@yang2025qwen3] | greedy + 3 seeds | thinking disabled; added 16 Nov 2026, before any eval3 run |
| primary (second family) | Llama-3.1-8B-Instruct [@grattafiori2024llama3] (snapshot `0e9e39f2…`) | greedy + 3 seeds | run through the `evarb.clients.FamilyClient` adapter |
| secondary | Qwen2.5-14B-Instruct (snapshot `cf98f3b3…`) | greedy only | reported separately; also the eval3 writer and one annotator |
| format-limited | Llama-3.2-3B-Instruct | greedy only | reported separately, never pooled; failed the 95% format-readiness criterion (`MODEL_FAMILY_READINESS.md`) |

All models run in bf16 on one NVIDIA L40, from a local Hugging Face cache in offline mode (`HF_HUB_OFFLINE=1`), with `max_new_tokens` and chat-template settings recorded in the run manifests. The base seed for greedy runs is 20261111.

## 4.4 Cells and run matrix

A **cell** is one model under one decoding. The design has **18 cells**: four primary models × four decodings (16 cells), plus Qwen2.5-14B greedy and Llama-3.2-3B greedy. Every cell runs all 268 valid eval3 tasks under all 12 configurations of Table 3.3, i.e. 3,216 (task, configuration) runs per cell and 57,888 runs in total (derived arithmetic; the execution plan states the bound ≤ 276 tasks × 12 configurations per cell).

Primary cells are scheduled before the secondary ones, so that a confirmatory analysis is possible on complete primary cells if the campaign is stopped (`PHASE3_EXECUTION_PLAN.md` §3). (The execution plan, dated 16 November, lists 14 cells with 12 primary ones because it predates the addition of Qwen3-8B; the preregistration's four primary models give 16 primary cells and 18 cells in all.)

## 4.5 Unit of analysis, item set and clustering

- **Unit:** the task. For each model, task success is the mean over that model's decodings; contrasts are paired within model and decoding (`PREREGISTRATION.md` §8).
- **Item set:** the primary item set is every mechanically valid eval3 item (268 tasks; Section 4.8). It is written with `scripts/subset_tasks.py`, which prints counts and a hash only, and passed to `analyze_p2.py --tasks`.
- **Clustering:** a family is a (category, attribute) pair. eval3 has 135 families among its valid tasks (Section 5).

## 4.6 Test, confidence intervals and multiplicity

- **Test:** two-sided sign-flip permutation test of family-level summed differences. Families are pooled across models, and a family's sign is flipped for all models together. 100,000 seeded Monte Carlo permutations.
- **Confidence interval:** 95% percentile bootstrap over families of the mean task-level difference, 10,000 seeded resamples.
- **Multiplicity:** Holm correction over the four confirmatory contrasts {EBG − RT, EBG − T, EBG − LG, EBG − B}, pooled over the primary models, at α = 0.05. All other contrasts are exploratory and controlled with Benjamini–Hochberg [@holm1979simple; @benjamini1995fdr]. The sign-flip permutation test follows the standard randomisation argument for paired differences [@good2005permutation], applied at the family level; the percentile bootstrap [@efron1979bootstrap] resamples whole families, as in cluster bootstrapping [@field2007clustered].
- **Reported without tests counted toward the claims:** per-model and per-category results, harmful-answer rates, and the secondary and format-limited models, for every contrast.

The analysis was verified before any real agent run with a dry run of three simulated agents on p2val (77 tasks × 12 configurations × 3), which checked that all 12 configurations run, that deleted rows are scored as missing failures with complete denominators, that pairing and family pooling behave as specified, and that only the four Holm-family pooled rows are marked confirmatory (`PREREGISTRATION.md` §14). The dry-run numbers are meaningless and are not reported.

## 4.7 Exclusions, missing runs and stopping rules

**Run-level exclusions.** None. Unparsable outputs, harness errors and step-limit hits are failures (`PREREGISTRATION.md` §6).

**Missing runs** (§7). A (task, configuration) pair with no row, or with a harness error, is scored as a failure (`outcome = missing`) and counted separately. A cell with more than 5% missing pairs is re-submitted once; the runner resumes and skips finished pairs. Missing pairs that remain after that are failures. A whole cell that cannot run is reported as missing; the primary test is then run on the cells that exist, and this is stated.

**Stopping** (§10). The campaign runs to completion of all 18 cells. There is no interim efficacy look. The only grounds for stopping early are integrity failures: a freeze mismatch, a seal mismatch, or a runner defect. A defect fix restarts the affected cells from scratch and is reported. If the primary cells finish but the secondary ones cannot, the confirmatory analysis is run on the primary cells and the rest is reported as not run.

**Cost and latency** (§11) are reported per configuration and not tested: model calls per run, LLM-arbiter calls per run, wall-clock latency and tokens.

## 4.8 The primary item set: a documented change and a wording inconsistency

**The change.** An earlier draft of the design defined the primary item set as the items on which both blind annotators agreed with the gold label at non-low confidence. On 16 November 2026 at 10:14 UTC this was changed to **all mechanically valid items** (`data/p2val2/PRIMARY_RULE_DECISION.md`; `PREREGISTRATION.md` §5). The decision was taken after the p2val2 annotations were available and before any mechanism, baseline or LLM-arbiter output on p2val2 was opened, and before any eval3 output existed. Only annotator-versus-gold agreement per category was examined. On the 90 valid p2val2 items, the double-agreement rule kept 51 items and left six categories with no primary item, because the small blind annotators failed the temporal-reasoning categories the benchmark is designed to test (for example, 0 of 4 for Llama-3.1-8B on `update_record_time`, `valid_time_same_import`, `three_value_chain`, `hypothetical_change` and `quoted_claim`). The preregistration argues that restricting the confirmatory set to items small models already agree on would bias it toward easy items and remove the categories under test. The double-agreement set (`eval3_PRIMARY_IDS.json`, hash in `FREEZE_eval3.json`) and the set on which the Qwen2.5-14B annotator agrees with gold are retained as **secondary sensitivity sets**, reported but not tested for the claims.

**The inconsistency.** The frozen preregistration is internally inconsistent on this point. §5 states that the primary item set is every mechanically valid eval3 item. §6 ("Exclusions") still contains the earlier rule: "Flagged items (annotator disagreement or low confidence) are excluded from the primary analysis and reported in a secondary analysis." §8 likewise refers to "the flagged complement" being analysed separately. The §6 and §8 wording was not updated when §5 was revised. **The analysis follows §5 and `PRIMARY_RULE_DECISION.md`**: the primary set is all 268 valid items, and the flagged and double-agreement subsets are sensitivity analyses. We report this as a defect in the frozen document rather than correct it silently. The sensitivity results on the double-agreement subset are reported alongside the primary results so that a reader who prefers the §6 reading can apply it: on the 161-item double-agreement subset the four contrasts are +14.3, +12.7, +19.7 and +14.7 pp, all with intervals above zero and Holm-adjusted p < 0.05, against +17.1, +14.5, +15.9 and +15.3 pp on the primary set (Section 8.2). The conclusions do not depend on which reading is taken.

## 4.9 Power

Power was computed on 17 November 2026 (`scripts/power_phase3.py`; `PREREGISTRATION.md` §9) from the measured p2val2 agent-level greedy runs (90 tasks; Qwen2.5-3B, Qwen2.5-7B, Llama-3.1-8B, Qwen3-8B). Paired task differences per contrast were resampled with a stratified bootstrap to eval3's structure of 135 families × 2 items × 4 models, and tested with the sign-flip test at the strictest Holm level (0.0125), with 2,000 simulations.

**Table 4.3.** Power at the effect measured on the development split and at half that effect (`PREREGISTRATION.md` §9). The measured differences are development estimates used only for planning.

| Contrast | p2val2 difference (pp), development | Power at measured / at half |
|---|---|---|
| EBG − RT (H-primary) | +15.8 | 1.00 / 0.961 |
| EBG − T | +12.5 | 1.00 / 0.883 |
| EBG − LG | +13.1 | 1.00 / 0.528 |
| EBG − B | +18.6 | 1.00 / 0.996 |

The preregistered seed rule (power at half the measured effect ≥ 0.8 for H-primary) was met, so the number of sampled seeds stayed at three. EBG − LG is under-powered at half the development effect (0.53); this is stated, not corrected. The simulation treats the p2val2 effect as the truth. p2val2 has 90 single-item families, whereas eval3 has two items per family, so the estimate may not transfer.

## 4.10 Development observations disclosed before the freeze

The preregistration (§15) records what was known from development data at the freeze, so that readers can judge whether the hypotheses were shaped by it. On p2val2 (agent level, greedy, 90 items, four models), the pooled EBG − RT difference was +15.8 pp, but heterogeneous across models (+10.0, +24.4, +27.8 and +1.1 pp for Qwen2.5-3B, Qwen2.5-7B, Qwen3-8B and Llama-3.1-8B). Ungated enforcement (EBG-all) scored higher than gated EBG (243 vs 218 of 360) with more harmful answers (29 vs 14). Llama-3.1-8B showed no EBG benefit over RT, with 9 format failures and heavy abstention in every configuration. These observations did not change the hypotheses. The preregistration states that, if the Llama-3.1-8B result repeats on eval3, it will be reported as a failure to generalise across families, and that the ungated variant remains an exploratory contrast (E3) rather than the primary configuration.

The p2val2 item audit was performed by the mechanism's maintainer. File timestamps place it before every p2val2 mechanism and LLM-arbiter output, but the hash record was written after all outputs existed; it is a documented quality check, not an independent or blind audit (`PREREGISTRATION.md` §16).

## 4.11 Execution

Phase 3 started as Slurm array job 4233 (repository commit `d82155c`). Deviations from the planned execution that were recorded before any eval3 outcome was analysed are listed in Section 13.6. **Results.** All 18 cells completed: 3216 rows each, 57,888 in all, with 0 missing pairs, 0 duplicates and 0 harness-error rows, and every cell's last Slurm segment exited cleanly. Nine cells ran as the original array, the remainder under a two-lane controller; two cells were interrupted by an unplanned node reboot on 2026-11-20 and resumed after the damaged tail of each output file was quarantined, without losing a completed run (Section 11 and `PHASE3/PHASE3_DEVIATIONS.md`).


# 5. Dataset

> Draft, 18 November 2026. Sources: `PHASE2/BENCHMARK_EVAL3_SPEC.md`, `PHASE2/FREEZE_eval3.json` (counts, agreement statistics, seal checks and hashes only; no content), `PHASE2/PREREGISTRATION.md` §5 and §12, the generator `PHASE2/benchmark/skeleton.py` (structure only), `PHASE2/BASELINE_COMPARISON.md` for the development splits. No eval3 item, label or outcome was read for this section.

## 5.1 Design principles

eval3 is the confirmatory evaluation set. It was designed so that the ground truth does not depend on the mechanism's author's reading of any text, and so that nobody connected to the mechanism sees its contents before Phase 3 scoring. Three principles follow.

1. **Gold before text.** A deterministic skeleton fixes every structural fact and the expected behaviour before any natural-language text exists.
2. **Writer and annotators blind to the mechanism and the gold.** Record texts are written by a model that sees only writing briefs; two other model runs annotate the texts without access to the gold.
3. **Built after the freeze, sealed, read by nobody.** The set was built in one cluster job after the mechanism was frozen, into a directory outside the source tree, and only counts, statistics and hashes were brought into the repository.

## 5.2 Construction

**Order** (`BENCHMARK_EVAL3_SPEC.md` §2), enforced by timestamps and hashes: (1) freeze the mechanism; (2) generate the skeleton; (3) write the texts; (4) annotate; (5) seal. Steps 2–5 ran in a single Slurm job (4200) that wrote only to the sealed directory on the cluster. The eval3 provenance record includes the hash of `FREEZE_evarb.json` that was in force when the set was built (`FREEZE_eval3.json`, `provenance`).

**Skeleton.** The generator (`benchmark/skeleton.py`, seed 20261201) produces, for each item, the entity, attribute, values, record dates and sources, the category, the expected behaviour (`answer:<value>`, `conflict` or `abstain`, plus a stale value where relevant) and, for every record, a *writing brief* stating what its text must convey. Each item has five distractor records about other entities. The skeleton has **23 categories × 12 items = 276 items**. Six attributes rotate across items, and a family is a (category, attribute) pair; by construction there are 138 families of two items each.

**Categories.** The 23 categories (skeleton v2) cover:

| Group | Categories | Expected behaviour |
|---|---|---|
| Record-time ordering | `update_record_time`, `three_value_chain`, `historical_question` | new / latest value; old value for the historical question |
| Validity-time ordering | `valid_time_same_import`, `backfilled_entry`, `as_of_question` | new value by validity date; old value for the as-of question |
| Explicit corrections | `same_day_correction_ref`, `same_day_correction_noref`, `supersession_later_ref` | corrected value |
| Negative and modal statements (v2 semantics: the established value stands) | `negated_replacement`, `retention`, `unconfirmed_change`, `hypothetical_change`, `quoted_claim` | old (established) value |
| Genuine conflicts | `conflict_plain`, `conflict_same_validity`, `conflict_rival_neutral`, `authority_both`, `missing_timestamp`, `incidental_change_word`, `negated_both_stand` | `conflict` |
| Controls | `single_record_control`, `unsupported` | the only value; `abstain` |

In total, 15 categories (180 items) have an answer, 7 categories (84 items) are genuine conflicts, and 1 category (12 items) requires abstention. One category was excluded on purpose: a tie broken only by source authority, because its gold depends on a convention the agent's prompt does not state. It remains in the development fixtures only.

**Semantics.** eval3 uses the v2 semantics adopted after the p2val annotation (Section 3.3.4): a record that only reports a claim, proposes, conditions, or says it does not replace the other value does not establish its value, so the established value stands. A conflict requires two asserted values with nothing ordering them, or an explicit statement that both stand.

**Names.** Entities come from the memlab name pool slice [14000:17600] and eval3 distractor entities from [17600:20000]. These slices are disjoint from those of every development and validation split (dev [150:1600] and [0:150], eval2 [1600:5200], p1dev [5200:8000], p1hold [8000:10400], p2dev [10400:12800], p2val [12800:14000] with distractors [20000:21200]; p2val2 [21200:22400] per the generator configuration).

**Texts.** Record texts and the wording of historical questions were written by **Qwen2.5-14B-Instruct** (greedy; seeded T = 0.7 retries), from the briefs only. The writer input contained no gold, date or source fields and no label words (checked; Section 5.4). The writer was required to keep each record's own value verbatim and to write date *values* in ISO form (`YYYY-MM-DD`), so that the mechanical validator would not reject correct long-form dates; validity dates that are not values may appear in any form. Questions about the current state use the memlab question templates shared with every split, and distractor texts use the memlab templates.

**Mechanical validation** (`benchmark/assemble.py`). Every text must name its entity and its own value, and the question must be present and must not contain the value. Items that fail are excluded before sealing, and only their ids are recorded. **268 of 276 items are valid; 8 were excluded.** According to `PHASE3/LIMITATIONS.md`, the 8 exclusions were values written as long-form dates. The 268 valid tasks fall into **135 families** (the 138 of the specification is the skeleton count before exclusion).

## 5.3 Blind annotation

Two annotators labelled every valid item from the text alone, following `benchmark/ANNOTATION_GUIDELINES.md`: **Llama-3.1-8B-Instruct** and **Qwen2.5-14B-Instruct** (a separate prompt and run from the writing run). Neither saw the mechanism or the gold. Agreement with the skeleton gold (`FREEZE_eval3.json`, `agreement`):

| Annotator | Exact agreement with gold | Cohen's κ (three classes) | Low confidence | Unparsed |
|---|---|---|---|---|
| Llama-3.1-8B-Instruct | 174 / 268 | 0.471 | 1 | 0 |
| Qwen2.5-14B-Instruct | 232 / 268 | 0.767 | 6 | 0 |

κ is Cohen's kappa [@cohen1960kappa] over the three gold classes.

Items on which both annotators agree with gold at non-low confidence form the double-agreement set (161 items); the remaining 107 are flagged. Under the frozen design these counts define a **secondary sensitivity set**, not the primary set (Section 4.8). Because the annotators are small models that, on the development split p2val2, failed several temporal-reasoning categories wholesale (`data/p2val2/PRIMARY_RULE_DECISION.md`), annotator disagreement is not evidence that an item's gold is wrong, and annotator agreement is not ground truth.

**There was no human validation of eval3** (`FREEZE_eval3.json`, `human_validation: "none"`). The writer, Qwen2.5-14B, is also the second annotator and a secondary evaluated model, so the two annotators are not equally independent of the texts; the Llama annotator is the stronger check.

## 5.4 Split boundaries, leakage and template overlap

Checks ran inside the sealed job (`seal_checks.py`) and report counts only (`FREEZE_eval3.json`, `seal_checks`; all hard checks passed):

| Check | Result |
|---|---|
| Name pool unique | yes |
| Entities from eval3's own slice | 276 / 276 |
| Distractors from eval3's distractor slice | 1,019 / 1,019 |
| Entities in any other split's slice | 0 |
| Duplicate entities within eval3 | 0 |
| Entity overlap with dev fixtures, regression fixtures, p2dev, p2val, p2val2 | 0 each |
| Gold or label leakage into the writer input | 0 |
| Gold, value or category fields in the annotator input | 0 |

Surface overlap is reported rather than prevented. The seal checks compare masked eval3 texts with all development texts, and report `n_gold_texts` = 552, `template_overlap_8gram` = 280, `exact_masked_duplicates` = 252 and `duplicate_texts_within` = 223 (field names as recorded; the exact denominators are defined in `seal_checks.py`). A static generator audit before any text existed (`data/GENERATOR_AUDIT.json`) found that 16 of eval3's 19 masked brief templates are shared with p2val2, by design: p2val2 is a small sample of the same generator distribution. The category semantics overlap with the development categories by design, since they are what is being tested. eval3 is therefore a set of synthetic, templated records with heavy surface regularity, not natural memory logs.

## 5.5 Sealing and access

The sealed files (skeleton, writer input, texts, groups, tasks, annotator input, both annotation files, agreement, primary ids, provenance, seal checks and manifest; 13 files) are read-only on the cluster, with a `SHA256SUMS` file whose own hash is recorded in `FREEZE_eval3.json`. The repository holds hashes, counts and agreement statistics only. The rule recorded with the freeze is that nobody connected to the mechanism reads eval3 contents before Phase 3 scoring. The skeleton generator is in the repository, so the *structure* of eval3 is reproducible; the *texts* exist only in the sealed directory. The Phase 3 runner refuses any task file whose hash differs from the frozen one.

## 5.6 Development and validation splits

None of the following is used in the confirmatory analysis (`PREREGISTRATION.md` §5). They are listed so that readers can see which data shaped the mechanism.

| Split | Size | Role | Tuned on? |
|---|---|---|---|
| Development fixtures (`dev_groups`, `regression_groups`) | 114 + 46 groups | component-level development | yes |
| `p2dev_tasks` | — | agent-level development | yes |
| Phase 1 p1dev | — | Phase 1 development | yes |
| Phase 1 p1hold | 48 tasks per configuration | held out in Phase 1, then lost held-out status | yes |
| eval2 (Campaign 2) | 96 tasks, 22 families | earlier exploratory evaluation; failure taxonomy | used for diagnosis |
| p2val | 77 valid items (v1 semantics) | first validation split; looked at once with evarb-0.1, which was then revised | development since the evarb-0.2 revision |
| p2val2 | 92 skeleton items, 90 valid (v2 semantics) | validation of the frozen evarb-0.2; built after the freeze | no |
| **eval3** | 276 skeleton items, **268 valid, 135 families** | **confirmatory** | **no** |

p2val2 was built after the mechanism freeze and never used for tuning, but its results were known before the preregistration was frozen and informed the power analysis and the primary-set decision (Section 4). It is development evidence in the sense used throughout this paper.

**Results.** eval3 behaved as a confirmatory set should: every one of the 268 items produced a complete row for all 12 configurations in all 18 cells, and the three item-set definitions — all 268 valid items, the 161 double-agreement items and the 107-item flagged complement — give the same four verdicts (Section 8.2). The effects are somewhat larger on the flagged complement (+21.3 pp on H-primary) than on the double-agreement subset (+14.3 pp), which is the opposite of what annotator noise inflating the effect would predict.


# 6. Implementation

This section describes what was built and how it was run, so that the numbers in Sections 7–10 can be traced to code
and to specific jobs. Nothing here is an experimental result.

## 6.1 Components

| Component | File(s) | Role |
|---|---|---|
| Agent harness | `memlab.py` | the agent loop, tool schemas, tool executors, the scorer |
| Arbiter and policy | `evarb/` (9 modules, version 0.2) | cue detection, evidence-basis assessment, arbitration, the basis-gated enforcement policy, notice rendering |
| Phase 1 comparison mechanisms | `rcs.py`, `tea.py` | the record-conflict scanner (configurations R, RT) and the temporal-expression annotator (T, RT) |
| LLM arbiter | `evarb/llm_arbiter.py` | the model-based arbiter baseline (LA, LG), driven by the same client as the agent |
| Model client | `hf_client.py`, `evarb/clients.py` | a local Hugging Face causal-LM client with a Hermes-style tool template, wrapped per model family by `FamilyClient` |
| Parser | `agentrun_v2.parser` | tool-call extraction from raw generations, with a client-side fallback path |
| Runner | `scripts/run_p2.py` | one cell = one model × one decoding × 268 tasks × 12 configurations; resumable; writes the manifest |
| Analysis | `scripts/analyze_p2.py` | the preregistered statistics |
| Integrity gates | `PHASE3/scripts/finalize_gates.py`, `verify_phase3.py` | G1–G4 (Section 6.5) |
| Platform report | `PHASE3/scripts/platform_continuity.py` | the reporting-only G5 check (Section 11) |
| Cross-check | `PHASE3/scripts/crosscheck_phase3.py` | an independent re-computation of the headline numbers |
| Reports | `PHASE3/scripts/build_reports.py`, `write_results_section.py` | tables, CSVs and the numeric results draft; adds no statistics |

The 14 files that can affect what an agent does — the nine `evarb` modules, `rcs.py`, `tea.py`, `memlab.py`,
`hf_client.py` and `run_p2.py` — are hashed into **every** manifest line at **every** job start. The hash map is
identical across all 20 starts of the campaign.

## 6.2 Model execution

Models run locally through Hugging Face Transformers 5.22.2 on PyTorch 2.15.0 (CUDA runtime 13.2), in bfloat16, on
one NVIDIA L40, loaded from a pinned local snapshot directory with `device_map={"": 0}`. Generation uses at most 700
new tokens per call. Greedy cells set `do_sample=False`; sampled cells set `do_sample=True`, `temperature=0.7`,
`top_p=0.9`, with `torch.manual_seed(seed)` called once when the client is constructed. Chat templates are applied
with thinking disabled where the model supports it. Tool calls are parsed from the raw generation by AGENTRUN's own
parser, and the raw text, the parser version and the parse path are all logged, so a parse failure is visible as
such rather than silently scored as a wrong answer.

## 6.3 Orchestration

Each cell is a Slurm job requesting one GPU. A controller job (`phase3_controller_v2.sbatch`) keeps at most two
cells in flight — one per L40 — resubmits a cell that stops short, and exits only when all 18 cells have written a
`DONE` marker. It writes an append-only event log and a status file, and on completion a SHA-256 manifest of every
raw file. The finalization job (`phase3_finalize.sbatch`) is CPU-only and runs the gates, the staging, the platform
report, the verification, the analysis, the cross-check, the report generation, the numeric results draft and a
SHA-256 seal, stopping at the first failure and recording the stage it stopped at. The campaign therefore needs no
interactive session: the laptop that submitted the first job plays no part in what follows.

## 6.4 Resume semantics

The runner iterates tasks in sorted `task_id` order (outer loop) and the 12 frozen configurations (inner loop),
appending one JSON row per `(task, config)` pair and flushing after each. On restart it reads the rows already
present and skips those pairs. A cell therefore survives an interruption without re-executing completed work, and a
resumed segment is always a contiguous suffix in task order carrying all 12 configurations for each whole task it
contains. Section 11 explains why that property matters for this campaign, and what it does not cover.

## 6.5 Integrity gates

Every job refuses to start unless the `evarb-0.2` files match `FREEZE_evarb.json`, the sealed eval3 directory passes
`sha256sum -c`, and the preregistration's SHA-256 equals the value recorded at the freeze. All 20 starts printed
`freeze evarb-0.2 mismatches []` and the sealed preregistration hash `221013b3cee87c00`.

Before any analysis, four gates must pass:

- **G1** all 18 preregistered cells have a `DONE` marker;
- **G2** every cell holds exactly 268 × 12 = 3216 unique `(task, config)` pairs, with no duplicate and no unparsable
  line;
- **G3** the last Slurm segment of every cell exited 0;
- **G4** every manifest line of a cell agrees on temperature, seed, split hash, code hashes, configurations and on
  every field of the client's **identity**.

G4's client policy (version `g4-v2`) partitions the client metadata. Eighteen fields — backend, family, family
adapter, model, model path, PEFT adapter and its hash, temperature, seed, decoding, maximum new tokens, dtype,
thinking mode, parser version, torch, transformers, CUDA runtime and GPU model — must be present in every start and
equal across starts; a difference or an absence fails the gate and prints the field path and the values. Exactly one
field, `gpu_mem_gib`, is declared *observational*: it is the device's total memory as reported by the driver, it is
recorded in the manifest and nowhere else, and it is excluded from the identity comparison only — its per-start
values are retained and reported. Any client key in neither set fails the gate until it is explicitly classified.
The policy is shared by both validators so they cannot drift apart, and the previous policy is preserved verbatim
alongside it. Section 11 explains why this distinction was needed.

## 6.6 Analysis implementation

`analyze_p2.py` scores each row with the frozen scorer, treats a missing pair or a harness error as a failure,
averages success within task over a model's decodings, forms paired contrasts within model and decoding, clusters by
family = (category, attribute), and runs a two-sided sign-flip permutation test on family-level summed differences
with 100,000 seeded Monte-Carlo draws, a 10,000-resample seeded family bootstrap for the confidence interval, and
Holm correction over the four primary contrasts. `crosscheck_phase3.py` recomputes the per-configuration counts and
the primary effect sizes by an independent route; the pipeline stops unless the two agree exactly. The report
generator reads only those outputs and computes no statistic of its own.


# 7. Confirmatory results

All numbers in this section come from the frozen analysis run inside the cluster finalization job (Slurm job 4359)
over the 18 completed cells. Every cell holds exactly 268 × 12 = 3216 rows: 57,888 rows in all, with no missing
pair, no duplicate and no harness error. The confirmatory analysis pools the four primary models over greedy
decoding and three T = 0.7 seeds — 51,456 scored runs on 268 tasks in 135 families. An independent re-computation of
the 60 model × configuration counts and the four primary effect sizes agrees with the frozen analysis exactly.

## 7.1 The four preregistered contrasts

| Hypothesis | Contrast | Difference (pp) | 95% CI | p | Holm-adjusted p | Preregistered verdict |
|---|---|---|---|---|---|---|
| H-primary | EBG − RT | **+17.1** | [12.2, 22.1] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S1 | EBG − T | **+14.5** | [10.5, 18.6] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S2 | EBG − LG | **+15.9** | [10.4, 21.2] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S3 | EBG − B | **+15.3** | [10.3, 20.5] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |

Differences are in percentage points of task success, paired within model and decoding, with 95% percentile
bootstrap confidence intervals over families and two-sided sign-flip permutation p-values on family-level summed
differences (100,000 draws; the floor of the Monte-Carlo estimate is 1 × 10⁻⁵). Holm correction is over these four
contrasts. All four confidence intervals lie above zero.

## 7.2 S4: harm

S4 asked whether EBG's harmful-answer rate is no higher than RT's. It is substantially lower: **3.1%** of EBG runs
were harmful (135 of 4288) against **22.6%** for RT (968 of 4288), a paired difference of **−19.4 pp**
(95% CI [−24.6, −14.6]). Arbitrary picks, the specific harm that motivated the mechanism, fall from 252 under RT to
13 under EBG. The preregistered verdict is **NOT FALSIFIED**: the confidence interval for the EBG − RT harmful
difference does not lie above zero, and EBG's arbitrary picks do not exceed RT's.

## 7.3 Success and harm by configuration

Pooled over the four primary models and four decodings (n = 4288 runs per configuration):

| Config | Success | Harmful | Arbitrary pick | Unnecessary abstention | Format error | Step limit | Missing |
|---|---|---|---|---|---|---|---|
| B (memory, no labels) | 1972 (46.0%) | 302 (7.0%) | 172 | 658 (15.3%) | 118 (2.8%) | 104 (2.4%) | 0 |
| G (metadata labels, advisory) | 1867 (43.5%) | 337 (7.9%) | 109 | 510 (11.9%) | 135 (3.1%) | 91 (2.1%) | 0 |
| R (record-conflict scanner) | 1931 (45.0%) | 689 (16.1%) | 153 | 330 (7.7%) | 227 (5.3%) | 79 (1.8%) | 0 |
| T (temporal annotator, advisory) | 2009 (46.9%) | 316 (7.4%) | 35 | 557 (13.0%) | 110 (2.6%) | 72 (1.7%) | 0 |
| RT (R + T, enforced) | 1897 (44.2%) | 968 (22.6%) | 252 | 415 (9.7%) | 234 (5.5%) | 77 (1.8%) | 0 |
| LA (LLM arbiter, advisory) | 2053 (47.9%) | 568 (13.2%) | 295 | 633 (14.8%) | 128 (3.0%) | 79 (1.8%) | 0 |
| LG (LLM arbiter, gated) | 1948 (45.4%) | 914 (21.3%) | 510 | 676 (15.8%) | 122 (2.8%) | 55 (1.3%) | 0 |
| EB (evidence-basis labels) | 2372 (55.3%) | 115 (2.7%) | 13 | 566 (13.2%) | 109 (2.5%) | 86 (2.0%) | 0 |
| **EBG (full mechanism)** | **2630 (61.3%)** | **135 (3.1%)** | **13** | 494 (11.5%) | 120 (2.8%) | 42 (1.0%) | 0 |
| EBG-all (ungated enforcement) | **3047 (71.1%)** | 294 (6.9%) | 166 | 545 (12.7%) | 121 (2.8%) | 44 (1.0%) | 0 |
| EBG-unsafe (no safe submission) | 2638 (61.5%) | 142 (3.3%) | 12 | 374 (8.7%) | 247 (5.8%) | 49 (1.1%) | 0 |
| EBG-noR3 (no search-before-submit) | 2573 (60.0%) | 145 (3.4%) | 14 | 604 (14.1%) | 104 (2.4%) | 42 (1.0%) | 0 |

Two features of this table matter as much as the preregistered contrasts, and neither favours a simple reading.

First, **the development finding replicates on sealed data**. Metadata-derived labels made agents *worse* than no
labels at all (G 43.5% against B 46.0%), and *enforcing* record-derived labels was worse still and far more harmful
(RT 44.2% success, 22.6% harmful, against B's 46.0% and 7.0%). Enforcement is not neutral: applied to labels the
evidence does not support, it tripled the harm rate relative to plain memory.

Second, **ungated enforcement of the same evidence-basis labels scored higher than EBG** — 71.1% against 61.3% —
while more than doubling the harmful rate, 6.9% against 3.1%, and restoring arbitrary picks from 13 to 166. Section 9
takes this apart. It is the central tension in our results and we do not resolve it in EBG's favour.

## 7.4 Per-model effects

Per-model differences are descriptive; the confirmatory claims rest on the pooled, family-clustered tests above.

| Contrast | Qwen2.5-3B | Qwen2.5-7B | Qwen3-8B | Llama-3.1-8B |
|---|---|---|---|---|
| EBG − RT, success (pp) | +10.0 [3.0, 17.1] | +26.6 [20.2, 33.1] | +25.0 [18.2, 32.1] | +6.8 [3.3, 10.5] |
| EBG − RT, harmful (pp) | −25.2 | −27.7 | −24.5 | −0.3 |
| EBG − T (pp) | +17.0 [11.4, 22.8] | +15.7 [9.7, 21.7] | +16.0 [9.4, 22.6] | +9.3 [5.8, 13.0] |
| EBG − LG (pp) | +12.2 [4.6, 19.9] | +23.2 [14.9, 31.4] | +11.8 [5.1, 18.8] | +16.3 [10.6, 22.3] |
| EBG − B (pp) | +10.8 [4.2, 17.6] | +18.2 [11.0, 25.5] | +17.6 [9.3, 26.3] | +14.7 [9.8, 19.9] |

The direction is positive for every model on every contrast, and every interval excludes zero. The magnitude is not
uniform: the two mid-sized Qwen models gain two to four times as much on H-primary as Qwen2.5-3B or Llama-3.1-8B.

The Llama-3.1-8B result deserves emphasis because it was pre-stated as a risk. On the p2val2 development split this
model showed essentially no EBG benefit over RT (+1.1 pp), and the preregistration said that a repeat on eval3 would
be "a failure to generalise across families" and would be reported as such. On eval3 the benefit is small but
positive and its interval excludes zero (+6.8 pp [3.3, 10.5]). The harm reduction, however, does not transfer at all
(−0.3 pp): Llama-3.1-8B was already producing very few harmful answers under RT, because it abstains instead — 35.3%
unnecessary abstention under RT, 44.0% under EBG, 60.7% under B. For this model EBG converts abstentions into
answers rather than converting harmful answers into correct ones, which is a different mechanism from the one the
hypothesis describes.

## 7.5 Secondary cells

The two greedy-only secondary models are analysed separately and are never pooled with the primary models.

| Contrast | Qwen2.5-14B (secondary) | Llama-3.2-3B (format-limited) |
|---|---|---|
| EBG − RT | +29.9 [23.0, 36.9] | +12.3 [6.3, 18.3] |
| EBG − T | +22.8 [15.9, 29.9] | +29.5 [22.8, 36.3] |
| EBG − LG | +13.8 [8.5, 19.3] | +7.1 [1.5, 12.6] |
| EBG − B | +17.2 [10.1, 24.3] | +34.7 [27.7, 41.7] |

Qwen2.5-14B shows the largest EBG − RT effect of any model in the study. Llama-3.2-3B failed the preregistered
readiness criterion before the campaign and is reported here only for completeness: its absolute success is very low
(41.8% under EBG, 7.1% under B) and it abstains unnecessarily on 88.7% of B runs, so its differences measure
recovery from near-total failure rather than the effect the hypotheses concern.

## 7.6 Absolute performance

No configuration is good in absolute terms. The best preregistered configuration, EBG, answers 61.3% of pooled
primary tasks correctly, and on the subset of tasks that have a definite answer rather than a genuine conflict the
pooled answer accuracy under EBG is 46.0%. Qwen2.5-7B and Qwen3-8B reach 75.0% and 77.8% overall under EBG;
Llama-3.1-8B reaches 33.0%. The contribution is a relative one about mechanism design, not a claim that small agents
handle conflicting persistent memory well.


# 8. Statistical analysis

## 8.1 What was tested, and how

The unit is the task. Success per task is the mean over a model's decodings, contrasts are paired within model and
decoding, and families — (category, attribute) pairs, 135 of them among the 268 valid tasks — are the clusters. The
test is a two-sided sign-flip permutation of family-level summed differences with families pooled across models, so
a family's sign flips for all four models together; with 135 families the exact enumeration is infeasible and the
analysis uses 100,000 seeded Monte-Carlo draws, whose smallest attainable estimate is 1 × 10⁻⁵. Confidence intervals
are 95% percentile bootstraps over families, 10,000 seeded resamples, of the mean task-level difference. Holm
correction runs over the four preregistered contrasts at α = 0.05; everything else is exploratory and reported with
Benjamini–Hochberg adjustment [@holm1979simple; @benjamini1995fdr; @good2005permutation; @efron1979bootstrap;
@field2007clustered]. Missing pairs and harness errors count as failures and stay in every denominator; in this
campaign there were none of either.

All four primary contrasts reach the Monte-Carlo floor before correction, so Holm's step-down leaves them at
4 × 10⁻⁵, and family support is lopsided rather than marginal: for EBG − RT, 43 to 66 families favour EBG per model
against 3 to 25 against.

## 8.2 Preregistered sensitivity analyses

Section 4.8 records a wording inconsistency in the frozen preregistration about which items form the primary set.
The analysis follows §5 — all 268 mechanically valid items — and reports the alternatives as sensitivity analyses so
that a reader who prefers the §6 reading can apply it.

| Analysis | Tasks | Families | EBG − RT | EBG − T | EBG − LG | EBG − B |
|---|---|---|---|---|---|---|
| **Primary (confirmatory)** | 268 | 135 | **+17.1** [12.2, 22.1] | **+14.5** [10.5, 18.6] | **+15.9** [10.4, 21.2] | **+15.3** [10.3, 20.5] |
| Double-agreement subset | 161 | 94 | +14.3 [8.8, 20.4] | +12.7 [7.8, 17.8] | +19.7 [13.8, 25.7] | +14.7 [9.3, 20.3] |
| Flagged complement | 107 | 67 | +21.3 [13.4, 29.3] | +17.2 [11.8, 23.0] | +10.2 [1.3, 19.4] | +16.4 [7.5, 25.5] |
| Qwen2.5-14B-agreed subset | 232 | 123 | +15.3 [10.2, 20.7] | +13.9 [9.6, 18.4] | +15.5 [9.8, 21.4] | +14.8 [9.5, 20.3] |

Every contrast keeps its sign, every interval excludes zero, and every Holm-adjusted p stays below 0.05 in all three
sensitivity sets. The preregistered conclusions do not depend on the item-set reading. Effects are somewhat larger on
the flagged complement than on the double-agreement subset, which is the opposite of what an "annotator noise
inflates the effect" account would predict.

## 8.3 Independent cross-check

A second implementation recomputed the 60 model × configuration success counts and the four pooled primary
differences directly from the raw run files, by a different route from the frozen analysis. All 60 counts and all
four differences agree exactly (EBG − RT 17.1 against 17.1, 1072 task pairs against 1072, and likewise for the other
three). The pipeline is configured to stop if they do not.

## 8.4 Post-hoc exploratory sensitivity to the platform transition

Two of the eighteen cells contain rows produced after an unplanned node reboot that changed the host kernel and the
NVIDIA driver (Section 11). Both analyses below were specified **after** that transition came to light and **before**
any confirmatory outcome was inspected, but they are post-hoc with respect to the preregistration. They are
exploratory, they are reported separately, and they do not change the preregistered verdicts.

| Analysis | Rows | EBG − RT | EBG − T | EBG − LG | EBG − B |
|---|---|---|---|---|---|
| Confirmatory (all 16 primary cells) | 51,456 | +17.1 [12.2, 22.1] | +14.5 [10.5, 18.6] | +15.9 [10.4, 21.2] | +15.3 [10.3, 20.5] |
| Exploratory: straddling cell excluded | 48,240 | +17.0 [12.1, 22.0] | +14.4 [10.5, 18.5] | +15.9 [10.5, 21.2] | +15.3 [10.3, 20.5] |
| Exploratory: Qwen3-8B, pre-reboot decodings only | 9,648 | +24.8 [17.9, 31.8] | +15.7 [9.2, 22.2] | +11.9 [5.1, 19.0] | +17.4 [9.0, 26.1] |

Dropping `qwen3_8b_T07_s3` entirely moves the pooled primary estimates by at most 0.1 pp. Restricting Qwen3-8B to
its three fully pre-reboot decodings gives +24.8 pp on H-primary against +25.0 pp with all four — a difference of
0.2 pp, far inside the bootstrap interval.

**What this establishes:** the preregistered conclusions do not depend on the one cell whose rows straddle the
platform change. **What it does not establish:** that the platform change had no effect on generation. These
analyses drop or isolate the straddling cell; they do not compare the same task and configuration across the two
driver versions, which this campaign cannot do, because no such pair exists. Agreement here is consistent with the
transition being inert and equally consistent with an effect too small to move a family-clustered permutation test
at this sample size, and it says nothing about the two individual tasks whose own rows are split across platforms.

## 8.5 Exploratory contrasts

The remaining contrasts were preregistered as exploratory and are reported with BH adjustment. Their substantive
reading is in Section 9.

| Contrast | Difference (pp) | 95% CI | p (BH) | Harmful difference (pp) |
|---|---|---|---|---|
| EBG − EB | +6.0 | [3.9, 8.2] | 2.2 × 10⁻⁵ | +0.5 [−0.1, 1.2] |
| EBG − R | +16.3 | [11.7, 21.0] | 2.2 × 10⁻⁵ | −12.9 [−18.0, −8.2] |
| EB − T | +8.5 | [5.4, 11.6] | 2.2 × 10⁻⁵ | −4.7 |
| EB − G | +11.8 | [8.3, 15.2] | 2.2 × 10⁻⁵ | −5.2 |
| LG − LA | −2.4 | [−5.6, 0.6] | 0.167 | **+8.1** [6.1, 10.2] |
| EBG − EBG-all | **−9.7** | [−15.2, −4.3] | 0.0013 | −3.7 [−6.6, −1.3] |
| EBG − EBG-unsafe | −0.2 | [−1.0, 0.7] | 0.776 | −0.2 [−0.6, 0.2] |


# 9. Ablation studies

EBG combines four things: evidence-basis labels shown to the agent, a reversible notice at the terminal action,
**gating** that enforces only strong-strength resolutions, **safe submission** that keeps the pre-notice answer when
the response to a notice is unusable, and **search-before-submit**. The preregistered exploratory contrasts separate
them. Two of the four components carry essentially the whole effect; one is close to inert on success but changes
the failure profile; and one — gating — is a deliberate trade of success for safety rather than a free improvement.

The mechanism-level columns below come from the descriptive metrics over all six models. *Conflict preserved* is the
share of genuinely unresolvable groups the agent still reports as a conflict; *false resolution* is the share it
asserts an ordering for anyway.

| Config | Success (pooled primary) | Harmful | Conflict preserved | False resolution | Unnecessary abstention | Format error |
|---|---|---|---|---|---|---|
| B | 46.0% | 7.0% | 65.2% | 12.8% | 19.5% | 3.2% |
| G | 43.5% | 7.9% | 72.8% | 9.2% | 16.0% | 3.7% |
| T | 46.9% | 7.4% | 79.6% | 3.6% | 16.9% | 3.1% |
| R | 45.0% | 16.1% | 74.2% | 12.3% | 9.4% | 6.1% |
| RT | 44.2% | 22.6% | 66.8% | 19.0% | 11.1% | 6.2% |
| LA | 47.9% | 13.2% | 57.8% | 21.9% | 18.4% | 3.5% |
| LG | 45.4% | 21.3% | 42.4% | **37.0%** | 17.1% | 3.3% |
| EB | 55.3% | 2.7% | 81.6% | 2.0% | 16.7% | 3.1% |
| **EBG** | **61.3%** | **3.1%** | **88.5%** | **1.9%** | 12.8% | 3.3% |
| EBG-all | 71.1% | 6.9% | 77.3% | 12.9% | 13.9% | 3.3% |
| EBG-unsafe | 61.5% | 3.3% | 89.0% | 1.6% | 9.9% | **6.4%** |
| EBG-noR3 | 60.0% | 3.4% | 83.3% | 1.9% | 17.6% | 2.9% |

## 9.1 The labels do most of the work (EB − T = +8.5 pp, EB − G = +11.8 pp)

Replacing metadata-derived labels with evidence-basis labels, with no enforcement at all, raises success by 11.8 pp
over G and 8.5 pp over the temporal annotator T, and cuts the harmful rate from 7.9% and 7.4% to 2.7%. False
resolution falls from 9.2% (G) and 3.6% (T) to 2.0%. Most of the benefit of the mechanism is in *what the agent is
told*, before anything is enforced. This is the part of the result we consider best supported.

## 9.2 Gating adds a real but smaller increment (EBG − EB = +6.0 pp)

Adding the gated notice to the labels adds 6.0 pp [3.9, 8.2] of success with no detectable change in harm
(+0.5 pp [−0.1, 1.2]), lifts conflict preservation from 81.6% to 88.5%, and cuts step-limit failures from 2.0% to
1.0%. The notice mostly recovers runs where the agent had the right labels and still submitted the superseded value.

## 9.3 Search-before-submit is worth about 1.3 pp (EBG vs EBG-noR3)

Removing it costs 1.3 pp of success (61.3% to 60.0%) and raises unnecessary abstention from 12.8% to 17.6%: agents
that do not re-read memory before answering abstain more. Small, cheap, and in the expected direction.

## 9.4 Safe submission buys format robustness, not success (EBG − EBG-unsafe = −0.2 pp, n.s.)

Success is statistically indistinguishable with and without safe submission (−0.2 pp [−1.0, 0.7], p = 0.78), and so
is harm. What it changes is the failure profile: format errors nearly double without it, 3.3% to 6.4% pooled (2.8% to
5.8% on primary models), while unnecessary abstention falls from 12.8% to 9.9%. Without the fallback, a mangled
reply to a notice becomes a format failure; with it, the pre-notice answer stands, which sometimes means an
abstention. We would keep the component for robustness, but the success claim does not rest on it.

## 9.5 Gating versus ungated enforcement: the central trade (EBG − EBG-all = −9.7 pp)

Enforcing *every* arbitration, not only strong-strength ones, scores **9.7 pp higher** than EBG (71.1% against
61.3%; CI [−15.2, −4.3], BH p = 0.0013). It also:

- more than doubles the harmful rate, 3.1% → 6.9% (difference −3.7 pp [−6.6, −1.3] in EBG's favour);
- restores arbitrary picks from 13 to 166 runs;
- raises false resolution from 1.9% to 12.9%, and drops conflict preservation from 88.5% to 77.3%.

This is the clearest answer in the study to the second half of our research question, and it goes against the
mechanism we proposed. **Indiscriminate enforcement does increase harmful answers** — but on this benchmark it also
produces more correct answers than gated enforcement does. Gating is a trade, not a dominance. Which side of it one
should take depends on the relative cost of a wrong confident answer and a missed correct one, which this benchmark
does not price. We state the trade rather than resolve it, and we note two qualifications. The gap is sensitive to
the item set: it is −4.8 pp [−9.7, 0.3], not significant, on the double-agreement subset, and −17.1 pp on the
flagged complement, which suggests part of it lives in items where the annotators themselves disagreed. And success
and harm are not commensurable units: 9.7 pp of success against 3.8 pp of additional harm and a tenfold increase in
arbitrary picks is a judgement, not an arithmetic comparison.

## 9.6 Gating helps only when the arbiter is reliable (LG − LA = −2.4 pp, harm +8.1 pp)

The same gating machinery, driven by an LLM arbiter instead of the deterministic one, does not help: success is
statistically unchanged (−2.4 pp [−5.6, 0.6], p = 0.167) and harm rises by 8.1 pp [6.1, 10.2]. Under LG, false
resolution reaches 37.0% and conflict preservation falls to 42.4% — the worst of any configuration, worse than no
mechanism at all. For Qwen2.5-7B the LLM arbiter's gated variant falsely resolves 75.9% of genuine conflicts.

The useful generalisation is therefore not "enforcement helps" and not "gating helps", but that enforcement inherits
the reliability of whatever supplies its labels. Enforcing a deterministic, evidence-grounded arbiter's strong
resolutions helps; enforcing a record-metadata scanner's (RT) or a language model's (LG) is actively harmful. The
value of the evidence-basis idea is that it gives enforcement something defensible to enforce, and a principled
place to stop.


# 10. Failure analysis

EBG answers 61.3% of pooled primary tasks correctly, so roughly two runs in five still fail. This section accounts
for them. Counts are over the 4288 pooled primary runs per configuration unless stated otherwise; the full tables,
including every model × configuration cell, are in `PHASE3/PHASE3_FAILURE_ANALYSIS.md` and
`PHASE3/PHASE3_FAILURE_TABLES.md`.

## 10.1 Where EBG's failures go

| Failure mode under EBG | Pooled primary | Share of all runs |
|---|---|---|
| False conflict (reports a conflict where the evidence resolves) | 867 | 20.2% |
| Unnecessary abstention | 494 | 11.5% |
| Stale value (answers with the superseded value) | 119 | 2.8% |
| Format error (no parsable final answer) | 120 | 2.8% |
| Arbitrary pick | 13 | 0.3% |
| Step-limit exhaustion | 42 | 1.0% |
| Unsupported claim | 0 | 0.0% |
| Missing row / harness error | 0 | 0.0% |

EBG's residual failure is dominated by **over-conservatism**, not by harm: false conflicts and unnecessary
abstentions together account for 31.7% of runs, against 3.1% harmful. The mechanism was designed to move errors in
exactly this direction, and it did. Whether that is the right place for them is a deployment question, not one this
benchmark settles.

## 10.2 The two mechanism-level failure modes it was built to prevent

*False resolution* — asserting an ordering the evidence does not support — falls from 12.8% of conflict groups under
plain memory, 19.0% under RT and 37.0% under LG to **1.9%** under EBG. *Conflict preservation* rises from 65.2%,
66.8% and 42.4% to **88.5%**. The preregistered known limitations of Evarb-0.2 are visible in the residue: the
arbiter misses a negator more than four tokens before the cue, does not treat "correcting" as a correction cue, and
resolves `negated_both_stand` to the rival instead of a contradiction. Those were pinned by tests before the freeze
and were not fixed during the campaign.

## 10.3 Model-family failure profiles differ in kind

| Model, EBG | Success | Unnecessary abstention | Format error | Harmful |
|---|---|---|---|---|
| Qwen2.5-3B | 59.5% | 3.6% | 0.0% | 2.9% |
| Qwen2.5-7B | 75.0% | 0.6% | 0.1% | 4.3% |
| Qwen3-8B | 77.8% | 0.0% | 0.0% | 4.7% |
| Llama-3.1-8B | 33.0% | 44.0% | 11.1% | 0.7% |
| Qwen2.5-14B (secondary) | 73.5% | 1.2% | 13.8% | — |
| Llama-3.2-3B (format-limited) | 41.8% | 35.9% | 0.0% | — |

The Llama family fails differently from the Qwen family. Llama-3.1-8B abstains on 44.0% of EBG runs and fails to
produce a parsable answer on 11.1%, while being the *least* harmful model in the study — it rarely commits to a
wrong value because it rarely commits. Its EBG − RT harm difference is therefore −0.3 pp, against −24.5 to −27.7 pp
for the Qwen models: there was almost no harm to remove. This is the sharpest limit on generalisation in our
results. The mechanism's harm-reduction claim is demonstrated on models that actually produce harmful answers; on a
model whose dominant failure is abstention and malformed output, EBG raises success (+6.8 pp over RT, +14.7 pp over
B) by converting abstentions into answers, which is a different causal story from the one the hypotheses state.

Qwen2.5-14B's 13.8% format-error rate under every configuration is a separate, configuration-independent artefact of
its output formatting in this harness, not a mechanism effect.

## 10.4 Execution failures

There were none in the analysis sense: all 18 cells reached 3216 rows, with 0 missing pairs, 0 duplicates and 0
harness-error rows across all 57,888 runs, so no run was scored as `missing`. Step-limit exhaustion is a task-level
failure rather than an execution failure, and EBG has the second-lowest rate of it (1.0%, against 2.4% for B).

Two cells were interrupted by the node reboot described in Section 11 and were resumed by the controller after the
damaged tail of each file was quarantined. Neither interruption cost a completed run, and neither produced a
duplicate. The recovery itself is reported there rather than here, because it is an infrastructure event, not an
agent failure.

## 10.5 What the failure analysis does not cover

The scorer's categories are mechanical. We did not inspect individual eval3 transcripts for qualitative failure
patterns, because the task texts remain sealed until publication; the failure analysis is therefore at the level of
outcome categories and rates, not of narrative error types. Phase 1's failure taxonomy supplied the mechanisms we
tested for (M8, M9, M11); confirming that those specific mechanisms are what produced the eval3 residue would need a
transcript study that we have not done.


# 11. Platform and resume deviation analysis

Two of the eighteen cells were interrupted by an unplanned reboot of the compute node and finished on a changed host
platform. This section states what happened, what it is known to have affected, and what cannot be established from
the data. Nothing in it changes the preregistered analysis; the full ledger is in `PHASE3/PHASE3_DEVIATIONS.md` and
the underlying investigation in `PHASE3/PHASE3_G4_FORENSIC_REPORT.md`.

## 11.1 How the deviation surfaced

The finalization job stopped at its integrity gates with two failures of the form *"manifest field `client` differs
between starts"*, for `qwen3_8b_T07_s3` and `llama32_3b_greedy`. The gate compared the manifest's `client` object as
a single opaque JSON blob, so it could not distinguish a change of client implementation from a change in read-only
host telemetry, and its message named neither the subfield nor the values.

A field-level comparison of the four manifest lines showed one differing subfield, in both cells:
`client.gpu_mem_gib`, from 44.6 to 44.4. That field is the device's total memory as the driver reports it,
`round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1)`. It is stored in the client's version record and
read only when the manifest is written; the model is loaded with an explicit device map and no memory budget, so the
value cannot influence placement, offloading, batching or generation. Every field that determines what was executed
— model, snapshot path, adapter, dtype, temperature, seed, decoding, maximum new tokens, parser version, family
adapter, torch, transformers, CUDA runtime — is identical across the two starts of both cells, as are the split hash,
the configuration list and the 14 frozen code hashes, which are in fact identical across all 20 starts of the
campaign.

## 11.2 What actually changed

The compute node rebooted at 2026-11-20T10:11:58, having been up since 2026-10-03. Across that reboot the host
Linux kernel and the NVIDIA kernel driver both changed. The post-reboot state is directly verified
(kernel 6.8.0-149-generic; NVIDIA module 580.178.04, loaded at 10:12:02). The pre-reboot state is **inferred**, not
read: the node booted before the NVIDIA packages were upgraded on 2026-10-11 from 580.173.02 to 580.178.04, so it
continued running the already-loaded 580.173.02 module against newer userspace — which is corroborated by the
recorded failure of `nvidia-smi` on this node on 2026-11-11 with a driver/library version mismatch, and by the same
command working after the reboot. The previous boot's kernel log is not readable from the account used, so this
remains an inference. The 0.2 GiB difference in reported device memory is consistent with a driver revision changing
its reserved carve-out; device identity is excluded, because both GPUs report identical totals and the two affected
cells occupied different devices in both of their starts.

The reboot also truncated the row being written in each of the two in-flight cells. Slurm requeued both jobs; both
failed immediately in the resume path on the truncated line; the controller quarantined the damaged tail — 1153 and
3617 bytes, each containing zero complete rows — and resubmitted. Both cells then completed to the full 3216 rows
with no duplicates. One collateral loss is permanent: Slurm's requeue overwrote the console logs of the two
interrupted starts. Their manifest lines survive with the code hashes and freeze state intact.

## 11.3 Scope, and why the contrasts are not confounded by it

| | `qwen3_8b_T07_s3` | `llama32_3b_greedy` | Campaign |
|---|---|---|---|
| Rows on the old platform | 2345 | 3107 | 56,908 (98.3%) |
| Rows on the new platform | 871 (27.1%) | 109 (3.4%) | **980 (1.69%)** |
| Whole tasks on the new platform | 72 | 9 | — |
| Tasks split across platforms | 1 (`eval3-0202`) | 1 (`eval3-0267`) | **2 of 268** |

The other sixteen cells finished before the reboot. Because the runner's outer loop is over tasks and its inner loop
over the 12 configurations, a resumed segment carries all 12 configurations for every whole task it contains: the
post-reboot segments are balanced across configurations to within one row per configuration. A platform-induced
shift would therefore move all twelve arms of a task together, which the paired, family-clustered design differences
out. The residual within-task confound is exactly the two boundary tasks named above, one in a single decoding of one
primary model and one in the never-pooled format-limited cell.

## 11.4 Resume and the random stream

The client seeds PyTorch once per process. A resume is a new process, so the post-resume segment of a sampled cell
restarts its sampling stream from the base seed instead of continuing it. Only `qwen3_8b_T07_s3` is affected: the
other resumed cell is greedy, and no other cell was resumed. This does not bias the sampling distribution — the
design fixes T = 0.7 with seeds 1, 2 and 3, and makes no claim about stream continuity — but it does mean that
reproducing that cell byte for byte now requires reproducing the interruption at the same row. It is recorded as a
reproducibility limitation rather than a validity threat.

## 11.5 Decision, and what remains unknown

Both cells are retained. The preregistration pins the mechanism, harness, runner, analysis and data — all
hash-verified identical across both starts — and pins the hardware only as "bf16, one L40", which held; the GPU
driver and host kernel are not pinned. Resume is explicitly provided for, and a restart is permitted only for a
freeze mismatch, a seal mismatch or a runner defect, none of which occurred. Re-running the two cells now would
additionally be a post-hoc choice taken with knowledge of which cells were affected.

What cannot be established from this campaign is whether the two driver versions produce different generations for
these models. No `(task, config)` pair exists on both platforms, because the quarantined fragments contain no
complete rows, so there is nothing to compare; settling it would require re-running completed cells. The exploratory
sensitivity analyses in Section 8.4 test whether the conclusions depend on the straddling cell, which is a weaker
and different question: agreement there is consistent with the transition being inert, but equally consistent with an
effect too small to move a family-clustered permutation test at this sample size, and it says nothing about the two
tasks whose own rows are split.

Two durable corrections follow from this episode rather than from any result. First, the integrity gate now
distinguishes client identity from host observation explicitly, fails closed on any unclassified field, and prints
the field and values on a mismatch. Second, a reporting-only platform-continuity check now derives, from the
manifests alone, which cells straddle a node boot, and records the surrounding facts separated into verified,
inferred and unknown — so that a platform transition can never again reach the analysis visible only as a rounding
difference in a telemetry field. The run manifest should also record the driver version, kernel release and boot
identifier; that is a change for future campaigns, since the Phase 3 manifests are frozen artefacts and were not
rewritten.


# 12. Discussion

## 12.1 What the study shows

The research question was whether evidence-basis-aware arbitration improves persistent-memory reliability for small
tool-using agents, and whether indiscriminate enforcement can increase harmful answers. Both halves now have an
answer, and they do not point the same way.

On the first half, the preregistered comparison is unambiguous within its scope. The full mechanism beat enforced
record-and-temporal labels by 17.1 pp of task success, advisory temporal labels by 14.5 pp, an LLM arbiter under the
same gated policy by 15.9 pp, and unlabelled memory by 15.3 pp, with every interval well clear of zero after Holm
correction, in the same direction for all six models, and stable across three item-set definitions. Harm fell with
it: 3.1% of EBG runs were harmful against 22.6% under RT, and arbitrary picks fell from 252 to 13.

On the second half, the answer is yes — and it cuts against our own design. Enforcing every arbitration rather than
only strong-strength ones raised false resolution from 1.9% to 12.9%, restored arbitrary picks from 13 to 166, and
more than doubled the harmful rate. It also scored 9.7 pp *higher* on task success. Gating buys safety with
accuracy; it does not dominate.

## 12.2 The mechanism that actually carries the effect

The ablations locate the benefit more precisely than the headline contrasts do. Most of it is in the labels: giving
the agent evidence-basis statuses with no enforcement at all (EB) is worth +11.8 pp over metadata labels and
+8.5 pp over advisory temporal labels, and cuts harm from ~7.5% to 2.7%. Gating adds a further +6.0 pp. Safe
submission adds nothing measurable to success (−0.2 pp, p = 0.78) while halving format errors, and
search-before-submit adds 1.3 pp.

The LG − LA contrast tells us why this ordering matters. The same gating machinery driven by an LLM arbiter produced
no success gain and 8.1 pp *more* harm, with 37.0% false resolution. Enforcement inherits the reliability of
whatever supplies its labels. Enforcing a record-metadata scanner's labels (RT) tripled harm relative to plain
memory; enforcing a language model's (LG) tripled it too; enforcing a deterministic arbiter's strong, evidence-cited
resolutions did not. The contribution is best stated as: *the evidence basis is what makes enforcement safe to apply
and tells you where to stop applying it* — not that gating or enforcement is good in itself.

## 12.3 The label-harm finding replicates

The study began with a development observation: metadata-derived reliability labels made small agents worse than no
labels, because the agents followed the label instead of the text. On sealed confirmatory data this replicates
without modification. G scored 43.5% against B's 46.0%, with more harm (7.9% vs 7.0%) and more false conflicts
(31.4% vs 26.4%). Enforcing those labels (RT) made it worse again: 44.2% success and 22.6% harm. A reliability
signal that the evidence does not support is not merely useless to a small agent; it is actively misleading, and
enforcement amplifies it.

## 12.4 Where it does not generalise

Model family matters more than model size for *how* the mechanism helps. For the three Qwen models the story is the
one the hypotheses describe: harmful answers become correct ones, with harm differences of −24.5 to −27.7 pp. For
Llama-3.1-8B it is not: that model abstains on 44% of EBG runs and fails to format an answer on 11%, is the least
harmful model in the study under every configuration, and gains its +6.8 pp over RT by converting abstentions into
answers. Its harm difference is −0.3 pp, because there was almost no harm to remove. The preregistration anticipated
this risk from the development split, where Llama showed +1.1 pp; eval3 gives a small positive effect whose interval
excludes zero, which is better than the development data suggested but is not the same effect as the one measured on
Qwen. We do not claim universal superiority across families.

Nor is the absolute picture good. The best configuration answers 61.3% of tasks correctly and 46.0% of the tasks
that have a definite answer. Llama-3.2-3B, which failed the readiness criterion before the campaign, remains near
the floor. These are small models on synthetic, template-regular, English, ISO-dated records in one harness. Nothing
here speaks to frontier models, to natural memory logs, or to conflicts without lexical cues.

## 12.5 Development evidence, exploratory results and confirmatory results

Three kinds of evidence appear in this paper and should not be read alike. The Phase 1 pilot numbers in Section 1
and the p2val2 observations in Section 4.10 are **development evidence**: they motivated the design and the
hypotheses and are not tests of them. The four Holm-corrected contrasts and S4 are **confirmatory**: preregistered,
frozen before the data existed, and reported here with whatever sign they came out. Everything in Section 9, the
three item-set sensitivity analyses, and the two platform sensitivity analyses in Section 8.4 are **exploratory**;
the last two are additionally post-hoc, specified after the platform transition came to light. We draw no
confirmatory conclusion from any of them, including the EBG − EBG-all trade that we consider the most interesting
result in the paper.

## 12.6 How much the deviations limit the conclusions

Three execution facts constrain what can be claimed, and we weigh them explicitly rather than listing them.

**The platform transition (Section 11).** 980 of 57,888 rows (1.69%), in two of eighteen cells, were produced after
the host kernel and NVIDIA driver changed. Because the runner's loop order makes a resumed segment carry all twelve
configurations for every whole task it contains, the transition is balanced across configurations to within one row,
and dropping the affected cell entirely moves the pooled estimates by at most 0.1 pp. The residual confound is two
tasks out of 268 whose own rows are split across platforms. We judge this a disclosure, not a threat to the primary
conclusions — but the honest statement of its limit is that we cannot demonstrate the driver change was inert,
because no task and configuration was run on both platforms.

**The two affected configurations.** One is a single T = 0.7 seed of one primary model, contributing a quarter of
one of sixteen primary cells; the other is the format-limited secondary cell that is never pooled. Neither carries a
confirmatory claim on its own.

**Qwen3-8B re-seeding.** The resumed cell restarted its sampling stream rather than continuing it. This does not
bias the sampling distribution, since the design fixes the seeds and makes no claim about stream continuity, but it
means that one cell cannot be reproduced byte for byte without reproducing the interruption.

Taken together these limit *reproducibility* of two cells and leave one unanswerable question about driver effects;
they do not reach the preregistered contrasts, which are stable to removing the affected data entirely.

## 12.7 What would change our mind

Four results would undermine the contribution as stated. A replication in which evidence-basis labels without
enforcement (EB) did not beat metadata labels would remove the part of the effect we consider best supported. A
benchmark that prices wrong confident answers against missed correct ones, on which ungated enforcement came out
ahead overall, would make gating the wrong default rather than a defensible one. A model family on which EBG lowered
success would bound the claim further than Llama-3.1-8B already does. And a transcript study showing that EBG's
remaining 20.2% false conflicts are items the arbiter *could* have resolved from the text would move the mechanism's
known limitations from a documented residue to a design flaw.


# 13. Threats to validity and limitations

> Draft, 18 November 2026. Sources: `PHASE3/LIMITATIONS.md` (written 17 November 2026 before any eval3 outcome, with execution notes added 18 November before any eval3 outcome was analysed; "to be extended, never softened, after results"), `PHASE2/PREREGISTRATION.md` §12, §15–16, `PHASE2/BENCHMARK_EVAL3_SPEC.md` §2, `PHASE2/BASELINE_COMPARISON.md` §4. Everything in this section was fixed before the confirmatory results were known. Limitations revealed by the results are added in Section 13.8, which extends this section and does not soften it.

## 13.1 Construct validity: the data

- **No human validation.** No human authored or adjudicated eval3. The texts were written by Qwen2.5-14B, and the only independent checks are two model annotators. On the development split p2val2 they agreed with gold on 58/90 (Llama-3.1-8B) and 71/90 (Qwen2.5-14B) items; on eval3 on 174/268 and 232/268 (`FREEZE_eval3.json`). Annotator agreement is not ground truth, and annotator disagreement may reflect annotator error rather than a faulty item.
- **Writer, annotator and evaluated model overlap.** Qwen2.5-14B wrote the texts, is one of the two annotators, and is a secondary evaluated model. Its results are reported separately for this reason.
- **The author defined the categories.** The categories and their semantics were chosen by the mechanism's author and are encoded in the skeleton generator. What is independent of the author is the wording of every record and historical question and the blind check that the wording carries the intended meaning, not the choice of what to test. A benchmark designed by the author of the method may favour the method's notion of evidence.
- **Synthetic, templated records.** eval3 has heavy surface regularity: the seal checks report many duplicated masked texts and 8-gram template overlaps with development texts, and 16 of 19 masked brief templates are shared with p2val2. Items are synthetic templates, not natural memory logs. Current-state question templates and distractor texts are shared with every split.
- **Untested surface forms.** Value dates appear in ISO form only; 8 of 276 skeleton items were excluded mechanically (values written in long-form dates), so long-form value dates are untested. Text is English only.
- **Implicit conflicts are out of scope.** eval3 tests conflicts and resolutions signalled lexically or by metadata. Conflicts without explicit cues, as in STALE [@chao2026stale], are not tested; Evarb is expected at best to fall back to time order or leave them unresolved.

## 13.2 Construct validity: the mechanism

- **Known failures of the frozen Evarb-0.2, stated before any eval3 outcome** (`PREREGISTRATION.md` §12; pinned in `PHASE2/tests/test_known_limitations.py`):
  - *Long-range negation:* a negator more than four tokens before the cue is missed. A same-date record such as "It is not the case that, after the long review, the team was revised from 40 to 60" is resolved to 60 with strong (enforceable) strength.
  - *`negated_both_stand`:* "…does not replace X. Both figures stand until they are reconciled" is resolved to the rival value (moderate) instead of a contradiction; 0 of 4 on p2val2.
  - *"correcting" is not a correction cue:* a same-day "correcting … to Y" record yields a strong contradiction, which the gated policy would enforce.
  
  eval3 items of these forms count against Evarb as written. Evarb-0.2 was not changed.
- **Lexical, English cue lists.** Paraphrases outside the lists fall back to time order.
- **Historical and as-of questions** score zero at component level for every method, because component scoring asks for the current value; question intent is handled in the agent loop. Component-level accuracy figures therefore understate agent-level behaviour on these categories.
- **Composite primary contrast.** EBG and RT differ in the arbiter, gating, notice wording and safe submission at once. H-primary can show that the combination helps, not which element is responsible; attribution rests on exploratory ablations.

## 13.3 Internal validity: development history and analyst degrees of freedom

- **The mechanism was developed on data from the same generator family.** Evarb-0.1 was tuned on the development fixtures and looked at once on p2val, after which the semantics and the mechanism were revised. p2val2 was untouched by tuning, but its results were known before the preregistration was frozen and informed the power analysis and the primary-set decision.
- **Development evidence that bears on the hypotheses** (`PREREGISTRATION.md` §15): on p2val2 (90 single-item families), EBG − RT was about +1 pp on Llama-3.1-8B, and ungated enforcement (EBG-all) scored higher than gated EBG with more harmful answers. These were known at the freeze and did not change the hypotheses.
- **Audit not blind.** The p2val2 item audit was done by the mechanism's maintainer. That it preceded the outcome files rests on file timestamps and the auditor's own statement; the hash record was written after all outputs existed (`PREREGISTRATION.md` §16).
- **Primary-set change and wording inconsistency.** The primary item set was changed on 16 November from double-agreement items to all valid items, before any eval3 output existed and before any p2val2 mechanism output was opened. §6 and §8 of the frozen preregistration still describe the earlier rule. The analysis follows §5; the double-agreement subset is reported as a sensitivity analysis (Section 4.8).
- **Prompts** were fixed before eval3 but were developed on earlier splits.

## 13.4 Statistical conclusion validity

- **Power is a development estimate.** It treats the p2val2 effect as the truth. EBG − LG is under-powered at half the measured effect (0.53).
- **Decoding repetitions are not independent samples.** The three T = 0.7 seeds measure decoding noise, not new tasks; the family is the unit of inference.
- **Family structure differs from development.** p2val2 has single-item families; eval3 has up to two items per family, so variance estimates from development may not transfer.
- **Pooling across models.** H-primary is pooled over four primary models. A pooled effect can coexist with no effect in one model; per-model results are reported for this reason, without tests counted toward the claims.

## 13.5 External validity

- **Model scale.** Models are small open-weight (3B–14B). No frontier model is evaluated. Results do not extend to larger models.
- **One harness.** One tool-using harness (memlab, evarb loop 0.2) with a synthetic tool registry and a simple retrieval store. Other harnesses, retrieval methods or step budgets may change the results.
- **Second family partly format-limited.** The second family is represented by Llama-3.1-8B, which needs the `FamilyClient` adapter and had 9 format failures per configuration on p2val2. A conclusion about family generality therefore rests on a model that is partly format-limited. Llama-3.2-3B failed the readiness criterion and is reported separately.
- **Qwen3-8B** is run with thinking disabled.
- **Latency** is wall time under single-occupancy Slurm jobs on one L40 while other projects' CPU jobs may share the node. The T = 0.7 and 14B budget numbers were partly estimated.

## 13.6 Execution notes recorded before any eval3 outcome was analysed

The following deviations from the planned execution were recorded in `PHASE3/LIMITATIONS.md` on 18 November 2026, before any eval3 outcome was analysed.

1. **Concurrent cells.** From 18 November 08:58 UTC, cells 9–17 ran up to two at a time, one per L40 (Slurm generic resources; `CUDA_VISIBLE_DEVICES` 0 and 1), under a second controller job (`PHASE2/hpc/phase3_controller_v2.sbatch`, job 4257) that replaced retry controller 4243. Cells 0–7 ran alone on the node's GPUs. Model, decoding, configurations, data and code were unchanged, and the in-job freeze, seal and preregistration checks passed for every cell. Wall-time latency for cells that overlapped another AGENTRUN cell was measured with a second GPU process on the node, so it is not strictly single-occupancy. The measured throughput of the running Llama-3.1-8B cell did not change when the second cell started (13.9 vs 14.2 runs per minute). Latency is a reported, untested quantity (`PREREGISTRATION.md` §11).
2. **Wall-time limit for the 14B cell.** The Qwen2.5-14B cell was given a 36-hour wall-time limit on the command line (the sbatch file is unchanged), so that it would not be split by the 12-hour default.
3. **Incidental exposure of progress lines.** While checking cell 8's progress on 18 November, the last five progress lines of its Slurm log were displayed in the operator's terminal. They contained the task id, configuration and scored outcome for three eval3 runs. No task text, gold label or aggregate was seen, nothing was changed as a result, and progress has since been read from row counts only. We disclose this because the preregistration's rule is that nobody connected to the mechanism reads eval3 contents before scoring; three per-run outcome labels were seen, after the freeze and with no possible effect on frozen materials.

## 13.7 Separation from other work

This study is separate from the authors' earlier work on fine-tuning tool-using models, which used a different benchmark and asked a different question; no result from that work is used here.

## 13.8 Limitations revealed by the results

This subsection was written after the confirmatory results and extends Sections 13.1 to 13.7; nothing above it was
changed.

1. **Gating is a trade, not an improvement.** Ungated enforcement of the same evidence-basis labels scored 9.7 pp
   higher than the gated mechanism while more than doubling the harmful rate and raising false resolution from 1.9%
   to 12.9% (Section 9.5). Our design prefers the safer side of that trade, but this benchmark assigns no relative
   cost to a wrong confident answer versus a missed correct one, so it cannot establish that the preference is
   right. The gap is also item-set sensitive: −4.8 pp and not significant on the double-agreement subset, −17.1 pp
   on the flagged complement.
2. **The harm-reduction claim rests on models that produce harm.** For the three Qwen models EBG − RT reduces the
   harmful rate by 24.5 to 27.7 pp. For Llama-3.1-8B it reduces it by 0.3 pp, because that model abstains (44.0% of
   EBG runs) or fails to format an answer (11.1%) instead of committing to a wrong value. The success gain there
   comes from converting abstentions into answers, which is a different mechanism from the one the hypotheses
   describe (Section 10.3).
3. **Residual failure is over-conservatism.** Under EBG, 20.2% of runs report a conflict where the evidence
   resolves and 11.5% abstain unnecessarily, against 3.1% harmful. Whether that distribution of errors is
   preferable is a deployment judgement the study does not make.
4. **Absolute performance is low.** The best configuration answers 61.3% of tasks correctly and 46.0% of the tasks
   that have a definite answer. Conclusions are about relative mechanism design, not about competence.
5. **One component is unsupported on success.** Safe submission changes success by −0.2 pp (p = 0.78). It is
   retained for format robustness (3.3% versus 6.4% format errors), not because the success data support it.
6. **The platform transition cannot be shown to be inert.** 1.69% of rows were produced after a mid-campaign kernel
   and GPU-driver change. Removing the affected cell moves the pooled estimates by at most 0.1 pp, but no task and
   configuration was executed on both platforms, so whether the change altered generation is unknown and not
   knowable from this campaign (Section 11, `PHASE3/PHASE3_DEVIATIONS.md` D1).
7. **Two cells are not byte-reproducible.** Those two cells straddle the platform change, and one of them restarted
   its sampling stream when it resumed (D3). The analysis remains byte-reproducible from the archived raw outputs.
8. **The failure analysis is category-level only.** eval3 transcripts stay sealed until publication, so we did not
   inspect individual failures qualitatively and cannot confirm that the Phase 1 failure mechanisms are what
   produced the eval3 residue (Section 10.5).


# 14. Reproducibility and artifact availability

## 14.1 What was frozen, and when

| Item | Frozen as | Date |
|---|---|---|
| Mechanism (Evarb-0.2) | `FREEZE_evarb.json`: 9 modules, the runner, the analysis script, the component evaluator, 3 frozen dependencies | 2026-11-14 |
| Evaluation data (eval3) | sealed on the cluster; hashes in `FREEZE_eval3.json` | 2026-11-16 |
| Preregistration | SHA-256 `221013b3…` recorded in `FREEZE_eval3.json` | 2026-11-17 |

Every Phase 3 job refused to start unless the `evarb-0.2` files matched `FREEZE_evarb.json`, the sealed eval3
directory passed `sha256sum -c`, and the preregistration's hash equalled the value recorded at the freeze. All 20
job starts of the campaign printed `freeze evarb-0.2 mismatches []` and the sealed preregistration hash. The runner
additionally refused any task file whose hash differed from the sealed one.

## 14.2 Provenance of every row

Each cell writes a manifest line at every start recording the model identity and resolved snapshot path, the PEFT
adapter (none here) and its hash, decoding parameters and seed, dtype, maximum new tokens, parser version, family
adapter, `torch`, `transformers` and CUDA runtime versions, the GPU model, the split hash, the configuration list,
the SHA-256 of all 14 mechanism and harness files, the Slurm job id, the start time, and how many pairs were already
complete at that start. The 14 code hashes are identical across all 20 starts. A SHA-256 manifest of every raw file
is written when the campaign closes, and re-verified by the finalization job before anything is analysed.

## 14.3 Regenerating every number

The whole pipeline runs as one CPU-only Slurm job with no interactive steps:

```bash
cd research/AGENTRUN_PUBLICATION_2026/PHASE3
sbatch scripts/phase3_finalize.sbatch     # gates -> stage -> platform report -> verify -> analyze
                                          #       -> exploratory -> report -> results draft -> seal -> commit
```

or stage by stage from an existing checkout of the raw outputs:

```bash
bash scripts/run_phase3_analysis.sh verify       # completeness, freeze, preregistration and client-identity checks
bash scripts/run_phase3_analysis.sh analyze      # frozen analyze_p2.py, 100,000 seeded permutations, Holm
bash scripts/run_phase3_analysis.sh exploratory  # the two post-hoc sensitivity analyses (Section 8.4)
bash scripts/run_phase3_analysis.sh report       # independent cross-check, then tables and CSVs
```

Every reported number comes from that path. An independent re-computation of the per-configuration counts and the
four primary effect sizes must agree exactly or the pipeline stops; the report generator computes no statistic of
its own. On the shareable development split the same pipeline reproduces its outputs byte for byte.

## 14.4 What a reproduction can and cannot match

The analysis is reproducible byte for byte from the archived raw outputs: the permutations and bootstraps are
seeded, and the gates re-verify the inputs first.

Regenerating the *raw outputs* is a weaker guarantee, and this campaign has three specific caveats, all recorded in
`PHASE3/PHASE3_DEVIATIONS.md` and summarised in Section 11:

1. GPU kernels are not bitwise deterministic across hardware or library versions, so a re-run elsewhere may differ
   at the token level for some runs.
2. Two cells — `qwen3_8b_T07_s3` and `llama32_3b_greedy` — were not produced on a single host platform, because the
   node rebooted into a new kernel and NVIDIA driver partway through them. They cannot be reproduced row for row on
   one fixed driver version. The other sixteen cells were produced on one platform throughout.
3. `qwen3_8b_T07_s3` additionally re-seeded its sampler when it resumed at row 2345, so reproducing that cell byte
   for byte would require reproducing the interruption at the same row.

## 14.5 Availability

- **Released with the repository:** the code (mechanism, harness, runner, analysis, integrity gates, tests), the
  frozen manifests, the preregistration, the development splits and their runs, all aggregate Phase 3 results
  (JSON and CSV), the Phase 3 reports, the deviation ledger, the forensic report and the platform-continuity report,
  and the reproducibility package in `PHASE4/reproducibility/` (environment, model snapshots, dataset rules, Slurm
  scripts, analysis instructions, expected outputs, tests, limitations, deviations, SHA-256 manifests).
- **Withheld until publication:** the confirmatory eval3 items, their annotations and the per-run transcripts, so
  that the test set stays uncontaminated. Their hashes are public in `FREEZE_eval3.json`, so a later release can be
  checked against the frozen versions. The cluster's per-run logs are withheld for the same reason, since their
  progress lines carry per-task outcomes.
- **Not redistributed:** model weights. The exact Hugging Face snapshot hashes are listed in
  `PHASE4/reproducibility/MODELS.md`; obtain the weights under each model's own licence. Because the eval3 texts
  were written by Qwen2.5-14B-Instruct, the Qwen licence terms on model outputs apply to them.
- The package contains no credentials, tokens, API keys, host names, IP addresses or user identifiers; commands use
  `<user>@<cluster-login>` and `$HOME/AGENTRUN_HPC` as placeholders.

Nothing in this section claims public availability for an artifact that is in fact restricted: the eval3 items, the
annotations, the per-run transcripts and the cluster logs are restricted today, and the table above says so.


# 15. Conclusion and future work

Small tool-using agents with persistent memory fail in a particular way when their records disagree: they follow a
reliability label instead of the text, and enforcing that label at the terminal action makes the failure worse. This
paper tested a specific alternative — arbitration that states the *evidence basis* for each resolution and enforces
only what that basis supports — under a preregistration frozen before the confirmatory data existed.

The preregistered result is positive and stable. Across 57,888 runs on 268 sealed tasks, gated evidence-basis
arbitration beat enforced record-and-temporal labels by 17.1 pp of task success, advisory temporal labels by
14.5 pp, an LLM arbiter under the same policy by 15.9 pp, and unlabelled memory by 15.3 pp, all Holm-corrected, in
the same direction for all six models and stable across three item-set definitions. Harmful answers fell from 22.6%
to 3.1%, and the false-resolution rate on genuinely unresolvable groups fell from 19.0% to 1.9%.

Three findings qualify what that means. Most of the gain is in the labels, not the enforcement: evidence-basis
labels alone are worth 11.8 pp over metadata labels, with gating adding 6.0 pp. Ungated enforcement of the same
labels scores 9.7 pp higher still, while doubling harm and restoring the arbitrary picks the mechanism was built to
prevent — so gating trades accuracy for safety rather than dominating, and this benchmark does not price that trade.
And the same gating driven by an LLM arbiter produced no gain and more harm, which suggests the general lesson is
not about gating but about what enforcement is allowed to enforce.

The best configuration still answers only 61.3% of tasks correctly, and its residual failure is over-conservatism:
20.2% false conflicts and 11.5% unnecessary abstentions, against 3.1% harm. The mechanism moved errors where it was
designed to move them. Whether that is the right place for them is a deployment judgement this study does not make.

**Future work.** Four directions follow directly. (1) A benchmark that assigns explicit costs to a wrong confident
answer and to a missed correct one, so the gating trade in Section 9.5 can be decided rather than described.
(2) Extending the arbiter beyond lexical English cues and ISO value dates, where its documented limitations —
long-range negation, "correcting" as a correction cue, `negated_both_stand` — currently live. (3) A transcript study
of EBG's remaining false conflicts, to separate items the arbiter could have resolved from items where abstaining is
correct; this needs the eval3 release. (4) Model-family coverage: the Llama results show the mechanism helping
through a different route, and a family whose dominant failure is abstention needs a different evaluation of what
"reliability" means.

Two methodological artefacts also come out of the campaign rather than the results. Run manifests should record the
host kernel, GPU driver and boot identifier, not only the framework versions: in this campaign a mid-campaign
platform change was visible only as a 0.2 GiB difference in a telemetry field. And an integrity gate should separate
what identifies a run from what merely observes its host, fail closed on anything unclassified, and report the
difference it is willing to tolerate. Both changes are implemented and tested in the released code.

