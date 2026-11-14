# Phase 1 final report: memory-reliability control for small tool-using agents

**14 November 2026.** Branch `research/memory-ablation-2026-11`. Everything here is **exploratory**: development splits, one model family, mostly greedy decoding. No sealed set was opened.

## 1. Outcome in one paragraph

The original Phase 1 candidate, RCS, enforces resolution at the terminal action. It helps small models (R − G: +18 pp at 3B, +12 pp at 7B, ≈ 0 at 8B and 14B), but it is not novel: R3 is DISCERN's EarnedAbstainGate. The completed pilot found a larger and more important effect: **metadata-derived reliability labels harm every model ≤ 8B when the metadata cannot order the records** (Qwen2.5-7B same-day corrections: 22/24 → 3/24; G − B on S7/S8 −50 pp, family p = 0.004). Enforcement cannot repair this, because it reads the same labels.

A read-time arbiter that states the **evidence basis** of each label (TEA) removes most of that harm on held-out phrasings:
- p1hold TEA-resolvable tasks: +72 to +89 pp at 7B and 8B under advice, and +83 pp at 3B under enforcement.

It also exposes the counterpart risk:
- **enforcement turns the arbiter's own false resolutions into harmful answers at every size** (5–6 of 6 negated-cue conflicts become arbitrary picks);
- the best delivery depends on capacity: enforce at 3B, advise at ≥ 7B.

The defensible contribution is the measurement of label-induced harm and of enforcement's amplification of label errors, together with evidence-basis labels and basis-gated enforcement, which Phase 2 must test. Bitemporal ordering itself is DISCERN's and is not claimed.

## 2. Completion criteria (from the brief)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Exact status of all previously launched runs | **Done** | `PILOT_RESULTS.md` §1; `HPC_RESOURCE_SHARING.md` §2 |
| 2 | Preserve and hash-verify all pilot outputs | **Done.** 42 + 26 files node = laptop; `HASH_MANIFEST.txt` | §1, §5 of `PILOT_RESULTS.md` |
| 3 | Analyse every available pilot configuration | **Done:** A, B, E, G, R (8 runs) and B, G, R, T, RT (6 runs) | `data/pilot_deep_tables.md`, `data/pilot_tables.md` |
| 4 | Failure cases with task identifiers | **Done:** M8–M14 with run and task ids | `FAILURE_TAXONOMY.md` §6 |
| 5 | Compare with the closest related work | **Done.** Six papers in full text on 13 Nov; DISCERN and STALE re-read on 14 Nov for the temporal question | `RELATED_WORK_DEEP_DIVE.md` §1–§4 |
| 6 | Is RCS sufficiently novel? | **No**, not on its own | `CANDIDATE_MECHANISMS.md` addendum |
| 7 | Defensible direction chosen | **Done** | `SELECTED_RESEARCH_DIRECTION.md` §A |
| 8 | Working, isolated prototype | **Done.** `prototype/tea.py` + `rcs.py`; frozen harness untouched; 21 fixture tests pass | `prototype/test_tea.py`, `test_rcs.py` |
| 9 | Positive and negative effects evaluated | **Done**, on development data | `PILOT_RESULTS.md` §3, §5 |
| 10 | Rigorous Phase 2 design | **Done** (v2) | `EXPERIMENTAL_RESEARCH_DESIGN.md` |
| 11 | HPC sharing with Veriflow documented | **Done** | `HPC_RESOURCE_SHARING.md` |
| 12 | Reproducible, resumable repository state | **Done.** Scripts regenerate every table; runs are resumable; a local commit is listed in §8 | §7 |

**Phase 1 is complete as a development phase.** It is *not* complete in any confirmatory sense, and nothing in it may be reported as a validated result. In particular:
- TEA was never run with seeds;
- there was no second model family;
- TEA's lexicon and both development splits share one author;
- basis-gated enforcement (H5), the most promising mechanism, is designed but not implemented.

## 3. Runs (all complete; none failed; none missing)

| Group | Runs | Where |
|---|---|---|
| 13 Nov, outside Slurm (controller down) | `p1_qwen25_{3b,7b}_{greedy,T07_s1,T07_s2}`, `p1_qwen25_14b_greedy`, `p1_qwen3_8b_greedy`: 8 × 320 runs, plus a 40-run smoke test | `raw_pilot/`, `logs/queue_gpu{0,1}.log` |
| 14 Nov, Slurm job 4173, one GPU | `p1_{qwen25_3b,qwen25_7b,qwen3_8b}_greedy_tea` (3 × 128), `p1h_{…}_greedy` (3 × 240) | `raw_pilot/`, `logs/tea_pilot_4173.*` |

## 4. Headline exploratory results (denominators in `PILOT_RESULTS.md`)

