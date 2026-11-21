# Expected outputs

```
phase3_raw/                                   (cluster; restricted)
  eval3_<model>_<decoding>/                   18 cells: qwen25_3b, qwen25_7b, llama31_8b, qwen3_8b × {greedy, T07_s1, T07_s2, T07_s3};
                                              qwen25_14b_greedy; llama32_3b_greedy
    runs.jsonl       3,216 lines = 268 tasks × 12 configurations; one JSON object per run: task_id, config, model,
                     final, draft, tool_calls, api_calls, rcs_events, messages, timing, (error on harness failure)
    manifest.jsonl   one line per start: run_id, split_sha256, configs, evarb_version, code_sha256, client
                     (model, snapshot path, dtype, max_new_tokens, seed, temperature), torch, transformers, gpu, slurm_job_id
    DONE             {"finished_utc", "runs"}
  SHA256SUMS         written by the controller when all 18 cells are DONE
PHASE3/
  ANALYSIS/          COMPLETENESS, CONFIRMATORY_primary_cells, SENSITIVITY_*, SECONDARY_cells, METRICS, CROSSCHECK (.json/.md),
                     FINALIZE_GATES.json, controller_SHA256SUMS.txt, finalize_*.log;  ANALYSIS/DRYRUN/ = development pipeline test
  results/           execution.csv, per_model_config.csv, per_category.csv, per_decoding.csv, metrics.csv,
                     contrasts_primary_cells.csv, contrasts_sensitivity_*.csv, contrasts_secondary_cells.csv
  PHASE3_*.md, PHASE3_DECISIONS.json, PHASE3_SHA256_MANIFEST.txt
```
Outcome labels are produced by the frozen `memlab.score_run`: correct, wrong_value, stale_value, unsupported_claim, arbitrary_pick, over_abstain, false_conflict, format_error, max_steps (step limit) and missing.
