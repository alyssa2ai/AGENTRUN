# Persistent-memory reliability study (2026-11)

A pre-registered evaluation of **evidence-basis arbitration with gated enforcement** for small open-weight
tool-using agents whose persistent memory contains records that disagree.

This directory is **Study 2** of this repository. It is unrelated to the QLoRA specialization work at the
repository root: different question, different models, different benchmark, different code. Results are never
pooled across the two.

> **Status: complete, self-reported, not peer reviewed, not submitted anywhere.** See
> [`../../PUBLICATION_STATUS.md`](../../PUBLICATION_STATUS.md).

## The question

An agent with persistent memory will eventually read two records that disagree. The usual engineering answer is
to label records by reliability — derived from when each was written — and to enforce those labels at the terminal
action. For small models, both halves of that answer can misfire.

The study asks: **does arbitration that reports the *evidence basis* for each resolution, and enforces only what
that basis supports, improve reliability — and can indiscriminate enforcement of memory labels cause more harmful
answers despite improving raw accuracy?**

Both halves got an answer, and they do not point the same way. The four pre-registered contrasts are supported.
But removing the evidence gate, so that every arbitration is enforced, scored **9.7 percentage points higher** on
task success while more than doubling the harmful-answer rate. Gating is a trade, not a dominance.

## What was frozen, and when

| | Date | Recorded as |
|---|---|---|
| Mechanism (Evarb-0.2) | 2026-11-14 | `PHASE2/FREEZE_evarb.json` — 9 modules, runner, analysis script, 3 dependencies |
| Evaluation set (eval3) | 2026-11-16 | `PHASE2/FREEZE_eval3.json` — hashes only; contents withheld |
| Pre-registration | 2026-11-17 | `PHASE2/PREREGISTRATION.md`, its SHA-256 recorded in the seal manifest |

Every job refused to start unless all three matched. All 20 job starts of the campaign passed all three.

## Directory map

| Path | Contents |
|---|---|
| `PHASE1/prototype/` | `rcs.py` and `tea.py`, the two Phase 1 comparison mechanisms, plus the held-out split builder. Two of the 14 hash-frozen files |
| `PHASE2/` | the frozen mechanism `evarb/` (arbiter, policy, cues, rendering, LLM-arbiter baseline), the runner and analysis scripts, the benchmark builders, the pre-registration, freeze records and specifications, and the test suite |
| `PHASE3/` | the confirmatory campaign: `PHASE3_FINAL_REPORT.md`, `PHASE3_STATISTICAL_ANALYSIS.md`, comparison and ablation tables, `PHASE3_FAILURE_ANALYSIS.md`, `PHASE3_DEVIATIONS.md`, the G4 forensic report, machine-readable verdicts in `PHASE3_DECISIONS.json`, result CSVs in `results/`, and `PHASE3_SHA256_MANIFEST.txt` |
| `PHASE4/` | the long-form manuscript (`manuscript/`) and the reproducibility package (`reproducibility/`) |
| `PHASE5_PUBLICATION/` | the typeset paper: LaTeX source, bibliography, nine vector figures with their generated data, the supplement, the QA report, and the compiled PDFs in `build/` |
| `FINAL_COMPLETION_REPORT.md` | end-to-end account of the campaign, its integrity results, deviations and open items |

The harness (`memlab.py`) and the model client (`hf_client.py`) are the other two off-tree hash-frozen files; they
live in `../AGENTRUN_DEEPENING_2026-11-11/scripts/`.

## Start here

- **The paper:** `PHASE5_PUBLICATION/build/main.pdf` (30 pp) and `build/supplementary.pdf` (9 pp).
- **The numbers, machine-readable:** `PHASE3/PHASE3_DECISIONS.json` and `PHASE3/results/*.csv`.
- **What went wrong and what it cost:** `PHASE3/PHASE3_DEVIATIONS.md`.
- **How to reproduce:** `PHASE4/reproducibility/README.md`.

## The twelve conditions

All twelve run in every one of the 18 cells. `EBG` is the proposed condition; `RT` is the pre-registered primary
comparator.

| | Labels shown | Enforcement |
|---|---|---|
| `B` | none | — |
| `G` / `R` | metadata (record date) | — / every label |
| `T` / `RT` | lexical temporal arbiter | — / every label |
| `LA` / `LG` | the agent's own model as arbiter | — / gated |
| `EB` | evidence basis | — |
| **`EBG`** | **evidence basis** | **gated: strong strength only** |
| `EBG-all` | evidence basis | strong *and* moderate |
| `EBG-unsafe`, `EBG-noR3` | evidence basis | gated, minus one component each |

## Scale and integrity

57,888 runs across 18 cells, with **0 missing pairs, 0 duplicates, 0 unparsable lines and 0 harness errors**. Four
integrity gates ran before any analysis: every cell complete, exact row counts, clean exits, and a run identity —
model, snapshot, decoding, seed, dtype, parser, framework versions and the hashes of all 14 mechanism files —
constant across every start of a cell. An independent re-implementation recomputed the headline counts and effect
sizes by a different route and agrees exactly.

One deviation is recorded rather than smoothed over: an unplanned compute-node reboot changed the host kernel and
GPU driver partway through two cells, affecting 1.69% of rows. Removing the affected cell moves the pooled
estimates by at most 0.1 pp, but whether the driver change altered generation **cannot be established** from this
campaign, and the paper says so.

## Running the tests

```bash
cd research/AGENTRUN_PUBLICATION_2026/PHASE2 && python -m pytest tests -q
```

```bash
cd research/AGENTRUN_PUBLICATION_2026 && python -m pytest PHASE3/tests -q
```

`PHASE2/tests/test_clients.py` needs the `agentrun_v2` parser package, which is not part of this release; it is
reported as a known skip rather than hidden. Everything it exercises is pinned by hash in every run manifest.

## What is not here

The confirmatory evaluation items, their annotations and the per-run transcripts are withheld until publication so
the test set stays uncontaminated; their hashes are public in `PHASE2/FREEZE_eval3.json`. Cluster job logs are
withheld because their progress lines carry per-task outcomes. Development splits and their runs, and the raw
per-run outputs, are also not in this release. Model weights are not redistributed. No credentials, host names,
addresses or account identifiers appear anywhere in this release.
