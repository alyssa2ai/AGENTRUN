# Evidence arbitration specification (evarb-0.2, frozen)

**14 November 2026; updated 16 November 2026 for the frozen version.** The frozen code is `evarb-0.2` (`FREEZE_evarb.json`, frozen 2026-11-14T08:14:16Z; hashes re-verified locally and on the cluster on 16 November). This specification describes `evarb/cues.py`, `evarb/arbiter.py`, `evarb/policy.py` and `evarb/render.py`. If the code and this document ever disagree, the code is normative, and `tests/` pins the behaviour.

## 0. Changes from evarb-0.1 to evarb-0.2 (the frozen version)

evarb-0.1 was tuned on the development fixtures (160/160) and then looked at once on p2val (55/70 against the v1 skeleton gold). The p2val blind annotation showed that the v1 benchmark semantics for negated and reported claims were inconsistent, and the semantics were revised (**v2: a record that does not establish its own value leaves the established value standing**). evarb-0.2 implements v2 and closes the gaps the look exposed. **From that point p2val is development data**; the untouched validation split is p2val2.

| Change | Code | Effect |
|---|---|---|
| Negated replacement without a "both stand / disagree" marker sets the record aside (the rival stands, moderate) | `arbiter.py` step 1 | was `contradiction` in 0.1 |
| A record whose own value appears only inside reported, conditional or negated clauses is set aside | `cues.own_value_asserted`, `arbiter.py` step 1 | quoted claims no longer produce a contradiction |
| Doubt guard: a time-order winner whose text signals deliberation or doubt (`DOUBT_RE`: suggested, proposed, still, planned, likely, TBC, …) is `moderate` (advised, never enforced) | `cues.DOUBT_RE`, `arbiter.py` §6 | removes the one enforceable error left on p2val |
| Validity cues widened: "starting from/on", "beginning", "with effect from", "takes effect", "applies from" | `cues.VALID_FROM_RE` | |
| Ordinal dates ("3rd of March 2026", "March 3rd, 2026") | `cues.DATE` | |
| Retention phrasings ("remains in force", …) | `cues.KINDS["retention"]` | |

Every 0.2 change is pinned by a test (`test_doubt_word_downgrades_time_order_to_advisory`, `test_ordinal_dates`, `test_validity_cue_starting_from`, `test_negation_scope_is_local`, `test_p1hold_N3_negated_cue_is_not_resolved`, …). The rows in §3 and §4 below that mention "contradiction" for negated replacements describe the case **with** an explicit "both stand / disagree" marker.

## 1. Inputs and outputs

**Input.** The records of one `(entity, attribute)` group. Each record has:
- `record_id`, `value`, `text`, `source`;
- `recorded_on` (ISO date, or `""` when missing).

**Output** (`arbiter.Resolution`):

| Field | Values |
|---|---|
| `kind` | `unchallenged` (one distinct value) · `resolved` · `contradiction` · `unresolved` |
| `basis` | one of the ten bases in §3 |
| `strength` | `strong` · `moderate` · `none` |
| `current_value` | the resolved value, or `None` |
| `statuses[rid]` | `current` · `superseded` · `contradictory` · `unresolved` · `unchallenged`, each with `basis`, `strength`, and optionally `superseded_by` / `conflicts_with` / `valid_from` / `note` |

**"Historical" is not an arbiter status.** The renderer shows a superseded record as `historical` when the question asks about an earlier time (§5), because history depends on the question, not on the records.

## 2. Clause-level cues (`cues.py`)

**Splitting.** Each record text is split into clauses at sentence ends, semicolons and dashes. Every cue is found inside a clause and qualified by what scopes over it there:

| Qualifier | Rule |
|---|---|
| `negated` | a negator among the 4 tokens before the cue: not, no, never, neither, nor, without, nobody, none, nothing, and `n't` forms |
| `quoted` | the cue is inside quotation marks, or the clause contains a reporting verb (said, wrote, claimed, reported, according to, suggested, …) |
| `hypothetical` | the clause contains a conditional or modal marker: if, would, could, might, were to, unless, in case, assuming, "may" + verb |

**Cue kinds:**
- **correction:** corrected, erratum, typo, "was a mistake / wrong", amended;
- **supersession:** replaces, supersedes, "instead of", "no longer", revised, update(d), overrides;
- **dismissal:** disregard, ignore, discard, withdrawn, retracted, obsolete, void;
- **retention:** "remains valid", "still stands", unchanged;
- **unconfirmed:** "not (yet) confirmed / approved", pending, proposed, draft, tentative, provisional, "under review", "subject to approval";
- **contradiction:** "both … stand", "until reconciled", discrepancy, disagree, "conflicts with";
- **hypothetical_value:** the record's own value is stated inside a hypothetical clause.

**Rival reference.** A clause refers to a rival record if:
- it mentions the rival's value (token-bounded; numbers compared numerically, and digits inside dates or identifiers are not matched); or
- it uses an anaphor for an earlier value ("the earlier figure", "the previous value", "this morning's figure") and there is exactly one rival value.

**Validity dates:**
- `valid_from`: a date after "as of / as at / effective / valid from / since / dated / updated on / starting";
- `valid_to`: a date after "until / through / valid to";
- formats: ISO, "3 March 2026", "March 3, 2026";
- a date equal to the record's own value (a deadline) is never a validity date.

## 3. The ten evidence bases and their strength

