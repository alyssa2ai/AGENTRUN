# AGENTRUN persistent-memory reliability study: reproducibility package

This package documents how to reproduce the preregistered Phase 3 evaluation of **evidence-basis arbitration with gated enforcement (Evarb-0.2)** for small open-weight tool-using agents with persistent memory, and every table in the manuscript (`../manuscript/`).

It covers only the persistent-memory reliability study. The earlier QLoRA specialization study in the same repository (`publication/antic2026_submission/`, `notebooks/`, V1/E4) is a separate piece of work and is not part of this package.

## Contents

| File | What it documents |
|---|---|
| `ENVIRONMENT.md` | hardware, OS, Python, CUDA and package versions; `requirements-hpc.txt` |
| `MODELS.md` | model identifiers, Hugging Face snapshot hashes, decoding and generation settings |
| `DATASET.md` | the sealed eval3 benchmark, development splits, what can and cannot be shared |
| `EXECUTION.md` | running the 18-cell campaign under Slurm (runner, controller, recovery, finalization) |
| `ANALYSIS.md` | the preregistered statistics and how to regenerate every reported table from raw outputs |
| `EXPECTED_OUTPUTS.md` | directory layout, row counts and file formats of raw and analysis outputs |
| `TESTS.md` | test suites and what they cover |
| `LIMITATIONS_AND_FAILURE_MODES.md` | known failure modes of the mechanism, data and execution |
| `DEVIATIONS.md` | pointer to the Phase 3 deviation ledger: the host platform transition, the resume recovery, the re-seeding limitation and the integrity-gate correction |
| `configs/` | frozen manifests (`FREEZE_evarb.json`, `FREEZE_eval3.json`), `PREREGISTRATION.md`, primary-set decision record (byte copies) |
| `slurm/` | Slurm scripts used for Phase 3 (`phase3_finalize.sbatch` with host identifiers redacted) |
| `scripts/` | Phase 3 analysis scripts (copies; `run_phase3_analysis.sh` with host identifiers redacted) |
| `SHA256SUMS` | hashes of every file in this package; `SHA256SUMS_SOURCES` hashes of the originals in the repository |

The frozen mechanism and runner live in `research/AGENTRUN_PUBLICATION_2026/PHASE2/` (`evarb/`, `scripts/run_p2.py`, `scripts/analyze_p2.py`, `memlab.py`, `hf_client.py`, `rcs.py`, `tea.py`). Their hashes are in `configs/FREEZE_evarb.json` and in every run manifest.

## Shareable and restricted artifacts

| Artifact | Status | Reason |
|---|---|---|
| Code (mechanism, harness, runner, analysis, tests), frozen manifests, preregistration | shareable with the repository | written for this study |
| Aggregate results (`PHASE3/ANALYSIS/*.json`, `PHASE3/results/*.csv`, `PHASE3_*` reports) | shareable | counts, rates and statistics only |
| Development splits (p1dev … p2val2) and their runs | shareable with the repository | synthetic, generated for this study |
| **eval3** task file, texts, skeleton, annotations, per-run transcripts | **restricted** (kept on the cluster and in gitignored directories) | confirmatory test set. Release it only after the paper is accepted, with the authors' agreement. Texts were written by Qwen2.5-14B-Instruct, so the Qwen licence terms on model outputs apply |
| Model weights | **not redistributed** | obtain from Hugging Face under each model's licence (Qwen licence; Llama 3.1/3.2 Community Licence); exact snapshots in `MODELS.md` |
| Cluster logs | restricted | contain per-run outcome lines keyed by eval3 task id |

No credentials, tokens, API keys or private infrastructure details are included. Commands use `<user>@<cluster-login>` and `$HOME/AGENTRUN_HPC` as placeholders.

## Quick start (reproducing the tables from raw outputs)

```bash
cd research/AGENTRUN_PUBLICATION_2026/PHASE3
# raw cells in RAW_RESULTS/eval3_<model>_<decoding>/ and the sealed task file in SEALED_LOCAL/ (restricted; see DATASET.md)
bash scripts/run_phase3_analysis.sh verify
bash scripts/run_phase3_analysis.sh analyze   # frozen analyze_p2.py, 100,000 seeded permutations
bash scripts/run_phase3_analysis.sh report    # independent cross-check + PHASE3_* tables and CSVs
```

Without the restricted data, the same pipeline runs on the shareable p2val2 development runs: `DRY=1 bash scripts/run_phase3_analysis.sh verify|analyze|report`. That run reproduces `PHASE3/ANALYSIS/DRYRUN/` byte for byte; this was checked on 18 Nov 2026.
