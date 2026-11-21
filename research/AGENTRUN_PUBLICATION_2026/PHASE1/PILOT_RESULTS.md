# Phase 1 pilot results (exploratory, development splits only)

**14 November 2026.**

**Status.** Every number here is **exploratory**:
- `p1dev` and `p1hold` are development splits written by the same author as the mechanisms;
- the designs are single-family (Qwen);
- greedy decoding is complemented by only two sampled seeds, and only for 3B and 7B.

Nothing here is a confirmatory result, and nothing was run on the sealed sets.

**Tables are generated, not hand-typed:**
- `scripts/pilot_deep_analysis.py` → `data/pilot_deep_tables.md` and `data/pilot_deep_analysis.json`;
- `scripts/analyze_pilot.py` → `data/pilot_tables.md` (per run);
- `scripts/arbiter_offline_eval.py` → `data/arbiter_offline_eval.json`.

## 1. Recovery of the 13 November runs

| Run id | Model (snapshot in manifest) | Decoding | Tasks × configs | Runs | Started → exit=0 (UTC, 13 Nov) | Status |
|---|---|---|---|---|---|---|
| `smoke_qwen25_3b` | Qwen2.5-3B-Instruct | greedy | 8 × 5 | 40 | → 11:24 | complete (smoke only, not analysed) |
| `p1_qwen25_3b_greedy` | Qwen2.5-3B-Instruct | greedy | 64 × 5 | 320 | 11:24 → 11:36 | **complete** |
| `p1_qwen25_3b_T07_s1` | Qwen2.5-3B-Instruct | T = 0.7, seed 1 | 64 × 5 | 320 | 11:36 → 11:47 | **complete** |
| `p1_qwen25_3b_T07_s2` | Qwen2.5-3B-Instruct | T = 0.7, seed 2 | 64 × 5 | 320 | 11:47 → 12:10 | **complete** |
| `p1_qwen25_14b_greedy` | Qwen2.5-14B-Instruct | greedy | 64 × 5 | 320 | 12:10 → 14:35 | **complete** |
| `p1_qwen25_7b_greedy` | Qwen2.5-7B-Instruct | greedy | 64 × 5 | 320 | 11:24 → 11:45 | **complete** |
| `p1_qwen25_7b_T07_s1` | Qwen2.5-7B-Instruct | T = 0.7, seed 1 | 64 × 5 | 320 | 11:45 → 12:27 | **complete** |
| `p1_qwen25_7b_T07_s2` | Qwen2.5-7B-Instruct | T = 0.7, seed 2 | 64 × 5 | 320 | 12:27 → 13:13 | **complete** |
| `p1_qwen3_8b_greedy` | Qwen3-8B | greedy | 64 × 5 | 320 | 13:13 → 14:00 | **complete** |

**How completeness was established.**
- Every run has a `DONE` file with `runs: 320`, 320 lines in `runs.jsonl`, and an `exit=0` line in the queue log. Both queue logs end with `queue N finished`.
- All eight manifests carry:
  - the same split hash, `94fe396f…`;
  - `rcs_py_sha256` `9f0a838b…`, identical to `prototype/rcs.py` today;
  - `memlab_py_sha256` `dc28584c…`.
- **No process from these queues was alive on 14 Nov** (`HPC_RESOURCE_SHARING.md` §2).
- **Failed runs:** none. **Missing runs:** none.
- Every planned run in `prototype/launch_pilot.sh` exists. Nothing was relaunched or resumed.

**Hashes.**
- All files were copied from `<compute-node>` and sha256-compared, node versus laptop: 42 of 42 identical.
- Hashes for every file in `PHASE1/` are in `HASH_MANIFEST.txt`.

## 2. Design of the first pilot

- **Split `p1dev`** (seed 20261114): 64 tasks in 8 scenarios × 8 tasks; **34 scenario-variant families**.
  - S1–S6 use the memlab templates.
  - **S7** is a same-day correction: same `recorded_on`; the text says it corrects the earlier value.
  - **S8** gives the date only in the text: same import date, and different "As of" dates in the text.
  - Names come from a slice disjoint from dev, eval and eval2.
- **Configurations:**
  - A: no memory;
  - B: memory;
  - E: memory + provenance + labels + same-model verifier;
  - G: memory + provenance + labels;
  - R: G + RCS (rules R1 stale value, R2 false conflict, R3 no search; one corrective notice).
