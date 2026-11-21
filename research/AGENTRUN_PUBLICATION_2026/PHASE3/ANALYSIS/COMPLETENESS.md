# Completeness (eval3)

Tasks 268; task file sha256 `602eb74885084746…`.

| Cell | present | DONE | rows / expected | missing | duplicates | error rows | starts |
|---|---|---|---|---|---|---|---|
| eval3_qwen25_3b_greedy | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen25_3b_T07_s1 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen25_3b_T07_s2 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen25_3b_T07_s3 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen25_7b_greedy | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen25_7b_T07_s1 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen25_7b_T07_s2 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen25_7b_T07_s3 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_llama31_8b_greedy | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_llama31_8b_T07_s1 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_llama31_8b_T07_s2 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_llama31_8b_T07_s3 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen3_8b_greedy | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen3_8b_T07_s1 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen3_8b_T07_s2 | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_qwen3_8b_T07_s3 | True | True | 3216 / 3216 | 0 | 0 | 0 | 2 |
| eval3_qwen25_14b_greedy | True | True | 3216 / 3216 | 0 | 0 | 0 | 1 |
| eval3_llama32_3b_greedy | True | True | 3216 / 3216 | 0 | 0 | 0 | 2 |

G4 policy: g4-v2 (2026-11-21); declared observational: gpu_mem_gib

Observational client differences (reported, not failures): eval3_qwen3_8b_T07_s3: client.gpu_mem_gib = start 0=44.6 vs start 1=44.4; eval3_llama32_3b_greedy: client.gpu_mem_gib = start 0=44.6 vs start 1=44.4

Integrity problems: none
