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

[CITATION NEEDED: Cohen (1960) for κ]

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

Results: [RESULTS PENDING — filled from PHASE3 verified outputs]
