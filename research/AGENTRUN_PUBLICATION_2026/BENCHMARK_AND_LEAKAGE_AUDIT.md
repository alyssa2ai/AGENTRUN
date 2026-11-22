# Benchmark and leakage audit

**13 November 2026.** This audit covers every split used by either research thread. It records what each split can and cannot support.

## 1. Splits and what they are valid for

| Split | Size | Origin | Status now | Valid use |
|---|---|---|---|---|
| Legacy benchmark (`eval/tasks.py`) | 23 tasks | hand-written, thread 1 | The earlier 100% (V2 adapter) result is invalid as generalisation evidence: V2's 11 extra training trajectories were designed from V1's failures on these same 23 tasks (`docs/paper_agentrun_2.0.md`; `CORRECTIONS.md` item 8) | Historical diagnostic only. Not evidence of generalisation |
| Benchmark v2 dev (`benchmark_v2/dev.jsonl`) | 55 | generated (`bench-v2-gen-1.2`), thread 1 | Used for development and for the Campaign 2 base-vs-adapter re-runs | Development and diagnostics |
| Benchmark v2 sealed test (`.sealed/test.jsonl`) | 130 | same generator, sealed 2026-10-15 19:17 UTC | Never run, never displayed (see §3) | Confirmatory test **for thread 1 only** (tool-use fine-tuning). It has no memory scenarios, so it cannot test the memory paper |
| memlab dev (`benchmark/dev.jsonl`) | 12 | memlab generator | Used for building and debugging the harness | Development only |
| memlab eval (`benchmark/eval.jsonl`) | 48 | memlab generator, frozen before Campaign 1 | Campaign 1 results (1,440 local + 358 hosted runs) analysed and reported | Exploratory evidence |
| memlab eval2 (`benchmark/eval2.jsonl`) | 96 | memlab generator, seed 20261113, frozen 2026-11-12 04:54 UTC, sha256 `42552d7b…` | Campaign 2: 5,184 runs, analysed in depth, numbers in the MITACS dossier | **Validation / comparison set from now on.** When it was run it was a clean held-out set: frozen before any eval2 run, harness v2 developed on the 12 dev tasks only, nothing changed after results were seen (`CORRECTIONS.md` item 7). But its results have since been examined in depth (decompositions, failure analysis, this audit), and every next design decision will be informed by them, so it can no longer serve as an untouched final test |

There is **no untouched test set for the memory paper.** A new sealed memlab split is required before any claim is called confirmatory (see `EXPERIMENT_ROADMAP.md`, E1).

## 2. eval2 leakage audit (re-run 13 Nov 2026 with full store coverage)

Command: `py -3.11 scripts/leakage_audit.py` (log: `research/AGENTRUN_DEEPENING_2026-11-11/logs/leakage_audit_eval2_with_stores.log`; output: `tables/leakage_audit_eval2.json`).

Result: **77 PASS, 13 INFO** (run counts and a store hash), **0 FAIL**.

### Static checks on the benchmark (17 checks, all pass)

- **Freeze integrity.**
  - The file hash equals `FREEZE_eval2.json`.
  - The prompts and the harness variants match the freeze.
  - eval2 regenerates byte-identically from its seed.
- **Split separation.**
  - Entities are disjoint between dev and eval (664 entities checked).
  - eval2's entities and prompts are disjoint from the first eval split.
  - Person names are disjoint between dev and eval.
  - No entity is shared between two eval2 tasks.
- **Answer leakage.**
  - No expected value appears in any prompt, the system prompt or a tool schema.
  - No eval entity appears in the system prompt or schemas.
- **Contamination from other corpora.**
  - No eval2 entity name occurs in the training data (`training/training_data*.jsonl`), the legacy tasks, benchmark v2 dev, the v2 environment corpus or the real memory store.
  - There is no exact or template match with the 69 training and legacy prompts; the maximum TF-IDF similarity is 0.142, against a flag threshold of 0.80.
- **Fixture consistency.** Every scenario's fixtures agree with its expected outcome.

### Run-level checks (6 per dataset, 10 unpadded + 2 padded datasets)

