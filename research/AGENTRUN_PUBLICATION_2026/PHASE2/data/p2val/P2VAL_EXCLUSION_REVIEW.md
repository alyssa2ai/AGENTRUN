# Review of the 11 excluded p2val items

**16 November 2026.** Independent re-reading of every item that `assemble.py` excluded (rule: each record text must name its project and contain its own value, `evarb.cues.mentions`). Source: `p2val_skeleton.jsonl`, `p2val_texts.jsonl`, `p2val_MANIFEST.json`. p2val is development data, so reading it is permitted. **Decision: all 11 stay excluded.** The rule was fixed before the texts existed; re-admitting items after reading them would be a post-hoc change to the data set.

| Item | Category | Attribute | Validator reason | What the text actually does | Verdict on the text |
|---|---|---|---|---|---|
| p2val-0006 | supersession_later_ref | deadline | slots 1, 2 lack own value | both dates written long-form ("February 16, 2027", "April 2, 2027"); meaning correct | **validator false negative** |
| p2val-0012 | unconfirmed_change | deadline | slots 1, 2 lack own value | long-form dates; "proposed … not yet approved" correct | validator false negative |
| p2val-0039 | conflict_same_validity | deadline | slots 1, 2 lack own value | long-form dates; both valid from June 24, 2026, correct | validator false negative |
| p2val-0044 | unsupported | region | slot 1 lacks own value | slot 1 deadline written long-form; slot 2 fine | validator false negative |
| p2val-0069 | backfilled_entry | deadline | slots 1, 2 lack own value | long-form dates; validity dates (Aug 13 vs Jun 23) give the intended order | validator false negative |
| p2val-0081 | quoted_claim | deadline | slots 1, 2 lack own value | long-form dates; claim reported as "claimed … replacing", correct for v1 | validator false negative |
| p2val-0056 | unconfirmed_change | team_size | slot 2 lacks entity | slot 2: "A proposed change suggests reducing the team size to 5 people…" — no project named | **genuine failure**: the record cannot be attached to the project |
| p2val-0087 | incidental_change_word | deadline | slot 2 lacks entity and value | slot 2 names no project ("our timeline"); date long-form | genuine failure (entity) |
| p2val-0027 | same_day_correction_noref | deadline | slots 1, 2 lack own value | "has a delivery deadline." / "…is updated for today." — **no dates at all** | genuine failure (values dropped) |
| p2val-0060 | conflict_plain | deadline | slots 1, 2 lack own value | "has a delivery deadline." / "the delivery is due." — no dates | genuine failure |
| p2val-0075 | historical_question | deadline | slots 1, 2 lack own value | "deadline is set." / "delivery date … is noted." — no dates | genuine failure |

## Findings

1. **6 of 11 exclusions are validator false negatives** caused by the v1 writer rewriting ISO dates in long form. `mentions` matches dates only in ISO form. The texts themselves carry the intended meaning.
2. **5 of 11 are genuine writer failures:** 3 dropped the values entirely, 2 omitted the project name.
3. **Attribute bias:** 9 of the 11 excluded items are `deadline` items (plus one `region` item whose text failed on a deadline record, and one `team_size`). Only **5 of 14** deadline items survive, against 13–16 for every other attribute. Ten categories lose one of their four items; `unconfirmed_change` loses two. Results on p2val are not balanced over attributes, and say little about date-valued facts.
4. **Consequence already in place for p2val2 and eval3:** the v2 writer (`write_and_annotate.py`) requires every value verbatim, with dates in ISO form, and retries up to four times with the specific failure named. This removes the false negatives, but it also means **every date value in p2val2 and eval3 is ISO-formatted in the text**, so long-form value dates are not tested there. (Validity dates such as "starting March 3rd" are not values and may still be long-form.) This is recorded as a limitation in `BENCHMARK_EVAL3_SPEC.md` and `PHASE2_FINAL_REPORT.md`.
5. `mentions` belongs to the frozen evarb-0.2 (`evarb/cues.py`) and is not changed.
