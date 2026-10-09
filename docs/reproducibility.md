# Reproducibility Guide

This document describes how to reproduce the AgentLab QLoRA distillation experiment from scratch.

---

## 1. Environment Assumptions

### Hardware

- **Training:** Google Colab free-tier T4 GPU (15GB VRAM, 4-bit NF4 quantization required)
- **Local evaluation:** Any machine with Python 3.10+ (no GPU required for the eval client)
- **Colab server:** T4 GPU required for inference; Qwen 7B base + 4-bit LoRA fits on T4 VRAM

### Software

- Python 3.10 or 3.11
- See `requirements.txt` at the project root
- For Colab training/serving, packages are installed inside the notebook cells (no local install needed for the Colab-side scripts)

---

## 2. What needs what

The repository layout is described in [`project-map.md`](project-map.md).

| Activity | Hardware | External services / credentials | Command |
|---|---|---|---|
| Unit, scoring and result-consistency tests | CPU | none | `python -m pip install -r requirements-dev.txt && python -m pytest` |
| Recompute every reported score from committed results | CPU | none | `python results/verify_results.py` |
| Regenerate both training sets | CPU | none | Step 2 below (verified byte-identical, 2026-10-09) |
| Train V1 / V2 adapters | Colab T4 (15 GB) | Hugging Face model download | Steps 3–4 |
| Serve a condition | Colab T4 | ngrok authtoken | Step 5 |
| Run the 23-task benchmark | CPU (local client) | live server URL, `TAVILY_API_KEY`, internet (Open-Meteo) | Steps 6–7 |
| Phase 1 Gemini agent (not part of the four conditions) | CPU | `GEMINI_API_KEY`, `TAVILY_API_KEY` | `python main.py` |

Having a command for a step does not mean that step was re-run during the
repository clean-up. The executed experiments are the four conditions recorded
in `results/` and `docs/experiment-log.md`. E5, E7 and E8 are proposals and
have not been run.

---

## 3. Reproduction Steps

### Step 1: Local environment

```bash
git clone https://github.com/alyssa2ai/AGENTRUN.git
cd AGENTRUN
python -m venv .venv
source .venv/bin/activate   # or: .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

For the Phase 1 frontier-agent path, copy `.env.example` to `.env` and fill in `GEMINI_API_KEY` and `TAVILY_API_KEY`. **Never commit `.env`.**

### Step 2: Reproduce the training data (optional)

The training data JSONLs are already committed (`training/training_data.jsonl`, `training/training_data_augmented.jsonl`). To regenerate from scratch:

```bash
cd training
python generate_dataset.py            # writes training_data.jsonl (35 trajectories)
python augment_training_data.py       # writes training_data_augmented.jsonl (46) and training_data_prompts_augmented.py
```

Both scripts build trajectories from hard-coded tool calls and answers. They make
no model or API calls. On 2026-10-09 both outputs were regenerated in a scratch
directory, and the JSONL files matched the committed files byte for byte. The
older `generate_training_data.py` is the Gemini-driven generator. It needs
`GEMINI_API_KEY`, is not deterministic, and is not the source of the committed sets.

### Step 3: Train v1 LoRA on Colab

1. Open Google Colab, set runtime to T4 GPU
2. Upload `training/training_data.jsonl` to Colab
3. Open `training/colab_train_7b.py`, paste cells, run
4. Output: `/content/agentlab_qwen_lora_7b` (LoRA adapter)
5. **Back this up locally** — the `/content/` filesystem is volatile

### Step 4: Train v2 LoRA on Colab

1. Open Google Colab, set runtime to T4 GPU
2. Upload `training/training_data_augmented.jsonl` to Colab
3. Open `training/colab_train_7b_v2.py`, paste cells, run
4. Output: `/content/agentlab_qwen_lora_7b_v2` (LoRA adapter)

### Step 5: Run the Colab inference server

1. With the trained adapter in `/content/agentlab_qwen_lora_7b_v2`, open `serving/colab_server_v2.py`
2. Replace `NGROK_AUTH_TOKEN = "PASTE_YOUR_NGROK_TOKEN_HERE"` with your free ngrok authtoken from <https://dashboard.ngrok.com/get-started/your-authtoken>
3. Run the cells in order
4. Copy the printed public URL (e.g., `https://<random>.ngrok-free.app`)

### Step 6: Run the 23-task benchmark

