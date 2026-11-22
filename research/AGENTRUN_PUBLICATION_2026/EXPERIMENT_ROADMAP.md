# Experiment roadmap

**13 November 2026.** Nothing in this file has been run. It is a plan.

**Order.** Experiments are listed in order of scientific priority. Each has a decision rule fixed before it runs.

**Compute estimates.** They come from the Campaign 2 wall-clock times on one L40 (from the Slurm logs), for one pass of 96 tasks × 5 configurations (480 runs):

| Model | Time per 480 runs |
|---|---|
| Qwen2.5-1.5B | 4–6 min |
| Qwen2.5-3B | 16–17 min |
| Qwen2.5-7B | ≈ 33 min |
| Qwen3-8B | 35–38 min |
| Qwen2.5-14B | 96–123 min |

Other families will differ.

**Blocker for all of them.** The SIT Slurm controller is down: `scontrol ping` reports "Slurmctld(primary) at <cluster-login> is DOWN" (13 Nov 2026, 10:45 UTC). Running directly on `<compute-node>` without the scheduler is **not** planned; that decision belongs to the cluster administrator and the researcher.

## E0. Finish the pre-registered Campaign 2 jobs (14–20)

- **What.** The jobs already defined in `hpc/campaign2.sbatch` and committed in `ca664fa` before any result:
  - 14: dense retriever with 2,000 padding records;
  - 15–16: harness v1r (repair only), 7B and 8B;
  - 17–18: V2 adapter on eval2, v1 and v2;
  - 19–20: harness v2 at T = 0.7, two seeds (Qwen2.5-7B only).
- **How.** Once the controller is back, check `squeue`. Confirm that indices 14–20 have no log or result folder, then submit **only** those indices:

  ```bash
  sbatch --array=14-20%2 hpc/campaign2.sbatch
  ```

  Do not resubmit 0–13.
- **Cost.** About 3.5–4 GPU-hours in total, about 2 hours of wall-clock time with two jobs at a time (estimate from the timings above).
- **Why first.**
  - Job 15 is the only way to attribute the harness effect (H5) to the repair turn or to the prompt rules.
  - Jobs 19–20 give the first estimate of decoding variance.
  - Job 14 completes the retriever comparison.
- **Caveat.** These run on eval2, which is now a validation set. Their results are exploratory.

## E1. New sealed memlab split (confirmatory set)

- **What.**
  - Generate `eval3` with a new seed, new entities and **held-out templates**: at least one scenario-variant family per scenario that does not occur in dev/eval/eval2.
  - Freeze it, hash it and store it outside the repository before any run.
  - Pre-register the hypotheses H1–H6, the primary contrasts and the analysis: family-level sign-flip tests, Benjamini–Hochberg across contrasts, per-scenario decomposition.
- **Size.** Aim for ≥40 families (to reach useful power for clustered tests), about 160–200 tasks.
- **Cost.** About 2× the eval2 cost per model.
- **Decision rule.** A hypothesis is "confirmed" only if its pre-registered contrast is significant on eval3 under the family-level test.

## E2. Second model family and sampled decoding

- **What.** Repeat A–E with one other open-weight family at about 3 sizes. Llama 3.x or Gemma are candidates; which are cached on the cluster must be checked, and none is assumed here.
- **Decoding.** Use ≥3 sampled seeds (T = 0.7) in addition to greedy.
- **Why.** H2 (capacity dependence) is confounded with Qwen2.5-specific behaviour, such as 14B's Thai answers and calculator `round()` calls.

## E3. Free-text and agent-written memory

- **What.** A variant of the stores in which records are free-text sentences written by the agent or by a paraphraser, with timestamps that are missing or noisy for a controlled fraction.
- **Why.** The gate reads the structured `recorded_on` and `attribute` fields; its benefit on clean metadata is an upper bound (`BENCHMARK_AND_LEAKAGE_AUDIT.md` §4).
- **Prediction (to test, not assumed).** The gate's advantage shrinks as metadata quality drops.

## E4. External benchmark

- **What.** Run the A–E ablation (or its applicable subset) on one public benchmark. Options:
  - **STALE**: State Resolution and Premise Resistance map to S4 and S5;
  - **MemoryAgentBench conflict split**, together with Pakhomov & Nijkamp's last-write baseline;
  - **ENT-310** (DISCERN), if released.
- **First step.** Check licences and data availability before committing.

## E5. Verifier controls

- **What.** Separate "verification" from "same-model verification":
  1. a verifier that sees provenance but is a different (larger) model;
  2. a verifier that only checks numeric consistency deterministically.
- **Why.** Tests whether the C − B harm comes from the same-model self-check (as the self-correction literature predicts) or from verification as such.

## E6. Scorer validation

- **What.** Human annotation of a stratified random sample: about 200 runs over scenarios × configurations × models, by two annotators, using `docs/annotation_guide.md` adapted to memlab. Report agreement with the scorer (Cohen's κ) and the confusion between harmful and safe-miss outcomes.
- **Note.** Needs no GPU; can be done while the cluster is down.

## E7 (optional). Stale-binding probe

- **What.** A CICM-style linear probe at 7B on S4 tasks: is the current value recoverable from hidden states when the model answers with the stale one?
- **Why.** Would explain why a deterministic gate helps at 7B. Only worth doing if E1–E4 confirm H3.

## Not recommended

- Re-running Campaign 2 jobs 0–13.
- More analysis passes on eval2 aimed at new hypotheses.
- Using benchmark v2's sealed test for the memory paper: it has no memory scenarios.
- Hosted frontier-model runs before E1: uncontrolled serving, cost.
