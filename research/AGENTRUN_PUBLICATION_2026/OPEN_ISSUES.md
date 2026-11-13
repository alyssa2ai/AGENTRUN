# Open issues

**13 November 2026.** Ordered by how much each one blocks publication. "Owner" means who has to act.

| # | Issue | Blocks | Owner | Next action |
|---|---|---|---|---|
| 1 | **Slurm controller down** at `sitgpumaster` (192.168.192.11). `scontrol ping`: "Slurmctld(primary) at sitgpumaster is DOWN"; login node port 22 unreachable. Compute node `sit-gpu` is up | E0–E5, every new experiment | SIT HPC administrator | Report it to the administrator. When it is back, run `squeue`, then submit only indices 14–20 (`EXPERIMENT_ROADMAP.md` E0) |
| 2 | **No untouched test set for the memory study.** eval2 (96 tasks) is now a validation set | Any confirmatory claim | Researcher | Build, freeze and seal eval3 with held-out templates (E1); pre-register |
| 3 | **Closest papers read from abstracts only.** DISCERN (2611.15729, posted 11 Nov 2026), PACMI, AMV-Guard, GPM, STALE, CICM | Related work; final novelty verdict | Researcher | Read the full texts. Check whether any already reports a component-by-capacity ablation |
| 4 | **Single model family and greedy decoding.** Capacity claims rest on Qwen2.5 alone (plus one Qwen3 size); no variance estimate | H2, generality | Researcher + HPC | E2; jobs 19–20 give a first variance estimate |
| 5 | **Gate depends on clean structured metadata** (`recorded_on`, `attribute`) | External validity of the gate result | Researcher | E3 (free-text and noisy-timestamp memories) |
| 6 | **Harness effect mechanism unknown.** v2 adds a repair turn and two rules; the repair turn fired in 14 runs | H5 interpretation | HPC | Job 15/16 (v1r) |
| 7 | **v1 text-verifier penalty not robust** (exact family sign-flip p = 0.094). Earlier documents present it as established (`PROJECT_AUDIT.md`, MITACS dossier) | Accuracy of claims | Researcher | Use the corrected wording from `STATISTICAL_AUDIT.md` §3 in any future text |
| 8 | **Multiplicity.** Under Holm correction only 3 of 14 headline contrasts survive; under Benjamini–Hochberg, 10 do | Claim strength | Researcher | Pre-register the primary contrasts for eval3 |
| 9 | **No human validation of the scorer.** One known issue: empty-value `answer` outcomes are counted as harmful | Outcome taxonomy | Researcher | E6 (no GPU needed) |
| 10 | **No external benchmark** | External validity | Researcher | E4 (STALE or MemoryAgentBench with the last-write baseline); check licences first |
| 11 | **Sealed benchmark-v2 test set stored inside the working tree** (`.sealed/`, git-ignored). Never read beyond a count and field names | Integrity of thread-1 confirmatory test | Researcher | Move it outside the repository; re-verify the hashes against `SEAL.json` afterwards |
| 12 | **Leaked keys in public git history** (ngrok and two Tavily dev keys; from `PROJECT_AUDIT.md`) | Any public release | Researcher | Rotate the keys. History was deliberately not rewritten |
| 13 | **Uncommitted thread-1 work** (`agentrun_v2/`, `benchmark_v2/`, docs, tests, `.gitignore`/`README.md` changes) | Reproducibility of thread 1 | Researcher | Review and commit separately; not touched by this audit |
| 14 | **14B-specific artefacts**: Thai-language final answers, calculator `round()` rejections (about 20 step-limit failures per harness) | Interpretation of the 14B end of the curve | Researcher | Fix the tool or prompt in a new harness version for eval3, and declare the fix in the pre-registration |
| 15 | **Branch not pushed** (by instruction). Only local and cluster copies of the raw data exist, plus the cluster backup with SHA256SUMS | Data durability | Researcher | Push or archive when the researcher decides |
| 16 | **Hosted-model runs** (Campaign 1) used an endpoint that may change | Reproducibility of those runs | none | Report as non-reproducible; do not rely on them |
