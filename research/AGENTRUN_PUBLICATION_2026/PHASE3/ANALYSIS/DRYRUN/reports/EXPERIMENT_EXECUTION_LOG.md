# Experiment execution log

Slurm array 4233 (submitted 2026-11-17 08:5x UTC), retry controller 4243, one GPU at a time. Cluster logs are in `logs/`; manifests per cell in RAW_RESULTS.

# Completeness (DRY RUN on development data)

Tasks 90; task file sha256 `608e65363def3e7e…`.

| Cell | present | DONE | rows / expected | missing | duplicates | error rows | starts |
|---|---|---|---|---|---|---|---|
| p2val2_qwen25_3b_greedy | True | True | 1080 / 1080 | 0 | 0 | 0 | 1 |
| p2val2_qwen25_7b_greedy | True | True | 1080 / 1080 | 0 | 0 | 0 | 1 |
| p2val2_llama31_8b_greedy | True | True | 1080 / 1080 | 0 | 0 | 0 | 1 |
| p2val2_qwen3_8b_greedy | True | True | 1080 / 1080 | 0 | 0 | 0 | 1 |

Integrity problems: none

## Notes

(add: GPU-hours per cell from manifests/logs, resubmissions, incidents)
