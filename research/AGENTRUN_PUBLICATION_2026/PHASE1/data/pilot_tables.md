# Phase 1 pilot tables (exploratory; development-only split p1dev, 64 tasks)

## p1_qwen25_14b_greedy (320 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 11/64 | 17.2 [9.9, 28.2] | 0 | 0/46 | 34/46 | 0/24 | 0/8 | 7/10 | 3.88 | 4.59 | 6 | 26.47 | 0.0 |
| B | 46/64 | 71.9 [59.9, 81.4] | 0 | 8/46 | 1/46 | 0/24 | 7/8 | 10/10 | 2.69 | 3.59 | 4 | 28.09 | 3.53 |
| E | 48/64 | 75.0 [63.2, 84.0] | 0 | 6/46 | 2/46 | 0/24 | 6/8 | 10/10 | 2.8 | 4.23 | 2 | 28.71 | 3.89 |
| G | 51/64 | 79.7 [68.3, 87.7] | 0 | 3/46 | 2/46 | 0/24 | 6/8 | 10/10 | 2.8 | 3.69 | 2 | 25.61 | 3.89 |
| R | 53/64 | 82.8 [71.8, 90.1] | 0 | 3/46 | 1/46 | 0/24 | 6/8 | 10/10 | 2.84 | 3.78 | 1 | 26.74 | 3.92 |

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | 5 | 6 | 0 | 0 |
| B | 4 | 7 | 7 | 4 | 8 | 7 | 7 | 2 |
| E | 6 | 7 | 6 | 7 | 8 | 7 | 7 | 0 |
| G | 6 | 7 | 6 | 7 | 8 | 7 | 7 | 3 |
| R | 7 | 7 | 6 | 7 | 8 | 8 | 7 | 3 |

RCS: {"n_runs_R": 64, "n_fired": 2, "by_rule": {"R3": 2}, "transitions(rule,pre,post)": {"R3 | correct | correct": 1, "R3 | over_abstain | correct": 1}, "fixed": 1, "broke_correct": 0}

Paired: {"R-G": {"a_only": 2, "b_only": 0, "sign_test_p": 0.5, "families_pos": 2, "families_neg": 0}, "G-B": {"a_only": 7, "b_only": 2, "sign_test_p": 0.1796875, "families_pos": 4, "families_neg": 2}, "E-G": {"a_only": 0, "b_only": 3, "sign_test_p": 0.25, "families_pos": 0, "families_neg": 3}, "R-B": {"a_only": 9, "b_only": 2, "sign_test_p": 0.0654296875, "families_pos": 5, "families_neg": 2}}

## p1_qwen25_3b_greedy (320 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 11/64 | 17.2 [9.9, 28.2] | 8 | 0/46 | 31/46 | 0/24 | 0/8 | 9/10 | 3.44 | 4.5 | 8 | 2.35 | 0.0 |
| B | 29/64 | 45.3 [33.7, 57.4] | 5 | 24/46 | 5/46 | 0/24 | 8/8 | 9/10 | 2.5 | 3.23 | 0 | 1.95 | 2.78 |
| E | 24/64 | 37.5 [26.7, 49.7] | 2 | 25/46 | 8/46 | 0/24 | 7/8 | 8/10 | 2.98 | 3.91 | 2 | 2.21 | 3.44 |
| G | 24/64 | 37.5 [26.7, 49.7] | 7 | 25/46 | 3/46 | 0/24 | 6/8 | 7/10 | 2.98 | 3.62 | 2 | 2.03 | 3.44 |
| R | 36/64 | 56.2 [44.1, 67.7] | 6 | 16/46 | 2/46 | 1/24 | 6/8 | 8/10 | 3.06 | 4.08 | 0 | 2.34 | 3.53 |

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | 7 | 4 | 0 | 0 |
| B | 2 | 3 | 8 | 0 | 7 | 4 | 3 | 2 |
| E | 3 | 3 | 7 | 1 | 6 | 4 | 0 | 0 |
| G | 4 | 4 | 6 | 1 | 5 | 4 | 0 | 0 |
| R | 4 | 8 | 6 | 7 | 7 | 4 | 0 | 0 |

