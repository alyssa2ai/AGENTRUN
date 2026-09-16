# Provenance — Hyperparameters

**Label: VERIFIED**

Both v1 and v2 used the identical QLoRA configuration. The only difference was the
training data file. Source: `training/colab_train_7b.py`,
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

## Full configuration

| Hyperparameter | Value | Label |
|---|---|---|
| Base model | Qwen/Qwen2.5-7B-Instruct | VERIFIED |
| Quantization | 4-bit NF4, fp16 compute | VERIFIED |
| LoRA rank `r` | 16 | VERIFIED |
| LoRA alpha | 16 | VERIFIED |
| LoRA target modules | q_proj, k_proj, v_proj, o_proj | VERIFIED |
| LoRA dropout | 0.05 | VERIFIED |
| Optimizer | paged_adamw_8bit | VERIFIED |
| Learning rate | 2e-4 | VERIFIED |
| Per-device batch size | 2 | VERIFIED |
| Gradient accumulation | 4 | VERIFIED |
| Effective batch size | 8 | INFERRED (2 × 4) |
| Epochs | 3 | VERIFIED |
| Max sequence length | 1024 | VERIFIED |

## Artifacts

- `adapter_config.json` — committed PEFT config (canonical source)
- `training/colab_train_7b.py` — v1 training script
- `training/colab_train_7b_v2.py` — v2 training script
- `docs/reproducibility.md` — human-readable mirror (corrected)