- **Other settings:** harness v2; HF transformers, bf16, one L40 per queue.

**Unit of analysis.**
- A *run* is task × configuration × decoding.
- Contrasts use the **task-level mean over decodings**: 3 decodings for 3B and 7B, 1 for 14B and 8B.
- The test is an **exact family-level sign-flip permutation** over 34 families. Repeated decodings are never counted as independent tasks.

## 3. Results of the first pilot

**Counts are runs.** Denominators:
- 3B and 7B: 192 runs = 64 tasks × 3 decodings, with 138 answerable runs and 30 should-abstain runs.
- 14B and Qwen3-8B: 64 runs, 46 answerable, 10 should-abstain.

### 3.1 Overall and per behaviour

| Model | Config | Success | Over-abstain (answerable) | False conflict (answerable) | Unsupported (abstain tasks) | S3 conflict ok | S4 ok | **S7 ok** | **S8 ok** | Format err | Step limit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3B | B | 83/192 | 13/138 | 74/138 | 0/30 | 24/24 | 0/24 | 7/24 | 6/24 | 3 | 4 |
| 3B | G | 70/192 | 13/138 | 72/138 | 2/30 | 20/24 | 3/24 | 1/24 | 1/24 | 8 | 7 |
| 3B | R | **105/192** | 7/138 | 51/138 | 2/30 | 18/24 | 21/24 | **0/24** | **0/24** | 7 | 3 |
| 7B | B | 130/192 | 1/138 | 36/138 | 0/30 | 22/24 | 1/24 | **22/24** | 6/24 | 5 | 11 |
| 7B | G | 119/192 | 2/138 | 48/138 | 1/30 | 23/24 | 18/24 | **3/24** | 1/24 | 0 | 11 |
| 7B | R | **141/192** | 1/138 | 44/138 | 0/30 | 24/24 | 23/24 | 4/24 | 0/24 | 0 | 4 |
| Q3-8B | B | 47/64 | 0/46 | 16/46 | 0/10 | 8/8 | 3/8 | 3/8 | 2/8 | 0 | 1 |
| Q3-8B | G | 48/64 | 0/46 | 16/46 | 0/10 | 8/8 | 8/8 | 0/8 | 0/8 | 0 | 0 |
| Q3-8B | R | 48/64 | 0/46 | 16/46 | 0/10 | 8/8 | 8/8 | 0/8 | 0/8 | 0 | 0 |
| 14B | B | 46/64 | 1/46 | 8/46 | 0/10 | 7/8 | 4/8 | 7/8 | 2/8 | 4 | 4 |
| 14B | G | 51/64 | 2/46 | 3/46 | 0/10 | 6/8 | 7/8 | 7/8 | 3/8 | 4 | 2 |
| 14B | R | **53/64** | 1/46 | 3/46 | 0/10 | 6/8 | 7/8 | 7/8 | 3/8 | 4 | 1 |

**Notes on the other configurations:**
- **A:** 34/192, 42/192, 14/64 and 11/64 for 3B, 7B, Q3-8B and 14B. Over-abstention under A (96/138 at 3B) is honest, because A has no memory.
- **E (verifier):** 69/192, 113/192, 47/64, 48/64. The verifier rejected 6 correct drafts at 3B, 6 at 7B, 3 at 14B and 1 at 8B, and is never better than G overall.
- Stale-value answers are rare everywhere (0–3 runs).

### 3.2 Paired contrasts (task means over decodings; exact family sign-flip, 34 families)

| Model | R − G all | R − G on S7/S8 | G − B all | **G − B on S7/S8** | R − B all |
|---|---|---|---|---|---|
| Qwen2.5-3B (3 decodings) | **+18.2 pp**, tasks 20/6, p = 0.029 | −4.2 pp | −6.8 pp, p = 0.28 | −22.9 pp, tasks 1/5, p = 0.094 | +11.5 pp, p = 0.30 |
| Qwen2.5-7B (3 decodings) | **+11.5 pp**, tasks 18/2, p = 0.010 | 0.0 | −5.7 pp, p = 0.58 | **−50.0 pp, tasks 0/11, p = 0.004** | +5.7 pp, p = 0.64 |
| Qwen3-8B (greedy) | 0.0 (RCS never fired) | 0.0 | +1.6 pp | −31.2 pp, tasks 0/5, p = 0.063 | +1.6 pp |
| Qwen2.5-14B (greedy) | +3.1 pp, tasks 2/0, p = 0.50 | 0.0 | +7.8 pp, p = 0.37 | +6.2 pp | +10.9 pp, p = 0.25 |