RCS: {"n_runs_R": 64, "n_fired": 20, "by_rule": {"R2": 11, "R3": 9}, "transitions(rule,pre,post)": {"R2 | false_conflict | correct": 10, "R2 | false_conflict | stale_value": 1, "R3 | wrong_value | false_conflict": 1, "R3 | over_abstain | over_abstain": 1, "R3 | correct | format_error": 1, "R3 | over_abstain | correct": 1, "R3 | wrong_value | wrong_value": 2, "R3 | wrong_value | over_abstain": 1, "R3 | correct | correct": 1, "R3 | over_abstain | format_error": 1}, "fixed": 11, "broke_correct": 1}

Paired: {"R-G": {"a_only": 13, "b_only": 1, "sign_test_p": 0.0018310546875, "families_pos": 8, "families_neg": 1}, "G-B": {"a_only": 5, "b_only": 10, "sign_test_p": 0.3017578125, "families_pos": 3, "families_neg": 8}, "E-G": {"a_only": 2, "b_only": 2, "sign_test_p": 1.0, "families_pos": 2, "families_neg": 2}, "R-B": {"a_only": 16, "b_only": 9, "sign_test_p": 0.2295229434967041, "families_pos": 9, "families_neg": 8}}

## p1_qwen25_3b_greedy_tea (128 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|

RCS: {"n_runs_R": 0, "n_fired": 0, "by_rule": {}, "transitions(rule,pre,post)": {}, "fixed": 0, "broke_correct": 0}

Paired: {"R-G": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "G-B": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "E-G": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "R-B": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}}

## p1_qwen25_3b_T07_s1 (320 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 11/64 | 17.2 [9.9, 28.2] | 6 | 0/46 | 31/46 | 0/24 | 0/8 | 9/10 | 3.41 | 4.5 | 7 | 2.36 | 0.0 |
| B | 28/64 | 43.8 [32.3, 55.9] | 5 | 25/46 | 4/46 | 0/24 | 8/8 | 9/10 | 2.23 | 3.11 | 1 | 1.85 | 2.62 |
| E | 23/64 | 35.9 [25.3, 48.2] | 2 | 25/46 | 10/46 | 0/24 | 8/8 | 8/10 | 2.83 | 3.7 | 2 | 2.1 | 3.61 |
| G | 26/64 | 40.6 [29.5, 52.9] | 5 | 21/46 | 4/46 | 0/24 | 7/8 | 5/10 | 2.66 | 3.45 | 1 | 2.01 | 3.47 |
| R | 34/64 | 53.1 [41.1, 64.8] | 3 | 19/46 | 2/46 | 1/24 | 6/8 | 7/10 | 2.88 | 4.0 | 2 | 2.25 | 3.45 |

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | 7 | 4 | 0 | 0 |
| B | 2 | 3 | 8 | 0 | 7 | 4 | 2 | 2 |
| E | 0 | 4 | 8 | 1 | 7 | 3 | 0 | 0 |
| G | 4 | 5 | 7 | 1 | 3 | 4 | 1 | 1 |
| R | 3 | 8 | 6 | 7 | 7 | 3 | 0 | 0 |

RCS: {"n_runs_R": 64, "n_fired": 20, "by_rule": {"R3": 9, "R2": 11}, "transitions(rule,pre,post)": {"R3 | wrong_value | false_conflict": 3, "R2 | false_conflict | correct": 10, "R2 | false_conflict | stale_value": 1, "R3 | correct | format_error": 1, "R3 | over_abstain | correct": 1, "R3 | wrong_value | wrong_value": 1, "R3 | wrong_value | over_abstain": 1, "R3 | correct | max_steps": 1, "R3 | over_abstain | format_error": 1}, "fixed": 11, "broke_correct": 2}

Paired: {"R-G": {"a_only": 16, "b_only": 8, "sign_test_p": 0.15158963203430176, "families_pos": 9, "families_neg": 6}, "G-B": {"a_only": 7, "b_only": 9, "sign_test_p": 0.803619384765625, "families_pos": 5, "families_neg": 6}, "E-G": {"a_only": 6, "b_only": 9, "sign_test_p": 0.60723876953125, "families_pos": 4, "families_neg": 6}, "R-B": {"a_only": 14, "b_only": 8, "sign_test_p": 0.28627872467041016, "families_pos": 9, "families_neg": 7}}

