# Provenance — Hyperparameters

**Label: VERIFIED**

The LoRA and data hyperparameters below are identical for v1 and v2; the only
differences are the training-data file and three memory-related optimizer
settings that the v2 script adds. Source: `training/colab_train_7b.py`,
`training/colab_train_7b_v2.py`, and the committed `adapter_config.json`.

## Correction applied in Phase 1

`README.md` and `docs/reproducibility.md` previously disagreed on the training
hyperparameters. The audit resolved the discrepancy by inspecting the committed
`adapter_config.json`:

| Field | Old (README) | Old (reproducibility.md) | **Actual (adapter_config.json)** |
|---|---|---|---|
| `lora_alpha` | 32 | 32 | **16** |
| `target_modules` | q/k/v/o/gate/up/down | q/k/v/o/gate/up/down | **q/k/v/o only** |
| batch size | 1 | 1 | **2** |
| grad accum | 16 | 16 | **4** |

Both `README.md` and `docs/reproducibility.md` were corrected to match
`adapter_config.json`. The correction is recorded in
`results/experiment_summary.json` under `provenance.training_config`.

## Correction applied in Phase 7 (2026-10)

Earlier revisions of `README.md`, `docs/reproducibility.md`,
`docs/paper_agentrun_2.0.md`, `docs/experiment-log.md`, and
`publication/manuscript.tex` stated that v1 and v2 used *identical*
hyperparameters and listed the optimizer as `paged_adamw_8bit` for both. That
was wrong for v1. Reading the two training scripts:

| Setting | v1 `colab_train_7b.py` | v2 `colab_train_7b_v2.py` | Label |
|---|---|---|---|
| Optimizer | not set → `Trainer` default | `bnb.optim.PagedAdamW8bit`, passed as `optimizers=(optim_8bit, None)` | VERIFIED (source: scripts) |
| Gradient checkpointing | off | on (`use_reentrant=False`) | VERIFIED (source: scripts) |
| `model.config.use_cache` | left at default (on) | `False` | VERIFIED (source: scripts) |
| Gradient-checkpointing input grads | n/a | `enable_input_require_grads()` | VERIFIED (source: script) |
| Sequence-length argument | `max_seq_length=1024` | `max_length=1024` | VERIFIED (source: scripts); the v2 script notes `max_seq_length` is ignored in trl>=0.14, and the trl version used for the v1 run was not recorded |

The v2 script's own header comments record these additions. They were made so
the 46-trajectory run would fit the same 15 GB T4 budget. They do not affect
E4, which reuses the v1 adapter and varies only the parser, but they do mean
the E4→V2 contrast changes the training run and not only the training data.

## Full configuration (shared by v1 and v2)

| Hyperparameter | Value | Label |
|---|---|---|
| Base model | Qwen/Qwen2.5-7B-Instruct | VERIFIED |
| Quantization | 4-bit NF4, fp16 compute | VERIFIED |
| LoRA rank `r` | 16 | VERIFIED |
| LoRA alpha | 16 | VERIFIED |
| LoRA target modules | q_proj, k_proj, v_proj, o_proj | VERIFIED |
| LoRA dropout | 0.05 | VERIFIED |
| Learning rate | 2e-4 | VERIFIED |
| Per-device batch size | 2 | VERIFIED |
| Gradient accumulation | 4 | VERIFIED |
| Effective batch size | 8 | INFERRED (2 × 4) |
| Epochs | 3 | VERIFIED |
| Max sequence length | 1024 | VERIFIED (see caveat above) |
| Optimizer | see per-run table above | VERIFIED |
| Gradient checkpointing | see per-run table above | VERIFIED |

## Artifacts

- `adapter_config.json` — committed PEFT config (canonical source)
- `training/colab_train_7b.py` — v1 training script
- `training/colab_train_7b_v2.py` — v2 training script
- `training_args.bin` — Trainer state saved by a training run; not committed
  (`*.bin` is ignored) and not attributable to a specific run from the
  repository alone
- `docs/reproducibility.md` — human-readable mirror (corrected)