**Reading:**

1. **The enforcement benefit falls with capacity**, in this family and on this split:
   - R − G is +18 pp at 3B, +12 pp at 7B, and ≈ 0 at 8B and 14B.
   - At 3B the gain comes from R2 converting false conflicts into correct answers (28 of 59 firings) and from S4 (3/24 → 21/24).
   - This is consistent with H2, but on a development split.
2. **The labels themselves harm every model ≤ 8B on metadata-insufficient memory (S7/S8).** This is the largest and most consistent effect in the pilot:
   - **Qwen2.5-7B:** S7 falls from 22/24 (B) to 3/24 (G).
   - **Qwen2.5-14B:** unaffected (S7 7/8 in B and in G).
   - The verbatim example is `FAILURE_TAXONOMY.md` §6.2 (M8).
3. **Enforcement cannot repair label errors** (R − G on S7/S8 ≈ 0), because RCS reads the same labels (M9).
4. **Overall, the advisory labels are not a net gain below 14B:** G − B < 0 at 3B and 7B. R is the best configuration at 3B, 7B and 14B, **but R − B is not significant at any size**: R's gains on S1–S6 are offset by the S7/S8 losses.

### 3.3 RCS interventions (all R runs)

| Model | Fired / R runs | Fixed (wrong → correct) | **Broke a correct submission** | No change |
|---|---|---|---|---|
| 3B | 59/192 | 32 | **4** | 9 |
| 7B | 14/192 | 12 | 0 | 0 |
| Q3-8B | 0/64 | 0 | 0 | 0 |
| 14B | 2/64 | 1 | 0 | 1 |

**The four 3B breaks are all rule R3**, all on S6 tool-failure tasks where abstention was correct:
- `p1dev-S6_tool_failure-02` in all three decodings, twice ending as a format error and once as a false conflict;
- `p1dev-S6_tool_failure-06` (T07_s1), ending at the step limit.

The single "R3 converted a correct answer into a format error" reported on 13 Nov is the greedy instance of the first. **R3 is DISCERN's EarnedAbstainGate**, and this is its measured cost at 3B.

### 3.4 Cost

**Model calls per run:**
- R adds 0.0–0.5 model calls per run over G: 3B 3.50 → 4.00, 7B 3.70 → 3.91.
- The verifier (E) adds about 0.4–0.5.

**Memory-observation size:**
- Labels add about 450 characters per run: B 210–330 versus G 660–790 characters.
- RCS adds a notice of about 250 characters only when it fires.

**Latency:**
- Mean per run: 3B ≈ 2.6–3.0 s, 7B ≈ 6.9–7.6 s, Q3-8B ≈ 8.2–9.5 s, 14B ≈ 26–29 s.
- Latency was measured while both GPUs ran queues on one node, and the seeded 7B runs ran alongside 14B. **Treat latency as indicative only.**

## 4. The three comparisons the brief asked for

| | Existing memory (B) | Advisory labels (G) | Enforced (R) |
|---|---|---|---|
| Metadata sufficient (S1–S6) | baseline | better on S4 at every size; mixed elsewhere at 3B | best at 3B and 7B |
| Metadata insufficient (S7/S8) | **best ≤ 8B** (7B: 28/48 runs) | worst (7B: 4/48) | ≈ G (7B: 4/48) |
| Unsupported answers | 0 everywhere | 0–2 runs | 0–2 runs |
| Unnecessary abstention | low | low | lowest |

The temporal-arbitration candidate (TEA) is analysed separately in §5.

## 5. TEA follow-up (Slurm job 4173, 14 Nov 03:08–04:09 UTC, one L40)

**Runs.** All greedy, all `exit=0`, all complete, no resumes. Every manifest records `tea_py_sha256` `37bed1fe…`, `rcs_py_sha256` `9f0a838b…` and Slurm job 4173. All 26 files were sha256-identical on the node and the laptop.

