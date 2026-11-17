# eval3: sealed evaluation set specification

**14 November 2026; corrected 16 November 2026.** Build state and hashes: `FREEZE_eval3.json` (written only after the sealed build job has run). Generator: `benchmark/`.

**Build status (16 Nov, 10:30 UTC):** Slurm job 4200 was building eval3 (freeze check passed, 276-item skeleton written); completion and seal not yet verified. Once verified, `FREEZE_eval3.json` holds the counts, agreement statistics, split checks and hashes.

## 1. Purpose and separation

| Material | Role | May the mechanism be tuned on it? |
|---|---|---|
| `data/dev_groups.jsonl`, `p2dev_tasks.jsonl`, `regression_groups.jsonl` | development | yes (and it was) |
| Phase 1 `p1dev`, `p1hold` | development (p1hold lost held-out status in Phase 1) | yes |
| `data/p2val/` | first validation split | it was looked at once (evarb-0.1), the mechanism was then revised to evarb-0.2, so **p2val is development material** (logged in `FREEZE_evarb.json`) |
| `data/p2val2/` | validation of the frozen evarb-0.2 | **no** (built after the freeze; untouched) |
| **eval3** | **confirmatory (Phase 3)** | **no.** Built only after the mechanism freeze; never opened by the mechanism's author |
| benchmark-v2 sealed set (130 tasks) | fine-tuning thread | not used (no memory scenarios) |

## 2. Independence

**Order (enforced by timestamps and hashes in `FREEZE_evarb.json` and `FREEZE_eval3.json`):**
1. Freeze the mechanism (code hashes recorded).
2. Generate the eval3 skeleton.
3. Write the texts.
4. Annotate.
5. Seal.

Steps 2–5 run in one Slurm job that writes only to `~/AGENTRUN_HPC/sealed/eval3/` on the cluster, outside the source tree. The job log contains counts, agreement statistics and hashes only. The sealed files are made read-only.

**Who did what:**

| Role | Who | Sees the mechanism? | Sees gold? |
|---|---|---|---|
| Categories and semantics | Mechanism author (documented in `skeleton.py`) | yes | defines it |
| Skeleton (entities, values, dates, sources, gold) | Deterministic script, seed 20261201 | — | generates it |
| Record texts and historical-question wording | **Qwen2.5-14B-Instruct** (open weights, greedy, local) | no | no (briefs only) |
| Blind annotation 1 | **Llama-3.1-8B-Instruct** | no | no |
| Blind annotation 2 | **Qwen2.5-14B-Instruct** (separate prompt and run) | no | no |
| Reading eval3 items or labels | **nobody connected to the mechanism, before Phase 3 scoring** | — | — |

**Limitation, stated rather than hidden.** No independent human authored or adjudicated eval3. What is independent of the mechanism's author is:
- the wording of every record and historical question;
- the check that the wording carries the intended meaning.

The second annotator is the same model as the writer, so the two annotators are not equally independent. The Llama annotator is the stronger check. Qwen2.5-14B is a secondary model in Phase 3, which is a further reason to report it separately.

## 3. Construction

- **Names:** memlab name pool slice `[14000:17600]` for entities and `[17600:20000]` for eval3 distractor entities (p2val distractors `[20000:21200]`). These are disjoint from dev (`[150:1600]` and `[0:150]`), eval2 (`[1600:5200]`), p1dev (`[5200:8000]`), p1hold (`[8000:10400]`), p2dev (`[10400:12800]`) and p2val (`[12800:14000]`).
- **Seed:** 20261201.
- **Size:** 23 categories (skeleton v2) × 12 items = **276 items**, each with 5 distractor records. Families are category × attribute; with 12 items per category and 6 attributes in rotation, **138 families of 2 items**. (The earlier "22 × 12 = 264" and "8 conflict categories" described the v1 skeleton. Counts here are from `skeleton.build('eval3')` structure only.)
- **Balance:**
  - 15 categories with an answer (180 items): 8 with the new, latest or only value; historical and as-of (old value asked for); and, under the v2 semantics, retention, unconfirmed, hypothetical, negated replacement and quoted claim (the established old value stands);
  - 7 conflict categories (84 items): plain, same validity date, rival mentioned neutrally, both authoritative, missing timestamp, incidental change word, negated both-stand;
  - 1 unsupported category (12 items, abstain).
  - By basis: temporal record time (update, three-value chain, historical); validity time (same import, back-filled, as-of); explicit corrections (same-day with and without a reference to the old value, later supersession); negative and modal (negated replacement, retention, unconfirmed, hypothetical, quoted claim); conflicts (plain, same validity date, rival mentioned neutrally, both authoritative, missing timestamp, incidental change word); controls (single record, unsupported).

