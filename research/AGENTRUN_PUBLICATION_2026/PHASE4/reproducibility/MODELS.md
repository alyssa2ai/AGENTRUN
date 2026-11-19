# Models and decoding

| Role (PREREGISTRATION.md §4) | Hugging Face id | Snapshot (commit) | Decodings |
|---|---|---|---|
| primary | `Qwen/Qwen2.5-3B-Instruct` | `aa8e72537993ba99e69dfaafa59ed015b17504d1` | greedy; T = 0.7 seeds 1, 2, 3 |
| primary | `Qwen/Qwen2.5-7B-Instruct` | `a09a35458c702b33eeacc393d103063234e8bc28` | greedy; T = 0.7 seeds 1, 2, 3 |
| primary | `Qwen/Qwen3-8B` (thinking disabled through the chat template) | `b968826d9c46dd6066d109eabc6255188de91218` | greedy; T = 0.7 seeds 1, 2, 3 |
| primary, second family | `meta-llama/Llama-3.1-8B-Instruct` (through `evarb.clients.FamilyClient`) | `0e9e39f249a16976918f6564b8830bc894c89659` | greedy; T = 0.7 seeds 1, 2, 3 |
| secondary (never pooled; also the eval3 writer and an annotator) | `Qwen/Qwen2.5-14B-Instruct` | `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8` | greedy |
| format-limited (never pooled) | `meta-llama/Llama-3.2-3B-Instruct` | recorded in `PHASE3/RAW_RESULTS/eval3_llama32_3b_greedy/manifest.jsonl` (`client.model_path`) | greedy |

Settings common to all cells, from the `client` block of every manifest: backend `hf-local`, dtype bfloat16, `max_new_tokens` 700, parser `two-pass-v2+client-fallback`, no adapter, base seed 20261111 for greedy decoding.

**Configurations**, 12 per cell: B, G, R, T, RT, EB, EBG, LA, LG, EBG-all, EBG-unsafe, EBG-noR3 (`PHASE2/SYSTEM_ARCHITECTURE.md` §4; manuscript §3). LA and LG call the same model as the LLM arbiter.

**Cells**: 4 primary models × 4 decodings plus 2 greedy-only models = 18 cells. Each cell is 268 tasks × 12 configurations = 3,216 runs, so 57,888 runs in all. The cell index mapping is in `slurm/phase3_eval3.sbatch` (`CELLS`).