| Run id | Model | Split (sha256) | Configs | Runs |
|---|---|---|---|---|
| `p1_qwen25_3b_greedy_tea` | Qwen2.5-3B | p1dev (`94fe396f…`, same as §1) | T, RT | 128 |
| `p1_qwen25_7b_greedy_tea` | Qwen2.5-7B | p1dev | T, RT | 128 |
| `p1_qwen3_8b_greedy_tea` | Qwen3-8B | p1dev | T, RT | 128 |
| `p1h_qwen25_3b_greedy` | Qwen2.5-3B | p1hold (`f747fbfa…`, frozen before `tea.py`) | B, G, R, T, RT | 240 |
| `p1h_qwen25_7b_greedy` | Qwen2.5-7B | p1hold | B, G, R, T, RT | 240 |
| `p1h_qwen3_8b_greedy` | Qwen3-8B | p1hold | B, G, R, T, RT | 240 |

**Not run.** 14B: it was immune to the label harm in §3, and a run would have cost about 2.7 GPU-hours. Seeds were not run for T and RT either. **Every TEA number is a single greedy decoding.**

**Pairing.** On p1dev, T and RT exist only for greedy, so T/RT contrasts are paired with the greedy B/G/R runs of the same tasks. They are never paired with seed averages. p1hold has 48 tasks in 15 families, and the genuine-conflict subset is only 3 families (N1, N2, N3), so family-level p-values there cannot be small. **Report the task counts.**

### 5.1 p1dev: does correct labelling remove the label harm?

| Model | G | T | R | RT | S7 G → T → RT | S8 G → T → RT | Paired (greedy) |
|---|---|---|---|---|---|---|---|
| 3B | 24/64 | 28/64 | 36/64 | **53/64** | 0 → 2 → **8**/8 | 0 → 1 → **7**/8 | RT − R +26.6 pp, tasks 17/0, p = 0.0001; T − G +6.2 pp, p = 0.22 |
| 7B | 38/64 | 49/64 | 47/64 | **60/64** | 1 → 8 → 8/8 | 0 → 5 → 8/8 | T − G +17.2 pp, 13/2, p = 0.024; RT − R +20.3 pp, 15/2, p = 0.017 |
| Q3-8B | 48/64 | **64/64** | 48/64 | **64/64** | 0 → 8 → 8/8 | 0 → 8 → 8/8 | T − G +25.0 pp, 16/0, p = 0.0006; RT − T 0 |

(G and R here are the greedy runs of §3; the §3 tables pool three decodings.)

- **With correct labels, advice suffices from 7B up.** At 3B it does not: T barely moves 3B. Only enforcement on correct labels (RT) does.
- **This is H2 again, now with labels that are right.**
- RT also lowers false conflicts on answerable tasks to 1/46 (3B) and 0/46 (7B, 8B).
- **Unsupported answers:** RT 1/10 (3B), 0 elsewhere.
- **R3 broke the same 3B task again:** `p1dev-S6_tool_failure-02`, RT → `format_error`. That is the 5th R3 break of a correct abstention at 3B; there were none at ≥ 7B.

### 5.2 p1hold (held-out phrasings): generalisation and the arbiter's own harm

Successes per scenario, out of 6:

| Model | Config | C4 | H7a | H7b | H8a | H9 | N1 | N2 | **N3** | Total /48 |
|---|---|---|---|---|---|---|---|---|---|---|
| 3B | B | 0 | 3 | 0 | 0 | 0 | 6 | 4 | 4 | 17 |
| 3B | G | 0 | 1 | 0 | 0 | 0 | 6 | 5 | 6 | 18 |
| 3B | R | 5 | 1 | 0 | 0 | **0** | 6 | 5 | 6 | 23 |
| 3B | T | 0 | 1 | 0 | 1 | 1 | 6 | 6 | 6 | 21 |
| 3B | RT | 6 | 5 | 0 | 5 | 6 | 6 | 6 | **1** | **35** |
| 7B | B | 0 | 3 | 2 | 0 | 3 | 4 | 3 | 5 | 20 |
| 7B | G | 5 | 1 | 0 | 0 | 0 | 6 | 6 | 6 | 24 |
| 7B | R | 6 | 1 | 0 | 0 | 0 | 6 | 6 | 6 | 25 |
| 7B | T | 5 | 5 | 0 | 3 | 6 | 6 | 6 | 5 | **36** |
| 7B | RT | 6 | 5 | 0 | 5 | 6 | 6 | 6 | **0** | 34 |
| Q3-8B | B | 0 | 2 | 2 | 2 | 5 | 4 | 2 | 5 | 22 |
| Q3-8B | G | 6 | 0 | 0 | 0 | 0 | 6 | 6 | 6 | 24 |
| Q3-8B | R | 6 | 0 | 0 | 0 | 0 | 6 | 6 | 6 | 24 |
| Q3-8B | T | 6 | 5 | 0 | 5 | 6 | 6 | 6 | 6 | **40** |
| Q3-8B | RT | 6 | 5 | 0 | 5 | 6 | 6 | 6 | **0** | 34 |