## p1_qwen25_3b_T07_s2 (320 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 12/64 | 18.8 [11.1, 30.0] | 4 | 0/46 | 34/46 | 0/24 | 0/8 | 10/10 | 3.53 | 4.44 | 6 | 4.9 | 0.0 |
| B | 26/64 | 40.6 [29.5, 52.9] | 4 | 25/46 | 4/46 | 0/24 | 8/8 | 8/10 | 2.59 | 3.38 | 3 | 4.07 | 2.97 |
| E | 22/64 | 34.4 [23.9, 46.6] | 2 | 26/46 | 11/46 | 0/24 | 7/8 | 8/10 | 2.47 | 3.48 | 2 | 3.96 | 2.84 |
| G | 20/64 | 31.2 [21.2, 43.4] | 4 | 26/46 | 6/46 | 0/24 | 7/8 | 6/10 | 2.66 | 3.42 | 4 | 3.99 | 2.91 |
| R | 35/64 | 54.7 [42.6, 66.3] | 6 | 16/46 | 3/46 | 1/24 | 6/8 | 7/10 | 2.72 | 3.92 | 1 | 4.54 | 3.53 |

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | 8 | 4 | 0 | 0 |
| B | 1 | 3 | 8 | 0 | 6 | 4 | 2 | 2 |
| E | 1 | 3 | 7 | 1 | 6 | 4 | 0 | 0 |
| G | 1 | 3 | 7 | 1 | 5 | 3 | 0 | 0 |
| R | 3 | 8 | 6 | 7 | 6 | 5 | 0 | 0 |

RCS: {"n_runs_R": 64, "n_fired": 19, "by_rule": {"R3": 10, "R2": 9}, "transitions(rule,pre,post)": {"R3 | wrong_value | wrong_value": 3, "R2 | false_conflict | correct": 8, "R2 | false_conflict | stale_value": 1, "R3 | wrong_value | over_abstain": 3, "R3 | correct | false_conflict": 1, "R3 | over_abstain | correct": 2, "R3 | correct | correct": 1}, "fixed": 10, "broke_correct": 1}

Paired: {"R-G": {"a_only": 18, "b_only": 3, "sign_test_p": 0.0014896392822265625, "families_pos": 10, "families_neg": 1}, "G-B": {"a_only": 3, "b_only": 9, "sign_test_p": 0.14599609375, "families_pos": 2, "families_neg": 8}, "E-G": {"a_only": 5, "b_only": 3, "sign_test_p": 0.7265625, "families_pos": 3, "families_neg": 1}, "R-B": {"a_only": 19, "b_only": 10, "sign_test_p": 0.13604594767093658, "families_pos": 9, "families_neg": 7}}

## p1_qwen25_7b_greedy (320 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 14/64 | 21.9 [13.5, 33.4] | 0 | 0/46 | 42/46 | 0/24 | 0/8 | 10/10 | 2.92 | 3.73 | 0 | 3.06 | 0.0 |
| B | 43/64 | 67.2 [55.0, 77.4] | 3 | 12/46 | 0/46 | 0/24 | 7/8 | 7/10 | 3.17 | 4.14 | 3 | 3.87 | 4.27 |
| E | 36/64 | 56.2 [44.1, 67.7] | 0 | 18/46 | 6/46 | 0/24 | 7/8 | 8/10 | 2.88 | 4.17 | 4 | 4.32 | 3.69 |
| G | 38/64 | 59.4 [47.1, 70.5] | 4 | 18/46 | 0/46 | 0/24 | 7/8 | 8/10 | 2.88 | 3.75 | 4 | 3.94 | 3.69 |
| R | 47/64 | 73.4 [61.5, 82.7] | 1 | 15/46 | 0/46 | 0/24 | 8/8 | 9/10 | 3.08 | 4.08 | 1 | 4.34 | 3.88 |

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | 8 | 6 | 0 | 0 |
| B | 5 | 7 | 7 | 0 | 5 | 8 | 7 | 4 |
| E | 4 | 6 | 7 | 5 | 7 | 6 | 1 | 0 |
| G | 4 | 7 | 7 | 5 | 7 | 7 | 1 | 0 |
| R | 7 | 8 | 8 | 8 | 7 | 8 | 1 | 0 |

RCS: {"n_runs_R": 64, "n_fired": 6, "by_rule": {"R3": 3, "R2": 3}, "transitions(rule,pre,post)": {"R3 | wrong_value | correct": 3, "R2 | false_conflict | correct": 3}, "fixed": 6, "broke_correct": 0}

