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

Results: [RESULTS PENDING — filled from PHASE3 verified outputs]

## 1.6 Scope

The study concerns small open-weight models (3B–14B) in one synthetic tool-use harness with templated records, English text and ISO-format value dates. It makes no claim about frontier models, natural memory logs, implicit conflicts without lexical cues, or other harnesses. Section 13 lists the limitations that were fixed before the confirmatory results existed.
