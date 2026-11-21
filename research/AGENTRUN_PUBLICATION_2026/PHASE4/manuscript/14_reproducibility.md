# 14. Reproducibility and artifact availability

## 14.1 What was frozen, and when

| Item | Frozen as | Date |
|---|---|---|
| Mechanism (Evarb-0.2) | `FREEZE_evarb.json`: 9 modules, the runner, the analysis script, the component evaluator, 3 frozen dependencies | 2026-11-14 |
| Evaluation data (eval3) | sealed on the cluster; hashes in `FREEZE_eval3.json` | 2026-11-16 |
| Preregistration | SHA-256 `221013b3…` recorded in `FREEZE_eval3.json` | 2026-11-17 |

Every Phase 3 job refused to start unless the `evarb-0.2` files matched `FREEZE_evarb.json`, the sealed eval3
directory passed `sha256sum -c`, and the preregistration's hash equalled the value recorded at the freeze. All 20
job starts of the campaign printed `freeze evarb-0.2 mismatches []` and the sealed preregistration hash. The runner
additionally refused any task file whose hash differed from the sealed one.

## 14.2 Provenance of every row

Each cell writes a manifest line at every start recording the model identity and resolved snapshot path, the PEFT
adapter (none here) and its hash, decoding parameters and seed, dtype, maximum new tokens, parser version, family
adapter, `torch`, `transformers` and CUDA runtime versions, the GPU model, the split hash, the configuration list,
the SHA-256 of all 14 mechanism and harness files, the Slurm job id, the start time, and how many pairs were already
complete at that start. The 14 code hashes are identical across all 20 starts. A SHA-256 manifest of every raw file
is written when the campaign closes, and re-verified by the finalization job before anything is analysed.

## 14.3 Regenerating every number

The whole pipeline runs as one CPU-only Slurm job with no interactive steps:

```bash
cd research/AGENTRUN_PUBLICATION_2026/PHASE3
sbatch scripts/phase3_finalize.sbatch     # gates -> stage -> platform report -> verify -> analyze
                                          #       -> exploratory -> report -> results draft -> seal -> commit
```

or stage by stage from an existing checkout of the raw outputs:

```bash
bash scripts/run_phase3_analysis.sh verify       # completeness, freeze, preregistration and client-identity checks
bash scripts/run_phase3_analysis.sh analyze      # frozen analyze_p2.py, 100,000 seeded permutations, Holm
bash scripts/run_phase3_analysis.sh exploratory  # the two post-hoc sensitivity analyses (Section 8.4)
bash scripts/run_phase3_analysis.sh report       # independent cross-check, then tables and CSVs
```

Every reported number comes from that path. An independent re-computation of the per-configuration counts and the
four primary effect sizes must agree exactly or the pipeline stops; the report generator computes no statistic of
its own. On the shareable development split the same pipeline reproduces its outputs byte for byte.

## 14.4 What a reproduction can and cannot match

The analysis is reproducible byte for byte from the archived raw outputs: the permutations and bootstraps are
seeded, and the gates re-verify the inputs first.

Regenerating the *raw outputs* is a weaker guarantee, and this campaign has three specific caveats, all recorded in
`PHASE3/PHASE3_DEVIATIONS.md` and summarised in Section 11:

1. GPU kernels are not bitwise deterministic across hardware or library versions, so a re-run elsewhere may differ
   at the token level for some runs.
2. Two cells — `qwen3_8b_T07_s3` and `llama32_3b_greedy` — were not produced on a single host platform, because the
   node rebooted into a new kernel and NVIDIA driver partway through them. They cannot be reproduced row for row on
   one fixed driver version. The other sixteen cells were produced on one platform throughout.
3. `qwen3_8b_T07_s3` additionally re-seeded its sampler when it resumed at row 2345, so reproducing that cell byte
   for byte would require reproducing the interruption at the same row.

## 14.5 Availability

- **Released with the repository:** the code (mechanism, harness, runner, analysis, integrity gates, tests), the
  frozen manifests, the preregistration, the development splits and their runs, all aggregate Phase 3 results
  (JSON and CSV), the Phase 3 reports, the deviation ledger, the forensic report and the platform-continuity report,
  and the reproducibility package in `PHASE4/reproducibility/` (environment, model snapshots, dataset rules, Slurm
  scripts, analysis instructions, expected outputs, tests, limitations, deviations, SHA-256 manifests).
- **Withheld until publication:** the confirmatory eval3 items, their annotations and the per-run transcripts, so
  that the test set stays uncontaminated. Their hashes are public in `FREEZE_eval3.json`, so a later release can be
  checked against the frozen versions. The cluster's per-run logs are withheld for the same reason, since their
  progress lines carry per-task outcomes.
- **Not redistributed:** model weights. The exact Hugging Face snapshot hashes are listed in
  `PHASE4/reproducibility/MODELS.md`; obtain the weights under each model's own licence. Because the eval3 texts
  were written by Qwen2.5-14B-Instruct, the Qwen licence terms on model outputs apply to them.
- The package contains no credentials, tokens, API keys, host names, IP addresses or user identifiers; commands use
  `<user>@<cluster-login>` and `$HOME/AGENTRUN_HPC` as placeholders.

Nothing in this section claims public availability for an artifact that is in fact restricted: the eval3 items, the
annotations, the per-run transcripts and the cluster logs are restricted today, and the table above says so.