Paired: {"R-G": {"a_only": 9, "b_only": 0, "sign_test_p": 0.00390625, "families_pos": 6, "families_neg": 0}, "G-B": {"a_only": 11, "b_only": 16, "sign_test_p": 0.44206833839416504, "families_pos": 6, "families_neg": 13}, "E-G": {"a_only": 0, "b_only": 2, "sign_test_p": 0.5, "families_pos": 0, "families_neg": 2}, "R-B": {"a_only": 17, "b_only": 13, "sign_test_p": 0.584664711728692, "families_pos": 7, "families_neg": 9}}

## p1_qwen25_7b_greedy_tea (128 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|

RCS: {"n_runs_R": 0, "n_fired": 0, "by_rule": {}, "transitions(rule,pre,post)": {}, "fixed": 0, "broke_correct": 0}

Paired: {"R-G": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "G-B": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "E-G": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "R-B": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}}

## p1_qwen25_7b_T07_s1 (320 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 14/64 | 21.9 [13.5, 33.4] | 0 | 0/46 | 42/46 | 0/24 | 0/8 | 10/10 | 2.84 | 3.7 | 0 | 6.13 | 0.0 |
| B | 43/64 | 67.2 [55.0, 77.4] | 2 | 11/46 | 1/46 | 0/24 | 7/8 | 8/10 | 3.36 | 4.3 | 6 | 8.45 | 4.56 |
| E | 39/64 | 60.9 [48.7, 71.9] | 0 | 15/46 | 4/46 | 0/24 | 8/8 | 8/10 | 2.91 | 4.16 | 6 | 8.89 | 3.52 |
| G | 41/64 | 64.1 [51.8, 74.7] | 4 | 14/46 | 2/46 | 0/24 | 8/8 | 8/10 | 2.55 | 3.48 | 3 | 7.8 | 3.33 |
| R | 47/64 | 73.4 [61.5, 82.7] | 0 | 14/46 | 1/46 | 0/24 | 8/8 | 9/10 | 2.73 | 3.72 | 2 | 8.23 | 3.34 |

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | 8 | 6 | 0 | 0 |
| B | 5 | 8 | 7 | 1 | 6 | 8 | 7 | 1 |
| E | 5 | 6 | 8 | 4 | 7 | 6 | 2 | 1 |
| G | 4 | 6 | 8 | 6 | 6 | 8 | 2 | 1 |
| R | 6 | 8 | 8 | 8 | 7 | 8 | 2 | 0 |

RCS: {"n_runs_R": 64, "n_fired": 2, "by_rule": {"R3": 2}, "transitions(rule,pre,post)": {"R3 | wrong_value | max_steps": 1, "R3 | wrong_value | correct": 1}, "fixed": 1, "broke_correct": 0}

Paired: {"R-G": {"a_only": 8, "b_only": 2, "sign_test_p": 0.109375, "families_pos": 5, "families_neg": 2}, "G-B": {"a_only": 10, "b_only": 12, "sign_test_p": 0.8318119049072266, "families_pos": 4, "families_neg": 7}, "E-G": {"a_only": 3, "b_only": 5, "sign_test_p": 0.7265625, "families_pos": 3, "families_neg": 5}, "R-B": {"a_only": 13, "b_only": 9, "sign_test_p": 0.5234670639038086, "families_pos": 5, "families_neg": 6}}

## p1_qwen25_7b_T07_s2 (320 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 14/64 | 21.9 [13.5, 33.4] | 0 | 0/46 | 42/46 | 0/24 | 0/8 | 10/10 | 2.88 | 3.77 | 0 | 6.45 | 0.0 |
| B | 44/64 | 68.8 [56.6, 78.8] | 4 | 13/46 | 0/46 | 0/24 | 8/8 | 9/10 | 2.97 | 3.98 | 2 | 8.29 | 4.0 |
| E | 38/64 | 59.4 [47.1, 70.5] | 0 | 15/46 | 5/46 | 0/24 | 7/8 | 9/10 | 2.88 | 4.17 | 6 | 9.59 | 3.48 |
| G | 40/64 | 62.5 [50.3, 73.3] | 3 | 16/46 | 0/46 | 0/24 | 8/8 | 8/10 | 2.97 | 3.86 | 4 | 8.99 | 3.77 |
| R | 47/64 | 73.4 [61.5, 82.7] | 1 | 15/46 | 0/46 | 0/24 | 8/8 | 10/10 | 2.95 | 3.94 | 1 | 9.35 | 3.69 |

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | 8 | 6 | 0 | 0 |
| B | 4 | 8 | 8 | 0 | 7 | 8 | 8 | 1 |
| E | 5 | 5 | 7 | 3 | 7 | 8 | 2 | 1 |
| G | 4 | 7 | 8 | 7 | 7 | 7 | 0 | 0 |
| R | 7 | 8 | 8 | 7 | 8 | 8 | 1 | 0 |