```bash
# Set the ngrok URL on your local machine
export COLAB_SERVER_URL_V2=https://....ngrok.io   # Mac/Linux
set COLAB_SERVER_URL_V2=https://....ngrok.io      # Windows

# Run from the project root
python evaluation/run_eval_v2.py
```

Expected output:
- `results/eval_results_v2.json` — machine-readable results
- `results/eval_report_v2.md` — human-readable report
- 23/23 = 100.0% pass rate

### Step 7: Run E4 (controlled parser ablation)

E4 runs the V1 adapter behind the V2 two-pass parser. Following the steps below, with `evaluation/run_eval_e4.py`, gives a **client-matched** E4 that changes only the parser. That run has not been performed. The reported E4 (18/23) was produced by a notebook-local loop with a different tool stack; see `docs/e4-experiment-guide.md`.

1. Upload the V1 adapter (`agentlab_qwen_lora_7b/`) to Colab (same as Step 3).
2. Run `serving/colab_server_e4.py` in Colab (T4 GPU) — this server uses the V2 two-pass parser but loads the V1 adapter.
3. Copy the printed ngrok URL.
4. Run the benchmark locally:

```bash
export COLAB_SERVER_URL_E4=https://....ngrok.io
python evaluation/run_eval_e4.py
```

Expected outputs:
- `results/eval_results_e4.json` — machine-readable results (18/23 = 78.3%)
- `results/eval_report_e4.md` — human-readable report

### Step 8: Generate a comparison report

```bash
python evaluation/compare_results.py results/eval_results_base.json results/eval_results_v2.json \
    --label-a "Base Qwen 7B" --label-b "LoRA v2" \
    --output results/eval_comparison_report.md
```

The `compare_results.py` script is model-agnostic: it reads labels from the JSON metadata and accepts explicit overrides.

---

## 4. LoRA Training Configuration (v1 and v2)

Every LoRA and data hyperparameter is shared between the two runs:

| Hyperparameter | Value |
|---|---|
| Base model | Qwen/Qwen2.5-7B-Instruct |
| Quantization | 4-bit NF4, fp16 compute |
| LoRA rank | 16 |
| LoRA alpha | 16 |
| LoRA target modules | q_proj, k_proj, v_proj, o_proj |
| Learning rate | 2e-4 |
| Batch size | 2 (with grad accumulation 4, effective batch size 8) |
| Epochs | 3 |
| Max seq length | 1024 |

Three memory-related settings are **not** shared. The 46-trajectory run had to
fit the same 15 GB T4 budget, so `training/colab_train_7b_v2.py` adds them and
`training/colab_train_7b.py` does not:

| Setting | V1 (`colab_train_7b.py`) | V2 (`colab_train_7b_v2.py`) |
|---|---|---|
| Optimizer | Trainer default (script sets none) | `bnb.optim.PagedAdamW8bit`, passed via `optimizers=(optim_8bit, None)` |
| Gradient checkpointing | off | on, `use_reentrant=False` |
| KV cache (`use_cache`) | on | off |

This difference does not enter the V1→E4 comparison, because E4 reuses the V1 adapter. It does mean the E4→V2 comparison changes the adapter, the training
data, and these optimizer settings together, so the +5 difference should not be
read as an isolated effect of the 11 added trajectories. If you retrain V2
without these memory settings, say so when reporting the result.

Source: `training/colab_train_7b.py` and `training/colab_train_7b_v2.py`. The stored adapter_config.json confirms:
```json
{
  "lora_alpha": 16,
  "r": 16,
  "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"]
}
```

---

## 5. Benchmark Specificity

**All claims of pass rate in this repository are tied to this specific 23-task held-out set in `eval/tasks.py`.** Generalization beyond this benchmark is not implied.

| Score | Conditions |
|---|---|
| 22/23 (Base) | max_steps=3, 4-bit NF4, greedy decoding, original parser |
| 18/23 (v1)   | max_steps=3, 4-bit NF4, greedy decoding, original parser |
| 18/23 (E4)   | max_steps=3, 4-bit NF4, greedy decoding, corrected parser (V1 adapter) |
| 23/23 (v2)   | max_steps=3, 4-bit NF4, greedy decoding, corrected parser (V2 adapter) |

Parser aggregate effect (E4 − V1): 0 tasks.  
Data augmentation effect (V2 − E4): +5 tasks (adapter + data + optimizer settings change together; see §4).

