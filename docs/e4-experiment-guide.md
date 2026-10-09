# E4 Experiment: V1 Adapter + Fixed Parser

> **Outcome (recorded): E4 = 18/23 = 78.3%, identical to V1.** This document was
> written as an analysis protocol *before* the run; the pre-registered
> expectations are kept below under "Interpretation guide" for the record. The
> artifacts are `results/eval_results_e4.json`, `results/eval_report_e4.md`,
> and the per-task table in `RESULTS_VERIFIED.md`.

## What this isolates

E4 evaluates the **V1 LoRA adapter** (trained on 35 trajectories) using the **V2 two-pass parser**. This isolates the parser fix from the training data augmentation:

- **V1 result (18/23 = 78.3%)**: V1 adapter + V1 single-pass parser
- **E4 result (18/23 = 78.3%)**: V1 adapter + V2 two-pass parser
- **V2 result (23/23 = 100.0%)**: V2 adapter (46 trajectories) + V2 two-pass parser

From E4, we can decompose the v1→v2 improvement:
- **Parser effect** = E4 score − V1 score = 0 tasks
- **Remaining difference** = V2 score − E4 score = +5 tasks, which also changes the adapter's training run (data plus the optimizer and gradient-checkpointing settings in `training/colab_train_7b_v2.py`)

## Files created

| File | Purpose |
|------|---------|
| `serving/colab_server_e4.py` | Colab server: V1 adapter + V2 parser |
| `evaluation/run_eval_e4.py` | Local eval script for E4 |

## How to run E4 on Colab

### Step 1: Upload the V1 adapter

Download the V1 adapter from your backup (or re-download from HuggingFace if uploaded) and place it at:
```
/content/agentlab_qwen_lora_7b/
```

The directory should contain:
- `adapter_config.json`
- `adapter_model.safetensors`
- `tokenizer.json` (optional, will use base model's)
- `tokenizer_config.json` (optional)

**If you don't have the V1 adapter**, you must re-run the V1 training script (`training/colab_train_7b.py`) first.

### Step 2: Run the E4 server in Colab

1. Open Google Colab, set runtime to T4 GPU
2. Paste each cell from `serving/colab_server_e4.py` in order
3. Replace `NGROK_AUTH_TOKEN = "PASTE_YOUR_NGROK_TOKEN_HERE"` with your ngrok token
4. Run all cells
5. Copy the printed E4 SERVER URL

### Step 3: Run the E4 benchmark locally

```bash
export COLAB_SERVER_URL_E4=https://....ngrok.io
python evaluation/run_eval_e4.py
```

## Expected outputs

| File | Content |
|------|---------|
| `results/eval_results_e4.json` | Machine-readable results (23 tasks, 18 pass) |
| `results/eval_report_e4.md` | Human-readable report |

The committed `results/eval_results_e4.json` was produced by the Colab notebook
eval path, which recorded per-task pass/fail but not full traces, so its
`tool_calls`, `final_answer`, and `latency_seconds` fields are `null`. The
scoring script `evaluation/run_eval_e4.py` writes those fields when it is run
locally against a live server.

## Interpretation guide

The branches below were the pre-registered readings, written before the run.
They are kept for the record; the branch that applied was the first one.

| Experiment | Score | What changed |
|------------|-------|--------------|
| Base | 22/23 = 95.7% | No fine-tuning, V1 parser |
| V1 | 18/23 = 78.3% | V1 adapter + V1 parser |
| **E4** | **18/23 = 78.3%** | V1 adapter + V2 parser ← **observed** |
| V2 | 23/23 = 100.0% | V2 adapter + V2 parser |

**If E4 ≈ V1 (18/23)** *(observed)*: the parser fix produced no net aggregate change. Two tasks were recovered and two regressed, so the failure composition changed while the aggregate did not.

**If E4 >> V1 (e.g., 21/23):** the parser fix would have been a major factor and the V1 regression partly a parser artifact.

**If E4 ≈ V2 (23/23):** the parser fix alone would have recovered the full regression, and the training-data augmentation would have added nothing.

## Parser difference details

### V1 parser (single-pass)
```python
TOOL_CALL_PATTERN = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
```
Requires properly closed `` blocks. If the model emits `` without `</tool_call>`, returns empty tool_calls → treated as final answer.

### V2 parser (two-pass)
```python
# Pass 1: standard closed blocks
TOOL_CALL_CLOSED = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
# Pass 2: fallback — first JSON after any <tool_call> tag
TOOL_CALL_OPEN = re.compile(r"<tool_call>\s*(\{.*?\})", re.DOTALL)
```
Pass 1 tries strict matching. If that fails, Pass 2 recovers the first tool call from malformed output.

### Known limitation of Pass 2
Pass 2's regex `<tool_call>\s*(\{.*?\})` is non-greedy and stops at the **first** `}`, so it can only recover a tool call whose JSON contains no nested object at all. A call such as `{"name": "word_count", "arguments": {}}` is captured one closing brace short, `json.loads` fails inside the parser, and the output is treated as a final answer. Nested argument objects fail for the same reason. Pass 1 (strict closed-block) handles all of these correctly, so the limitation applies only to malformed output.

This behaviour is pinned by `test_parser_fixed.py`
(`test_v2_pass2_recovers_flat_args`,
`test_v2_pass2_empty_arguments_object_not_recovered`,
`test_v2_pass2_nested_args_also_fails`).