RCS: {"n_runs_R": 64, "n_fired": 6, "by_rule": {"R3": 2, "R2": 4}, "transitions(rule,pre,post)": {"R3 | wrong_value | correct": 1, "R2 | false_conflict | correct": 3, "R3 | over_abstain | correct": 1, "R2 | false_conflict | wrong_value": 1}, "fixed": 5, "broke_correct": 0}

Paired: {"R-G": {"a_only": 8, "b_only": 1, "sign_test_p": 0.0390625, "families_pos": 5, "families_neg": 0}, "G-B": {"a_only": 8, "b_only": 12, "sign_test_p": 0.5034446716308594, "families_pos": 3, "families_neg": 10}, "E-G": {"a_only": 7, "b_only": 9, "sign_test_p": 0.803619384765625, "families_pos": 6, "families_neg": 6}, "R-B": {"a_only": 11, "b_only": 8, "sign_test_p": 0.6476058959960938, "families_pos": 4, "families_neg": 6}}

## p1_qwen3_8b_greedy (320 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 14/64 | 21.9 [13.5, 33.4] | 1 | 0/46 | 38/46 | 0/24 | 0/8 | 10/10 | 3.39 | 4.05 | 3 | 9.29 | 0.0 |
| B | 47/64 | 73.4 [61.5, 82.7] | 0 | 16/46 | 0/46 | 0/24 | 8/8 | 9/10 | 2.69 | 3.55 | 1 | 8.15 | 3.16 |
| E | 47/64 | 73.4 [61.5, 82.7] | 0 | 16/46 | 1/46 | 0/24 | 8/8 | 10/10 | 2.59 | 3.94 | 0 | 9.47 | 3.25 |
| G | 48/64 | 75.0 [63.2, 84.0] | 0 | 16/46 | 0/46 | 0/24 | 8/8 | 10/10 | 2.59 | 3.47 | 0 | 8.44 | 3.25 |
| R | 48/64 | 75.0 [63.2, 84.0] | 0 | 16/46 | 0/46 | 0/24 | 8/8 | 10/10 | 2.59 | 3.47 | 0 | 8.43 | 3.25 |

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| A | 0 | 0 | 0 | 0 | 8 | 6 | 0 | 0 |
| B | 8 | 8 | 8 | 3 | 7 | 8 | 3 | 2 |
| E | 8 | 8 | 8 | 8 | 8 | 7 | 0 | 0 |
| G | 8 | 8 | 8 | 8 | 8 | 8 | 0 | 0 |
| R | 8 | 8 | 8 | 8 | 8 | 8 | 0 | 0 |

RCS: {"n_runs_R": 64, "n_fired": 0, "by_rule": {}, "transitions(rule,pre,post)": {}, "fixed": 0, "broke_correct": 0}

Paired: {"R-G": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "G-B": {"a_only": 6, "b_only": 5, "sign_test_p": 1.0, "families_pos": 3, "families_neg": 5}, "E-G": {"a_only": 0, "b_only": 1, "sign_test_p": 1.0, "families_pos": 0, "families_neg": 1}, "R-B": {"a_only": 6, "b_only": 5, "sign_test_p": 1.0, "families_pos": 3, "families_neg": 5}}

## p1_qwen3_8b_greedy_tea (128 runs)

| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | abstain ok | tool calls | model calls | step limit | latency s | records shown |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Per scenario (successes / 8):

| Config | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|

RCS: {"n_runs_R": 0, "n_fired": 0, "by_rule": {}, "transitions(rule,pre,post)": {}, "fixed": 0, "broke_correct": 0}

Paired: {"R-G": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "G-B": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "E-G": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}, "R-B": {"a_only": 0, "b_only": 0, "sign_test_p": null, "families_pos": 0, "families_neg": 0}}

