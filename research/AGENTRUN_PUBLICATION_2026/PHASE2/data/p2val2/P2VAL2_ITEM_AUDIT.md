# p2val2 item audit

**16 November 2026, 10:03 UTC.** Every one of the 92 p2val2 items was read against its skeleton (values, record dates, sources, brief, gold) after the writer and assembler finished (Slurm job 4199) and **before any evarb, TEA, legacy, LLM-arbiter or annotator output on p2val2 had been looked at**. Auditor: Claude (the assistant that maintains evarb, i.e. not independent of the mechanism's author). This audit is therefore a documented quality check, **not** a replacement for the blind annotations, and it does not change the pre-specified primary set (items where both blind annotators agree with gold).

## Checks per item

Text matches the intended meaning; every value preserved verbatim (also enforced mechanically); negation and quotation represented as briefed; gold unambiguous to a careful reader; no gold leaked to the writer (writer input has no gold, `GENERATOR_AUDIT.json`); entities unique (no duplicates within or across splits, same audit).

## Results

| Outcome | Items | n |
|---|---|---|
| Excluded by the pre-specified mechanical rule (values written long-form: "February 19th, 2027") | 0018 (conflict_same_validity), 0072 (backfilled_entry) | 2 |
| Text correct, gold unambiguous | all others | 86 |
| **Flagged: gold arguably ambiguous** | see below | 4 |

Flagged items (kept in the data set; reported as an audit-sensitivity subset):

| Item | Category | Gold | Problem |
|---|---|---|---|
| p2val2-0020 | authority_both | conflict | record 2 says the team size "is **now** 14" — change wording against a same-day, same-source rival; a reader may resolve to 14 |
| p2val2-0087 | conflict_same_validity | conflict | record 2: the port "**changed to** 3089 effective May 31" — the writer added change wording the brief did not ask for; a reader may resolve to 3089 |
| p2val2-0039 | quoted_claim | answer east-mesa-1 | "According to a recent statement, Project Thothoth **will now be using** far-cape-5 instead of east-mesa-1" — attributed, but phrased as a forthcoming fact; reading it as an established change is defensible |
| p2val2-0062 | quoted_claim | answer 2027-05-30 | "According to a recent message, the deadline **should now be** 2027-08-30" — same pattern, weaker |

Other observations, not flagged:
- Several `incidental_change_word` texts (0068, 0091) say the rival value "remains" — this asserts the rival as established, which still yields a genuine conflict.
- 0055's first record is clumsy ("For mid-basin-4, Project Traezaest is deployed in the mid-basin-4 cloud region") but unambiguous.
- All historical / as-of questions name no value; all as-of dates fall strictly between the two validity dates.
- Long-form value dates were avoided by the v2 writer in 88 of 90 items as intended; validity dates are still written in varied long forms ("June 24th, 2026", "May 25, 2026").

## How this is used

- Primary analysis: unchanged (blind-annotator agreement rule, `p2val2_PRIMARY_IDS.json`).
- Sensitivity: results are also reported on primary minus the 4 flagged items. This subset was fixed here, before outcomes were seen.