**Known data limitation (16 Nov):** the v2 writer prompt requires each record's own value verbatim, with date values in `YYYY-MM-DD` form, so that mechanical validation does not reject correct long-form dates (6 of the 11 p2val exclusions were such false negatives, `data/p2val/P2VAL_EXCLUSION_REVIEW.md`). eval3 therefore does not test long-form value dates. Validity dates (not values) may still be written in any form.

**Template overlap with development data, documented:**
- The **question templates** for current-state questions are the memlab templates, shared with every split.
- The **distractor texts** use the memlab templates.
- **Record texts and historical questions are written fresh** by the writer model. They are not drawn from any development template.
- The **category semantics** overlap with development categories by design. They are what is being tested.
- **One category is excluded:** a tie broken only by source authority, because its gold depends on a convention the agent's prompt does not state.

## 4. Ground truth and validation

- **Gold is fixed by the skeleton before any text exists:** `answer:<value>` / `conflict` / `abstain`, plus a stale value where relevant.
- **Mechanical validation** (`assemble.py`): every text names its project and its own value; questions are present and contain no value. Items failing this are excluded (ids only are logged).
- **Blind double annotation** (`write_and_annotate.py annotate`): ANNOTATION_GUIDELINES.md §3; labels from text only.
- **Agreement** (`agreement.py`): Cohen's κ (three classes) and exact agreement of each annotator with gold.
- **Static generator audit before any text exists** (`audit_generators.py`, 16 Nov, counts only; `data/GENERATOR_AUDIT.json`): deterministic builds; 276/276 eval3 entities and all 92 lead surnames from eval3's own slice; 0 entity overlap with p2val, p2val2, dev, regression, p2dev; distractor slices disjoint from every entity slice and from each other; 0 duplicate entities; 0 gold/date/source fields and 0 label words in the writer input; 6 attributes × 46 items; 138 families × 2 items. 16 of eval3's 19 masked brief templates are shared with p2val2 (same generator, by design: p2val2 is a small sample of eval3's distribution).
- **Split-boundary and leakage checks** (`seal_checks.py`, inside the sealed job, counts only): name-pool uniqueness; every entity and distractor from its own slice; zero entity overlap with dev, regression, p2dev, p2val, p2val2; no duplicate entities; no gold fields or label words in the writer input; no gold/value/category fields in the annotator input; masked 8-gram template overlap and exact masked duplicates against all development texts (reported). The job's `eval3_SEAL_CHECKS.json` and `eval3_PROVENANCE.json` (generator code hashes, model snapshots, job id, `human_validation: none`) are sealed with the data.
- **Primary item set (revised 16 Nov before any eval3 output existed, `data/p2val2/PRIMARY_RULE_DECISION.md`): all mechanically valid items.** The double-agreement ids (`eval3_PRIMARY_IDS.json`, still produced by the sealed job) and the Qwen2.5-14B-agreed items are secondary sensitivity sets. Reason: on p2val2 the small blind annotators failed the temporal-reasoning categories wholesale, so double agreement would have removed the categories under test (`PREREGISTRATION.md` §5).

## 5. Protection

- **Sealed files:** skeleton, writer input, texts, groups, tasks, annotator input, annotations, agreement, primary ids, manifest. Read-only on the cluster, with `SHA256SUMS`.
- `FREEZE_eval3.json` in the repository holds the hashes, counts and agreement statistics, **and no content**.
- **The Phase 3 runner refuses** any eval3 task file whose sha256 differs from the frozen hash (`run_p2.py --expect-sha`).
- The skeleton generator is in the repository, so the *structure* is reproducible. The *texts* exist only in the sealed directory.
- Nothing in the eval3 directory is read by any Phase 2 script except the sealed build job itself.
