# Environment

## Hardware
- One compute node with 2 × NVIDIA L40 (48 GB; 44.6 GiB visible to PyTorch), 96 CPU threads, ~500 GB RAM, Slurm with GPU gres (`--gres=gpu:1`; devices assigned per job through `CUDA_VISIBLE_DEVICES`).
- Each experiment cell uses one GPU, 4 CPUs and 48 GB RAM. The analysis is CPU-only (2 CPUs, 16 GB).
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

Pinned list: `requirements-hpc.txt`. `nvidia-smi` did not work on the node (driver/library mismatch), but CUDA worked through PyTorch. GPU identity is taken from `torch.cuda.get_device_name` and is recorded in each manifest.

## Offline model loading
Jobs set `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` and load cached snapshot directories. Lookup by model id failed offline on the cluster. Download the snapshots in `MODELS.md` first.

## Determinism
- Greedy cells use base seed 20261111. T = 0.7 cells use seeds 1, 2 and 3 (`run_p2.py --seed`).
- GPU kernels are not bitwise deterministic across hardware or library versions. A re-run on other hardware may differ at the token level for some runs. The analysis is reproducible byte for byte from the raw outputs, with seeded permutations (seed 0) and seeded bootstrap (seed 1 in `analyze_p2.py`, seed 3 in `phase3_metrics.py`).
- A resumed cell (after pre-emption) continues with a fresh sampler state for the remaining pairs. Every start is recorded as a separate line in `manifest.jsonl`.
