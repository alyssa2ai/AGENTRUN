# Implementation report (Phase 2)

**16 November 2026.** What was built, how it is checked, and what is frozen. Architecture: `SYSTEM_ARCHITECTURE.md`. Behaviour: `EVIDENCE_ARBITRATION_SPEC.md`.

## 1. Code

| Area | Files | Lines | Status |
|---|---|---|---|
| Mechanism (evarb) | `evarb/cues.py`, `arbiter.py`, `policy.py`, `render.py`, `loop.py` | 878 | **frozen, evarb-0.2** |
| LLM evidence-arbiter baseline | `evarb/llm_arbiter.py` | 111 | frozen with the mechanism |
| Model-family adapter (Llama-3.x tool calls) | `evarb/clients.py` | 118 | frozen with the mechanism |
| Runner, analysis | `scripts/run_p2.py`, `analyze_p2.py`, `component_eval.py` | 567 | frozen (hashes in `FREEZE_evarb.json`) |
| Benchmark generation | `benchmark/skeleton.py`, `write_and_annotate.py`, `assemble.py`, `agreement.py` | 630 | used for p2val, p2val2, eval3 |
| Added 16 Nov (not part of the mechanism) | `benchmark/seal_checks.py`, `audit_generators.py`, `scripts/component_report.py`, `power_phase3.py`, `budget_phase3.py`, `dryrun_pipeline.py`, `subset_tasks.py`, `write_freeze_eval3.py`, `finish_phase2.sh` | 1,046 | analysis / integrity tools; import the frozen code without changing it |
| Development fixtures | `fixtures/build_dev.py` | 378 | development data |
| Tests | `tests/` (8 files) | 92 tests | all pass |
| HPC | `hpc/*.sbatch`, `hpc/COORDINATION.md` | 6 scripts | one GPU each, resumable |

Frozen dependencies, never edited (hash-checked by every run manifest): `memlab.py` (harness, prompts, scorer), `hf_client.py`, Phase 1 `rcs.py` and `tea.py`.

## 2. Freeze

`FREEZE_evarb.json`: evarb-0.2, frozen 2026-11-14T08:14:16Z, 12 files plus 3 frozen dependencies. Verified on 16 November:
- locally: 12/12 files and 3/3 dependencies match;
- on the cluster copy, after syncing the source tree (pre-sync backup at `~/AGENTRUN_HPC/backups/phase2_pre_sync_20261116/`): 12/12 files match, dependencies match;
- every Phase 2 / Phase 3 sbatch file that can touch eval3 refuses to start on a mismatch.

The change history (0.1 → 0.2) and the reason p2val became development data are in `FREEZE_evarb.json["history"]` and `EVIDENCE_ARBITRATION_SPEC.md` §0. **No mechanism file was changed in this session.**

## 3. Tests (92, all passing)

| File | Tests | Covers |
|---|---|---|
| `test_arbiter.py` | 17 (+ parametrised cases) | bases, linguistic safeguards, negation scope, validity/ordinal dates, doubt guard, cycles, ties |
| `test_policy_and_loop.py` | 13 (+ parametrised) | intent, P1–P4, enforcement gating, notices, safe submission, Phase 1 config dispatch (mock client) |
| `test_regression_phase1.py` | 6 (+ parametrised) | every Phase 1 failure family, split hashes |
| `test_clients.py` | 6 | Llama JSON / python_tag / multi-call parsing; Qwen no-op |
| `test_analysis.py` | 4 | pairing within task and decoding, exact sign-flip, Holm/BH, bootstrap |
| `test_phase2_tools.py` | 7 | seal checks (pass, detect an injected gold leak); generator audit; end-to-end dry run of loop + analysis; primary subset; paired/Holm; power simulation |
| `test_known_limitations.py` | 3 | the long-range negation failure of the frozen evarb-0.2, pinned |

Map of required edge cases to tests: `NEGATION_AND_CONFLICT_TESTS.md`.

## 4. Data produced and verified in Phase 2

| Data | Where | Integrity |
|---|---|---|
| Development fixtures (114 groups, 80 tasks, 46 regression groups) | `data/` | `DEV_MANIFEST.json` |
| p2val (88 skeleton, 77 valid) | `data/p2val/` | `p2val_MANIFEST.json`; local files hash-identical to the cluster copies |
| LLM-arbiter predictions, 4 models × 230 groups (job 4189) | `raw/llm_arbiter/` | sha256 identical to the cluster |
| p2val2, eval3, agent-level runs | see `PHASE2_STATUS.md` | |

## 5. Known limitations of the implementation

- Negation scope is a 4-token window; long-range negation can produce a strong false correction (demonstrated in `NEGATION_AND_CONFLICT_TESTS.md` §4).
- Cue lists are English and lexical. Paraphrases outside the lists fall back to time order (strong unless the doubt guard fires).
- The LLM arbiter uses the agent's own model (LA/LG). A stronger external arbiter is not part of the frozen design.
- Latency in run records is wall time on a shared node; it is comparable only between runs of the same job.