| Finding | 3B | 7B | Q3-8B | 14B |
|---|---|---|---|---|
| R − G, p1dev (task mean over decodings) | **+18.2 pp** (p = 0.029) | **+11.5 pp** (p = 0.010) | 0 | +3.1 |
| G − B on S7/S8 (label harm) | −22.9 | **−50.0** (p = 0.004) | −31.2 | +6.2 |
| p1dev greedy G → T → RT | 24 → 28 → **53** | 38 → 49 → **60** | 48 → **64** → 64 | not run |
| p1hold B / G / R / T / RT (of 48) | 17 / 18 / 23 / 21 / **35** | 20 / 24 / 25 / **36** / 34 | 22 / 24 / 24 / **40** / 34 | not run |
| Correct conflicts lost to enforcement of a wrong TEA label (N3, of 6) | 5 | 5 | 6 | — |
| Correct abstentions broken by R3 | 5 (4 R + 1 RT) | 0 | 0 | 0 |
| Unsupported answers on should-abstain tasks | ≤ 2/30 in every config | ≤ 1/30 | 0 | 0 |

**The "88 unnecessary abstentions" figure is corrected:**
- it is 88 of 300 *runs*, 51 of which are the memoryless config A;
- with memory it is 37/240, of which 19 had all gold records in hand (`FAILURE_TAXONOMY.md` §6.1).

## 5. Did the mechanism improve reliability overall?

**Yes, on development data, with conditions:**
- **RT is the best configuration at 3B** on both splits.
- **T is the best at 7B and 8B on the held-out split.**
- Neither raised unsupported answers.
- TEA labels never changed a status without a text basis (0 regressions across p1dev, p1hold and eval2).

**Negative effects:**
- enforcement converts every arbiter false resolution into a harmful answer (M11);
- enforcement of misleading metadata produces stale answers (M12);
- R3 breaks correct abstentions at 3B (M10);
- the arbiter misses non-ISO validity cues it was not written for ("As at", "Disregard … confirmed");
- corrections that do not name the old value stay `conflicting` and still cause label harm (M14);
- RCS notice text is wrong for same-date corrections (architecture item 15).

## 6. Strongest defensible contribution

1. **Measurement:**
   - the downstream cost of confident reliability labels when metadata is insufficient or wrong, on 3B–14B open-weight tool agents;
   - the cost is large below 14B, it is cautionary-label-driven, and enforcement cannot remove it.
2. **Measurement:**
   - enforcement benefit is capacity-dependent (needed at 3B, unnecessary at ≥ 8B);
   - enforcement **amplifies** label errors in both directions.
3. **Mechanism, to be validated:**
   - evidence-basis labels (TEA), plus enforcement gated on basis and capacity;
   - **with the arbiter's precision reported as a first-class quantity, against an LLM-extractor baseline** (DISCERN/CUPMem style).

## 7. Reproduce

From `research/AGENTRUN_PUBLICATION_2026/`, with Python 3.11 on the laptop and no GPU.

Fixture tests:

```bash
py -3.11 -m pytest PHASE1/prototype/test_rcs.py PHASE1/prototype/test_tea.py -q
```

Arbiter accuracy on p1dev, p1hold and eval2:

```bash
py -3.11 PHASE1/scripts/arbiter_offline_eval.py
```

All pilot tables:

```bash
py -3.11 PHASE1/scripts/pilot_deep_analysis.py
```

Per-run tables:

```bash
py -3.11 PHASE1/scripts/analyze_pilot.py
```

Hash manifest:

```bash
py -3.11 PHASE1/scripts/make_manifest.py
```

**Line endings.** `HASH_MANIFEST.txt` is checkout-independent and equals the sha256 of the committed git blobs:
- raw `*.jsonl` files are hashed byte for byte; they are `-text` in `.gitattributes`, so they are never converted;
- all other files are hashed with CRLF normalised to LF.

Verify any checkout with:

```bash
py -3.11 PHASE1/scripts/make_manifest.py --check
```

On the cluster, through Slurm, one GPU (resumable; check `HPC_RESOURCE_SHARING.md` §7 first). From `PHASE1/`:

```bash
sbatch prototype/tea_pilot.sbatch
```

## 8. Remaining blockers and open items

- **Second model family:** Llama snapshots on `sit-gpu` look incomplete. They need a load test or a download (Phase 2 step 2.5).
- **Phrasing independence:** a third development split written by someone other than the arbiter's author (Phase 2 step 2.6).
- **Compute:** the Phase 3 estimate is about 130 GPU-hours. It needs an agreed window with Veriflow, which currently runs one GPU at a time through Slurm.
- **Veriflow's next GPU need is unknown.** Recheck before every submission.
- **Keys:** the ngrok and Tavily keys in public git history (memory note from October) still need rotating by the user. This is unrelated to Phase 1.
- **Nothing has been pushed.** The local commit is described in the session handoff.