**Scenario key:**
- H7a: correction naming the old value;
- H7b: correction not naming it;
- H8a: long-form validity dates;
- H9: back-filled entry, where metadata order is reversed;
- N1–N3: genuine conflicts (same text date; rival value mentioned; negated cue);
- C4: metadata-ordered control.

Under B the C4 control is unsolvable by design: B shows no dates, as with S4 `date_in_metadata_only`.

**Findings:**

1. **TEA generalises where its offline labels were right** (H7a, H8a, H9):
   - TEA-resolvable subset, T − G: 3B +11 pp (tasks 3/1), 7B +72 pp (13/0, p = 0.031), Q3-8B +89 pp (16/0, p = 0.016).
   - RT − R: +83 pp at 3B and 7B, +89 pp at 8B (15–16 tasks to 0).
2. **Enforcement amplifies whatever the label says.**
   - **TEA's wrong label on N3, under enforcement:** RT turns 5 (3B), 5 (7B) and 6 (8B) correct `conflict` answers into **arbitrary picks** (one 3B case became over-abstention).
     - All 16 come from R2 notices: `p1hold-N3_conflict_negated_replacement-00…05`; lists in `data/pilot_deep_analysis.json` → `rcs`.
     - Under T the same wrong label was **mostly ignored**: N3 6/6, 5/6, 6/6.
   - **The legacy label's error on H9, under enforcement:** R's R2 notice turned 5/6 3B H9 tasks from false conflicts into **stale answers** (`p1hold-H9_backfilled_entry-01…05`).
3. **Net best configuration depends on capacity.**
   - At 3B: RT (35/48) ≫ everything else. Enforcement is needed, and it pays for its N3 harm.
   - At 7B and 8B: **T is best** (36 and 40/48). RT loses its N3 tasks for no gain on the rest (RT − T: −4.2 and −12.5 pp).
   - This is the pattern H5 (basis-gated enforcement) and a capacity-dependent policy are meant to exploit. **It is an observation on one development split, not a validated policy.**
4. **An asymmetry in label compliance** (exploratory; N3 is one family of 6 tasks).
   - Models ≤ 8B follow a wrong *cautionary* label (`conflicting` on S7/S8/H7b) almost always.
   - They largely resist a wrong *committing* label (N3 `current`/`superseded`) when the text explicitly says "does not replace … both figures stand".
   - Wrong labels therefore hurt most when they push toward conflict or abstention, and enforcement removes the model's resistance to committing labels.
5. **TEA's honest misses remain label harm.** On H7b (a correction that does not name the old value), TEA leaves `conflicting`. Under T and RT every model fails (0/6), while B gets 2/6 at 7B and 8B.

### 5.3 Overhead

- **Model calls per run:** T ≈ G (3.1–3.7). RT adds model calls over T: 3B +0.52 to +0.64, 7B +0.17 to +0.39, Q3-8B 0 (p1dev) and +0.12 (p1hold).
- **Labels:** TEA adds `basis` (and occasionally `note` / `valid_from`). Mean memory-observation size per run, T versus G: +55 to +206 characters (`data/pilot_deep_analysis.json` → `per_run`, `memory_obs_chars_mean`).
- **Latency:** these runs had the node alone, so they are faster than the §3 runs, which shared the node: 3B 1.6–2.5 s, 7B 3.6–4.5 s, 8B 3.7–4.1 s per run. Latency is **not comparable with §3**.
- **Offline arbiter cost:** < 1 ms per group. No model call.

### 5.4 What this does and does not show

**Shows** (development data, one model family, greedy):
- (a) metadata-only labels cause large harm on metadata-insufficient memory;
- (b) basis-aware labels remove that harm on held-out phrasings where the arbiter is right;
- (c) small models need enforcement to benefit, and capable ones do not;
- (d) enforcement turns arbiter errors into harmful answers at every size.

**Does not show:**
- that TEA generalises to phrasings written by others;
- that basis-gated enforcement works (not implemented);
- behaviour of other model families;
- seed robustness of T and RT;
- anything confirmatory.