- **No ground-truth field in any message the model saw.**
- **Configuration separation.** Provenance and reliability fields appear only in the configurations that are meant to have them (D, E).
- **Stateless baseline is clean.** It never received memory, and its tools never returned a memory-only answer.
- **Store isolation.** Each memory store holds exactly its own task's records.

**Coverage fix.** Before this session, the store-isolation check was skipped silently for the 1.5B, 3B and 14B runs, because their store files had not been copied to the laptop. They now are, and the check passes for all ten unpadded runs. For the padded runs, the check validates the store records that the harness reconstructs deterministically.

**Conclusion.** No evidence of train/test leakage, answer leakage or cross-configuration leakage in Campaign 2.

## 3. Was the 130-task sealed set accessed or contaminated?

Evidence collected this session:

1. **Every Claude session transcript for this project was searched** for reads of `.sealed/`, `test.jsonl`, `SECRET_seed` and `--tasks` pointing at the sealed file.
   - The only access was by the previous session (13 Nov). It counted the lines and listed the JSON field names of the first record; no task content was printed.
   - No run script was ever given the sealed file. No result folder for it exists locally or in the cluster workspace listing.
2. **Hashes** of the sealed files still match `benchmark_v2/SEAL.json` (`seal.py verify` logic).
3. **Custody risk.** `.sealed/` lives inside the repository working tree (git-ignored, never committed), even though `docs/benchmark_v2.md` says it must be kept outside the repository. Any tool that indexes or searches the working tree (an IDE, an agent with grep, a backup) can read it.

**Verdict.** Not accessed in any way that exposes task content, and not used for any experiment. It remains usable as a confirmatory test for the fine-tuning thread, provided it is moved outside the repository before more automated work happens there. It is **not** a test set for the memory study.

## 4. Construct validity of the memlab benchmark (risks a reviewer will raise)

1. **Memory is structured and synthetic.** Each record carries `entity`, `attribute`, `value`, `recorded_on`, `source` and `record_id`. The gate (configuration E) uses the `recorded_on` and `attribute` fields directly.
   - Real agent memories are usually free text written by the agent, with missing or unreliable timestamps.
   - The gate's advantage is therefore an upper bound for clean metadata. A free-text or agent-written memory variant is needed (roadmap E3).
2. **Templated tasks.** Tasks come from a small number of templates per scenario (22 scenario-variant families). Effects cluster by family (see `STATISTICAL_AUDIT.md`).
3. **Same generator family for dev, eval and eval2.** The splits are entity-disjoint but not template-disjoint. Generalisation to unseen templates is untested. A held-out-template split would test it.
4. **Scenario mix chosen by the designer.** Six equal-sized scenarios, so pooled effects depend on that mix. Report per-scenario results.
5. **Retrieval stress is synthetic.** The 2,000 padding records are generated distractors, and the hash retriever is deliberately weak. Real corpora (e.g., LoCoMo-style conversation logs) would give different numbers.
6. **No external benchmark.** All memory evidence is on memlab. Closely related public benchmarks exist (STALE, MemoryAgentBench, LoCoMo, ENT-310 from DISCERN; see `RELATED_WORK_AND_NOVELTY.md`). At least one should be used (roadmap E4).
7. **Scorer.** Deterministic, with rules for answer tolerance and abstention phrasing. Previous sessions spot-checked it. One known scorer issue: an `answer` status with an empty value is counted as harmful (15 of 3B's 24 harmful outcomes under v1, 20 of 37 under v2; `CORRECTIONS.md` item 6). No human annotation of a random sample of runs yet (roadmap E6).

## 5. Thread-1 benchmark notes (for completeness)

- **The 23-task 100% result** came from an adapter whose added training trajectories were designed from failures on the same 23 tasks (evaluation adaptation). It is invalid as generalisation evidence and must not be cited as such.
- **The client-matched re-run in Campaign 2.** The adapter scores 23/23 on the legacy tasks across five runs. The base model scores 21–22/23 over five runs; at budget 3, greedy, it scores 21/23. On benchmark v2 dev the two models are tied (adapter 51/55 at both budgets; base 51/55 at budget 3 and 52/55 at budget 6).
  - This supports the thread-1 conclusion that the earlier gap was mostly an evaluation-client artefact.
  - It is still not a test-set result.
