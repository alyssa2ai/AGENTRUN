# Environment

## Hardware
- One compute node with 2 × NVIDIA L40 (48 GB; 44.6 GiB visible to PyTorch before the host reboot of 2026-11-20, 44.4 GiB after it — see "Platform transition during the campaign" below), 96 CPU threads, ~500 GB RAM, Slurm with GPU gres (`--gres=gpu:1`; devices assigned per job through `CUDA_VISIBLE_DEVICES`).
- Each experiment cell uses one GPU, 4 CPUs and 48 GB RAM. The analysis is CPU-only; the finalization job that produced the reported numbers ran with 2 CPUs and 6 GB (measured peak well under that).
- Measured peak VRAM in bf16 (Phase 2): Qwen2.5-3B 5.9 GiB, Llama-3.1-8B 15.5 GiB. Qwen2.5-7B ≈ 16 GiB and Qwen2.5-14B ≈ 30 GiB are weight sizes, not measured peaks.

## Software (recorded in every run manifest)
| Component | Version |
|---|---|
| OS | Ubuntu 24.04.3 LTS, Linux 6.8 |
| Python | 3.12.3 (system Python, virtual environment; no conda, no module system) |
| CUDA (PyTorch build) | 13.2 |
| torch | 2.15.0+cu132 |
| transformers | 5.22.2 |
| accelerate / tokenizers / safetensors / huggingface_hub | 1.15.0 / 0.23.3 / 0.8.0 / 2.4.0 |
| numpy | 2.5.4 |

Pinned list: `requirements-hpc.txt`. For most of the campaign `nvidia-smi` did not work on the node: the NVIDIA userspace libraries had been upgraded while the node stayed up, leaving them mismatched against the running kernel module. CUDA worked through PyTorch throughout. The mismatch was resolved by the host reboot of 2026-11-20 (below). GPU identity is taken from `torch.cuda.get_device_name` and is recorded in each manifest.

## Offline model loading
Jobs set `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` and load cached snapshot directories. Lookup by model id failed offline on the cluster. Download the snapshots in `MODELS.md` first.

## Determinism
- Greedy cells use base seed 20261111. T = 0.7 cells use seeds 1, 2 and 3 (`run_p2.py --seed`).
- GPU kernels are not bitwise deterministic across hardware or library versions. A re-run on other hardware may differ at the token level for some runs. The analysis is reproducible byte for byte from the raw outputs, with seeded permutations (seed 0) and seeded bootstrap (seed 1 in `analyze_p2.py`, seed 3 in `phase3_metrics.py`).
- A resumed cell continues with a **fresh sampler state** for the remaining pairs: the client calls `torch.manual_seed(seed)` once per process, and a resume is a new process, so the post-resume segment restarts the sampling stream rather than continuing it. This does not bias the sampling distribution — the design fixes T = 0.7 with seeds 1, 2 and 3 and makes no claim about stream continuity — but reproducing such a cell byte for byte requires reproducing the interruption at the same row. In this campaign exactly one sampled cell was resumed, `qwen3_8b_T07_s3`, at row 2345 of 3216; the other resumed cell, `llama32_3b_greedy`, is greedy and has no sampling stream. Every start is recorded as a separate line in `manifest.jsonl`.

## Platform transition during the campaign

The compute node rebooted at 2026-11-20T10:11:58, between the start and the finish of two of the eighteen cells.

| | Before | After | Status |
|---|---|---|---|
| Linux kernel | `6.8.0-139-generic` | `6.8.0-149-generic` | after: verified; before: inferred |
| NVIDIA kernel driver | `580.173.02` | `580.178.04` | after: verified; before: inferred |
| Device memory seen by PyTorch | 44.6 GiB | 44.4 GiB | verified (recorded in the manifests) |
| torch / transformers / CUDA runtime | `2.15.0+cu132` / `5.22.2` / `13.2` | unchanged | verified |
| The 14 frozen mechanism and harness files | identical | identical | verified |

The affected cells are `qwen3_8b_T07_s3` (871 of 3216 rows after the reboot) and `llama32_3b_greedy` (109 of 3216);
980 of 57,888 rows campaign-wide, or 1.69%. A reproduction attempt on a single, fixed driver version is therefore
*not* expected to reproduce those two cells row for row. Full account: `PHASE3/PHASE3_DEVIATIONS.md` (D1, D2) and
`PHASE3/PHASE3_PLATFORM_CONTINUITY.md`, which separates verified, inferred and unknown facts.

## Post-campaign environment change

`pytest` was installed into the campaign virtual environment on 2026-11-21, after all 18 cells were complete and
sealed, so that the test suites could be run on the cluster. No GPU run followed. `torch`, `transformers` and every
other package the campaign depended on are unchanged, and the 14 frozen code hashes still verify.

