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