| Basis | When | Strength |
|---|---|---|
| `explicit_correction` | asserted correction or dismissal that refers to the rival, at different dates | strong (moderate if the correcting record is *older* by `recorded_on`) |
| `explicit_supersession` | asserted replacement or revision that refers to the rival, at different dates | strong (same caveat) |
| `same_day_correction` | asserted correction, dismissal or supersession between same-date records, referring to the rival | strong |
| | the same with an unreferenced correction or dismissal, used only to break a same-time tie | moderate |
| `valid_time` | every established record states a validity date; the latest is unique in value | strong |
| `record_time` | unique latest `recorded_on` value | strong |
| `source_authority` | same-time tie in which exactly one value comes from an authoritative source (`system_of_record`, `tool:registry_lookup`, …) | moderate |
| `genuine_contradiction` | same time, different values, no ordering evidence | strong if there is no cue of any kind, otherwise moderate |
| `negated_correction` | (a) a negated correction or supersession together with an asserted "both stand / disagree" marker: contradiction | strong |
| | (a') 0.2: a negated replacement with no such marker ("this does not replace 40"): that record is set aside and the rival is current | moderate |
| | (b) retention of the rival, or the record's own change unconfirmed: that record is set aside and the rival is current | moderate |
| `quoted_or_hypothetical` | (a) the only ordering cue is reported speech: unresolved | none |
| | (b) the record's change or value is hypothetical: that record is set aside, the rival is current | moderate |
| `insufficient_evidence` | missing dates with no text dates; cyclic or inconsistent correction cues | none |

## 4. Precedence (`arbiter.arbitrate`)

1. **One distinct value:** `unchallenged`.
2. **Set aside records that do not establish their own value:**
   - their value is unconfirmed or proposed;
   - their change is hypothetical (unless they also carry an asserted correction);
   - they state that the rival remains valid;
   - (0.2) they say they do not replace the rival and no record says both stand;
   - (0.2) their own value appears only in reported, conditional or negated clauses.

   Set-aside records are `unresolved`. If the remaining records share one value, it is `current` (moderate).
3. **Negated pairs or an asserted contradiction marker:** `contradiction` (`negated_correction` or `genuine_contradiction`, strong).
4. **Asserted, referenced text edges** (r supersedes q):
   - if they define a unique winning value, it is `current` with the edge basis;
   - if they are inconsistent (cycles, two winners): `unresolved` / `insufficient_evidence`.
5. **Validity dates on every established record:** order by them (`valid_time`).
6. **Otherwise, `recorded_on` on every established record:** order by it (`record_time`). (0.2) If the winner's text matches the doubt guard, the strength is `moderate`.
7. **A tie at the top of 5 or 6 is broken, in this order, by:**
   - (a) an unreferenced correction or dismissal claimed by exactly one value (`same_day_correction`, moderate);
   - (b) a reported or hypothetical cue among the tied records (`unresolved`, `quoted_or_hypothetical`);
   - (c) exactly one authoritative source (`source_authority`, moderate);
   - (d) otherwise `contradiction` (`genuine_contradiction`).
8. **Missing dates with no text dates:** `unresolved` / `insufficient_evidence`.

**`update` and `revised` never break a tie on their own.** They are often incidental ("Weekly status update: …"); `amended` counts as a correction.

## 5. Question intent (`policy.question_intent`)

**Historical** if the question contains:
- "before the change / correction / update",
- previously, originally, initially, "used to", formerly, "at first", "prior to", "at the time",
- or a date after "as of / on / at" (also stored as `as_of`).

Otherwise the question is **current**.

## 6. Basis-gated enforcement (`policy.decide`)

Rules apply to anchored groups only: groups the agent retrieved whose entity is named in the question. The first matching rule wins.

| Rule | Condition | Action |
|---|---|---|
| **P3** | no `memory_search` and no successful registry result | REQUEST_EVIDENCE: "search memory; if nothing relevant, your previous submission stands" |
| **P1** | current question; answer equals a superseded value and not the current one | ENFORCE if the resolution is enforceable, else ADVISE |
| **P2** | current question; status `conflict`; every anchored multi-value group is resolved | ENFORCE if all are enforceable, else ADVISE |
| **P4** | answer equals a value of a contradictory group, and no registry result | ENFORCE toward `conflict` if enforceable, else ADVISE |
| — | anything else, including every unresolved group | NO_ACTION |

**Enforceable**, by mode:
- `gated`: strong;
- `all`: strong or moderate;
- `none`: never.

**Notices.** At most one notice per run. Notices state the basis truthfully: for example, a same-date correction is never described as "no two values on the same date", which was Phase 1 architecture item 15.

**Safe submission.** If the submission that follows a notice is unparsable, missing, or the step budget runs out, the final answer reverts to the pre-notice submission.

**Model capability is not an input to the policy.**

## 7. Labels shown to the agent (`render.py`)

```json
{"status": "current|superseded|historical|contradictory|unresolved|unchallenged",
 "evidence": "<basis in words>", "certainty": "established|likely|not established",
 "superseded_by": [...], "conflicts_with": [...], "valid_from": "...", "note": "..."}
```

An order the evidence cannot establish is shown as `unresolved` with "read the record texts". It is never shown as "conflicting", because Phase 1 found that small models follow wrong cautionary labels (M8, M13).

## 8. LLM arbiter baseline (`llm_arbiter.py`)

**Same output schema.**
- The prompt states the same evidence rules in plain language.
- The model returns a status and basis for every record.
- Strength is derived from the basis, with the same table as §3.
- Unparsable or inconsistent output (two different current values) becomes `unresolved` and is counted as a format failure.
- **LA:** labels only. **LG:** labels with the same gated policy.