Changing any of the following invalidates comparison: benchmark tasks, max_steps, generation mode, parser, base model.

### Verify the reported numbers

Every score in this repository can be recomputed from the committed result
files:

```bash
python results/verify_results.py
```

This re-tallies each condition's pass count, checks that the 23 task IDs are
identical across Base/V1/E4/V2, lists every per-task transition for V1→E4 and
E4→V2, and rewrites `RESULTS_VERIFIED.md`,
`results/results_verified.json`, and `results/results_verified.csv`. It reads
only committed artifacts; it does not re-run the model.

## 6. Random Seeds & Determinism

No random seeds were set in the training scripts (`colab_train_7b.py`, `colab_train_7b_v2.py`) or evaluation scripts (`run_eval_base.py`, `run_eval_finetuned.py`, `run_eval_v2.py`, `run_eval_e4.py`). As a result:

- **Training seed**: NOT SET / UNKNOWN — the QLoRA trainer's random number generation was not explicitly seeded. Model initialization (base weights), dataset shuffling, and weight initialization all used default behavior.
- **Eval seed**: NOT SET / UNKNOWN — the evaluation harness uses greedy decoding (`do_sample=False`), which is deterministic given the same model output. However, model generation without an explicit seed may have non-determinism from CUDA operations on GPU.

**For future reproducibility:** Set `torch.manual_seed(seed)` and `random.seed(seed)` before training/eval, and log the seed value. When using 4-bit NF4 quantization on Colab T4, also consider that CUDA non-determinism can affect reproducibility even with the same seed.

---

## 7. Security Precautions

**Before pushing to GitHub:**

1. Verify `.gitignore` is in place (it is at the project root)
2. **Never** commit:
   - `.env` files with real API keys
   - `*.safetensors` (LoRA weights — too large and not version-controlled)
   - `checkpoint-*/` directories
   - `agentlab_qwen_lora*/` directories (local adapter copies)
   - `tokenizer.json` (re-downloadable from HuggingFace)
   - `memory_store.json` (contains user-specific data)
3. If a real API key is accidentally committed:
   - **Immediately rotate the key** (revoke it at the provider's dashboard)
   - Remove the key from the file
   - Use `git filter-branch` or BFG Repo-Cleaner to remove from history
4. The `.env.example` file contains placeholders only — safe to commit

---

## 8. Expected Artifact Files

After a successful end-to-end reproduction, you should have:

| File | Source |
|---|---|
| `agentlab_qwen_lora_7b/` (local backup) | v1 training output |
| `agentlab_qwen_lora_7b_v2/` (local backup) | v2 training output |
| `results/eval_results_base.json` | `evaluation/run_eval_base.py` |
| `results/eval_results_v1.json` | `evaluation/run_eval_finetuned.py` |
| `results/eval_results_e4.json` | `evaluation/run_eval_e4.py` |
| `results/eval_results_v2.json` | `evaluation/run_eval_v2.py` |
| `results/eval_report_*.md` | (same scripts) |
| `results/eval_comparison_report.md` | `evaluation/compare_results.py` |
| `RESULTS_VERIFIED.md` | `results/verify_results.py` |

The V1 adapter directory produced by `training/colab_train_7b.py` is
`/content/agentlab_qwen_lora_7b` on Colab; back it up locally, since
`/content/` is volatile. The legacy `agentlab_qwen_lora/` name refers to an
earlier 0.5B adapter from Phase 3 and is not produced by either of the two
training scripts above.

---

## 9. Differences from the original Phase 1 frontier-agent code

This repository contains both the Phase 1 frontier-agent code and the Phase 4–5 QLoRA distillation code. The two are decoupled:

- **Phase 1** is the `agent.py` + `providers/` + `mcp_server.py` infrastructure, originally built around Gemini. It still functions; it is not the subject of the published experiment.
- **Phase 4–5** is the QLoRA experiment (Base / v1 / v2) on Qwen 7B. This is what the README and results sections describe.

If you want to reproduce **only** the QLoRA experiment, the minimum needed is:
- `ft_agent.py` (local client)
- `eval/` (benchmark)
- `mcp_server.py` + `tools.py` + `providers/` (MCP infrastructure for tool execution)
- `training/training_data_*.jsonl` (training data)
- `training/colab_train_*.py` (training scripts)
- `serving/colab_server_*.py` (Colab servers)
- `evaluation/run_eval_*.py` + `compare_results.py` (eval pipeline)
