# Architecture

This page describes the components that every reported condition (Base, V1, E4, V2) goes through, and what changes between conditions. Read it alongside the code. Where this page and the code disagree, the code is authoritative.

## Components

| Component | File(s) | Runs on | Varies across conditions? |
|---|---|---|---|
| Base model | `Qwen/Qwen2.5-7B-Instruct`, 4-bit NF4, fp16 compute | Colab T4 | no |
| LoRA adapter | V1: `training/colab_train_7b.py` (35 traj.); V2: `training/colab_train_7b_v2.py` (46 traj.) | Colab T4 | **yes** (none / V1 / V1 / V2) |
| Decoding | `do_sample=False`, `max_new_tokens=512` | Colab T4 | no |
| Serving-layer parser | `parse_model_output()` in `serving/colab_server*.py` | Colab T4 | **yes** (single-pass for Base/V1, two-pass for E4/V2) |
| HTTP transport | FastAPI `POST /chat`, exposed through ngrok | Colab to local | no |
| Agent loop | Base/V1/V2: `QwenRemoteClient.run()` in `ft_agent.py`; **E4: notebook-local loop** | local / Colab | **yes, for E4** |
| Tool schemas, executors and result format | Base/V1/V2: `mcp_server.py` (MCP over stdio), `tools.py`, `providers/`; **E4: notebook-local functions** | local / Colab | **yes, for E4** |
| Step budget | `max_steps=3` passed by every `evaluation/run_eval_*.py` | local | no |
| Scoring | `score_task()` in `eval/harness.py`, tasks in `eval/tasks.py` | local | no |

## One step of the loop

1. `ft_agent.py` sends the system prompt, the conversation so far, and the four tool schemas to `POST /chat`.
2. The server renders them with Qwen's chat template (`tokenizer.apply_chat_template(..., tools=...)`) and generates greedily.
3. The server's `parse_model_output()` turns the raw text into `{"tool_calls": [...], "text": null}` or `{"tool_calls": [], "text": "<answer>"}`.
4. If the server returned no tool calls but did return text, the client re-scans that text locally (`_parse_tool_calls_from_text`). It first looks for closed `<tool_call>` blocks, then for untagged `{"name": ..., "arguments": {...}}` JSON.
5. If there are still no tool calls, the text is the final answer. Otherwise each call is executed through MCP. An exception, or a tool result starting with `ERROR`, is recorded as a tool error. The call and its observation are appended to the conversation and the loop continues.
6. After `max_steps` model turns without a final answer, the run ends with `hit_max_steps=True`.

## The two parsers

Single-pass (`colab_server.py`, `colab_server_base.py`):

```python
re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)   # closed blocks only
```

Two-pass (`colab_server_v2.py`, `colab_server_e4.py`):

- **Pass 1** uses the same closed-block regex. It also drops calls whose JSON has no `name`, which the single-pass parser kept as `name=None`.
- **Pass 2** runs only if pass 1 found nothing. It applies `<tool_call>\s*(\{.*?\})` to the first opening tag. Because `.*?` stops at the **first** `}`, pass 2 recovers only calls whose JSON contains no nested object. A call with an `"arguments": {...}` member, even `{}`, is truncated, fails `json.loads`, and is returned as a final answer. The server docstring presents pass 2 as the fix for the `adversarial_chained_search_calc` malformed-output case, but that case carries nested arguments and pass 2 does not recover it. Under E4 that task regressed. `tests/test_parser.py` and `tests/test_parser_fixed.py` pin this behavior and check that the regexes in the tests match the serving sources.

Neither parser validates tool names or argument types against the tool schemas. An unknown tool name or malformed arguments reach MCP, which raises an error, and the client records that as a tool error.

## Caveats on what was held constant

- **Client version.** `ft_agent.py` has a single committed version (commit `93f27d7`, 2026-09-01). The repository does not record whether the client changed between the Base, V1, and V2 runs that day.
- **E4 used a different client.** The reported E4 score comes from cell 16 of `notebooks/colab_e4_session.ipynb`. That cell re-implements the loop and the tools inside Colab and still calls `eval/harness.py::score_task` with `max_steps=3`. Compared with `ft_agent.py` and MCP, it differs in four ways:
  - its tool schemas carry one-to-three-word descriptions ("Evaluate arithmetic") and no parameter descriptions;
  - tool calls go back to the model as OpenAI-style `tool_calls` with `content: null`, and results as `{"result": ...}` / `{"error": ...}` JSON, instead of `<tool_call>` text and the provider-formatted strings;
  - weather and search results are raw API structures, and only exceptions count as tool errors;
  - there is no client-side text re-parse (step 4 above).

  Every multi-step task therefore saw a different prompt at step 2 onward. See `docs/e4-experiment-guide.md`.
- **Live tools.** `web_search` (Tavily) and `get_weather` (Open-Meteo) return live data, so tool observations differ between runs and between conditions.
- **Training run.** V2 differs from V1 in its data and also in its optimizer and memory settings (`provenance/hyperparameters.md`).

## Why the runtime is not refactored

The evaluation client, tool layer, parsers, and scorer are kept as they were when the reported results were produced, so the committed results stay attributable to the committed code. Changes since then are limited to two:

- `eval/harness.py` imports the agent types only for annotations. Scoring can therefore run without the Gemini/MCP stack, and the scoring behavior is unchanged.
- The calculator in `tools.py` evaluates by walking the AST instead of calling `eval`. Results and error strings are unchanged for every input allowed by the character whitelist (checked against the original in `tests/test_calculator_tool.py`). The only exception is that exponents above 1000 are now rejected. This closes a denial-of-service path (`9**9**9**9`) and does not affect any benchmark task.
