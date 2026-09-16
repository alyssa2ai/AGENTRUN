# E4 Experiment: V1 Adapter + Fixed Parser

## What this isolates

E4 evaluates the **V1 LoRA adapter** (trained on 35 trajectories) using the **V2 two-pass parser**. This isolates the parser fix from the training data augmentation:

- **V1 result (18/23 = 78.3%)**: V1 adapter + V1 single-pass parser
- **E4 result (?)**: V1 adapter + V2 two-pass parser
- **V2 result (23/23 = 100.0%)**: V2 adapter (46 trajectories) + V2 two-pass parser

From E4, we can decompose the v1→v2 improvement:
- **Parser effect** = E4 score − V1 score
- **Data effect** = V2 score − E4 score

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
| `results/eval_results_e4.json` | Machine-readable results (23 tasks) |
| `results/eval_report_e4.md` | Human-readable report |

## Interpretation guide

After getting the E4 score, compare against:

| Experiment | Score | What changed |
|------------|-------|--------------|
| Base | 22/23 = 95.7% | No fine-tuning, V1 parser |
| V1 | 18/23 = 78.3% | V1 adapter + V1 parser |
| **E4** | **?** | V1 adapter + V2 parser |
| V2 | 23/23 = 100.0% | V2 adapter + V2 parser |

**If E4 ≈ V1 (18/23):** The parser fix had minimal impact. The regression was primarily due to training data.

**If E4 >> V1 (e.g., 21/23):** The parser fix was a major factor. The V1 regression was partly a parser artifact.

**If E4 ≈ V2 (23/23):** The parser fix alone recovered the full regression. Training data augmentation had no additional benefit.

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
Pass 2 only recovers tool calls with **flat arguments** (empty `{}` or no nesting). For nested args like `{"arguments": {"query": "..."}}`, the regex stops at the first `}` and produces invalid JSON. However, most v1 failures involved `word_count` with empty args, which Pass 2 handles correctly.
