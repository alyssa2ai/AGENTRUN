# E4 Experiment: V1 Adapter + Fixed Parser

> **Outcome (recorded): E4 = 18/23 = 78.3%, identical to V1.** This document was
> written as an analysis protocol *before* the run; the pre-registered
> expectations are kept below under "Interpretation guide" for the record. The
> artifacts are `results/eval_results_e4.json`, `results/eval_report_e4.md`,
> and the per-task table in `RESULTS_VERIFIED.md`.

## What E4 did and did not hold constant

*Added 2026-10-09 after the notebook was re-read. This section supersedes the
"What this isolates" protocol below wherever the two disagree.*

E4 was intended to change only the serving-layer parser, as planned in the
protocol below. The protocol's runner, `evaluation/run_eval_e4.py` (which goes
through `ft_agent.py` and MCP), was **not** used for the reported score. The
18/23 comes from cell 16 of `notebooks/colab_e4_session.ipynb`, which runs its
own loop inside Colab.

| Factor | V1 (2026-09-01) | E4 (2026-09-16) | Held constant? |
|---|---|---|---|
| Base model, adapter weights, decoding | V1 adapter, greedy | same | yes |
| Server-side parser | single-pass | two-pass | no (intended change) |
| Tasks, `score_task`, `max_steps=3` | `eval/` | same files, imported in Colab | yes |
| Tool schemas sent to the model | MCP-derived, full descriptions | minimal ("Evaluate arithmetic") | **no** |
| Tool-call / tool-result serialization | `<tool_call>` text; provider-formatted strings | OpenAI-style `tool_calls`; `{"result": ...}` JSON | **no** |
| Tool implementations / error semantics | `tools.py` + providers via MCP; `ERROR` prefix = error | notebook functions; exception = error | **no** |
| Client-side text re-parse fallback | yes (`ft_agent.py`) | none | **no** |
| Live search/weather data | 2026-09-01 | 2026-09-16 | **no** |
| Traces recorded | full | pass/fail only | n/a |

Consequences:

- The unchanged aggregate (18 → 18) and the four task flips are what was
  observed under all of these changes together. They **cannot be attributed
  to the parser alone**.
- The V1 traces do not support the parser-drop explanations given earlier for
  the two "recovered" tasks. In V1, `multi_three_tools` called all three tools
  and failed on `hit_max_steps`, and `adversarial_false_premise` called
  `web_search` and failed the content check. The two "regressed" tasks passed
  in V1 with all required tools called. E4 recorded no traces, so the mechanism
  behind any of the flips is unknown.
- The same notebook also contains an E4 run without a working search key,
  which scored 13/23 because search calls errored. The reported 18/23 is the
  run with the key working.
- **A client-matched E4 has not been run.** It would mean serving
  `colab_server_e4.py` and running `python evaluation/run_eval_e4.py`. That is
  the experiment needed for a parser-only estimate.

## What this isolates (original protocol, pre-run)

E4 evaluates the **V1 LoRA adapter** (trained on 35 trajectories) using the **V2 two-pass parser**. This isolates the parser fix from the training data augmentation:

- **V1 result (18/23 = 78.3%)**: V1 adapter + V1 single-pass parser
- **E4 result (18/23 = 78.3%)**: V1 adapter + V2 two-pass parser
- **V2 result (23/23 = 100.0%)**: V2 adapter (46 trajectories) + V2 two-pass parser

From E4, we can decompose the v1→v2 improvement:
- **Parser effect** = E4 score − V1 score = 0 tasks *(as planned; in practice E4 also changed the client, see above)*
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

The notebook's own export is kept verbatim as `results/eval_results_e4_notebook_raw.json`
(same 23 outcomes; checked by `tests/test_results_consistency.py`), and the
session log is `notebooks/colab_e4_session.ipynb` (credentials redacted).
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

This behaviour is pinned by `tests/test_parser_fixed.py`
(`test_v2_pass2_recovers_flat_args`,
`test_v2_pass2_empty_arguments_object_not_recovered`,
`test_v2_pass2_nested_args_also_fails`).
