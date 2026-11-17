# Negation, conflict and edge-case tests for evarb-0.2

**16 November 2026.** All numbers below were re-run on 16 November against the frozen code (`FREEZE_evarb.json`, every hash verified). Test suite: `tests/` (82 passed, local Python 3.11; also hash-verified on the cluster copy). Component tables: `data/BASELINE_dev_groups.md`, `data/BASELINE_regression_groups.md`.

**Status of this evidence: development.** The 114 development groups and 46 regression groups were used to build and tune evarb (160/160 after tuning). They show that the intended behaviour is implemented and pinned. They are **not** independent validation. Validation is in `BASELINE_COMPARISON.md` (p2val, p2val2).

## 1. Required behaviours, where each is tested, and the current result

| Behaviour (brief §4) | Unit / integration tests (all pass) | Fixture category | legacy | TEA | **evarb-0.2** |
|---|---|---|---|---|---|
| Negation ("does not replace 40") | `test_negation_scope_is_local`, `test_negated_cue_never_enforced_toward_a_value`, `test_p1hold_N3_negated_cue_is_not_resolved` | `negated_correction` (6) | 2/6 | 1/6 | **6/6** |
| Genuine conflicts stay conflicts | `test_genuine_conflicts_stay_conflicts`, `test_same_text_validity_date_is_contradiction`, `test_unreferenced_update_word_does_not_break_tie` | `conflict_plain`, `conflict_rival_mentioned`, `conflict_same_text_date`, `incidental_update_word`, `authority_both` (30) | 30/30 | 30/30 | **30/30** |
| Conditional corrections ("if approved, 60") | `test_linguistic_safeguards`, `test_bases` | `hypothetical_change`, `unconfirmed_update` (12) | 0/12 | 0/12 | **12/12** |
| Quoted corrections ("Ana said it was corrected to 60") | `test_linguistic_safeguards` | `quoted_correction` (6) | 6/6 | 0/6 | **6/6** |
| Same-day changes | `test_same_day_correction_false_conflict_fixed_in_loop`, `test_unreferenced_correction_breaks_tie_only_moderately`, `test_false_conflict_enforced_with_truthful_notice_for_same_day_correction` | `same_day_correction_named/unnamed` (12) | 0/12 | 4/12 | **12/12** |
| Incomplete timestamps | `test_metadata_insufficient_groups_resolve_to_expected`, `test_labels_say_unresolved_not_conflicting_when_order_unknown`, `test_unresolved_never_enforced` | `missing_timestamp`, `missing_timestamp_text_dated` (12) | 0/12 | 12/12 | **12/12** |
| Historical queries | `test_intent`, `test_stale_answer_on_historical_question_not_enforced`, `test_historical_label_and_no_enforcement` | `historical_question` (6) | 6/6 | 6/6 | **6/6** |
| Missing evidence (no search) | `test_no_search_requests_evidence` (P3) | agent-level only | | | |
| Source-authority ambiguity | `test_bases` (authority tie, moderate only), `test_moderate_resolution_only_advised` | `authority_one` (6), `authority_both` (6) | 6/12 | 6/12 | **12/12** |
| Retention ("40 remains valid") | `test_bases` | `retention` (6) | 0/6 | 0/6 | **6/6** |
| Ordinal dates, validity phrasing, doubt words (0.2) | `test_ordinal_dates`, `test_validity_cue_starting_from`, `test_doubt_word_downgrades_time_order_to_advisory`, `test_deadline_value_is_not_a_validity_date` | `valid_time_same_import`, `backfilled` (12) | 0/12 | 12/12 | **12/12** |
| Cyclic / inconsistent corrections | `test_cyclic_corrections_are_unresolved`, `test_correcting_record_older_than_corrected_is_not_strong` | — | | | |

## 2. Phase 1 failures retained as regression cases

Every Phase 1 failure family is kept in `data/regression_groups.jsonl` (46 groups, rebuilt from the frozen Phase 1 builders; split hashes asserted by `test_split_hashes_unchanged`) and in `tests/test_regression_phase1.py`:

| Phase 1 family | What went wrong in Phase 1 | legacy | TEA | evarb-0.2 |
|---|---|---|---|---|
| p1dev S7 (same-day correction naming the old value) | legacy labels harmed ≤ 8B models | 0/8 | 8/8 | **8/8** |
| p1dev S8 (validity date in text) | same | 0/8 | 8/8 | **8/8** |
| p1hold H7a / H7b (corrections with / without reference) | TEA enforced unreferenced corrections | 0/12 | 5/12 | **12/12** |
| p1hold H8a (validity text) | | 0/6 | 5/6 | **6/6** |
| p1hold H9 | | 0/6 | 6/6 | **6/6** |
| p1hold N3 (negated cue on a genuine conflict) | TEA resolved it; RT enforced arbitrary picks | 6/6 | 0/6 | **6/6** |
| p1dev S3, N1, N2 metadata order | must remain unchanged | | | pinned by `test_S4_and_C4_metadata_order_unchanged` and the parametrised N1/N2/S3 tests |

The R3 break (Phase 1 M10: a correct abstention destroyed by search-before-submit) is pinned by `test_phase1_M10_R3_break_is_reverted_not_a_format_error`.

## 3. The LLM evidence arbiter on the same cases (for reference)

Same groups, same scorer, prompt in `evarb/llm_arbiter.py`, greedy decoding, run in Slurm job 4189 (raw: `raw/llm_arbiter/`). Correct / n:

| Category | Qwen2.5-7B | Llama-3.1-8B | Qwen2.5-14B |
|---|---|---|---|
| negated_correction | 1/6 | 0/6 | 3/6 |
| quoted_correction | 0/6 | 0/6 | 0/6 |
| hypothetical + unconfirmed | 4/12 | 2/12 | 8/12 |
| retention | 1/6 | 0/6 | 0/6 |
| genuine conflicts (5 categories) | 22/30 | 0/30 | 27/30 |
| missing_timestamp | 0/6 | 0/6 | 0/6 |
| Phase 1 N3 | 5/6 | 0/6 | 1/6 |

The LLM arbiter is weakest exactly where the deterministic scoping rules are strongest (negation, quotation, retention). Llama-3.1-8B as arbiter resolves almost every genuine conflict to one value.

## 4. What these tests do not show

- They do not show generalisation to phrasings the author did not write. p2val (independent writer) found gaps in retention phrasing, validity cues and ordinal dates; those were fixed in 0.2, which is why p2val is development data now.
- Fixture texts are short and single-sentence. Long, multi-topic records are not covered.
- Negation scope is a 4-token window. Long-range negation ("It is not the case that, after the review, the budget was revised to 60") is outside it; checked on 16 November with a same-date pair (40, then "It is not the case that, after the long review in the spring, the team of Project X was revised from 40 to 60"): evarb-0.2 returns `resolved`, `same_day_correction`, **strong**, 60, i.e. an enforceable error. No fixture or validation item covers this; it is a known limitation of the frozen version and is not fixed (the mechanism is frozen). It is pinned as a regression case in `tests/test_known_limitations.py`, which asserts the current wrong output; any behaviour change fails the test and marks a new development version.
