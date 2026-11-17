# AGENTRUN compute coordination (sit-gpu)

**Updated 16 November 2026, 09:40 UTC.** A copy is kept on the cluster at `~/AGENTRUN_HPC/COORDINATION.md` for the other projects' sessions.

## Current queue (observed)

| Job(s) | Project | Needs | State |
|---|---|---|---|
| 4196 `vne_compare` | another user (gpuuser16) | `--mem=0` = all 515 GB, 2 CPU, no GPU, 365-day limit | RUNNING; blocks every other job on the node. Reported to the administrators by the AGENTRUN owner on 16 Nov |
| 4199 → 4200 → 4201[0-2]%1 | AGENTRUN | 1 GPU at a time; 64 / 64 / 48 GB RAM; 4 CPUs; ≈ 0.6 h + 1 h + 6 h | PENDING (chained by dependencies; no duplicates will be submitted) |
| 4204–4212 | ErrorEcho | CPU only; 8–128 GB RAM each, 1–16 CPUs, chained | PENDING |
| — | Veriflow | nothing queued | — |

## Compatibility when 4196 releases memory

- **GPU:** only AGENTRUN requests a GPU, and only one (array `%1`, dependencies). One L40 stays free for Veriflow or anyone else.
- **Memory:** AGENTRUN ≤ 64 GB at a time; ErrorEcho's largest chained step is 128 GB. Together ≤ 192 GB of 515 GB.
- **CPU:** AGENTRUN 4; ErrorEcho ≤ 16 at a time. 96 available.
- No ordering between the projects is needed. AGENTRUN does not touch Veriflow, ErrorEcho or BeyondSilence files or processes.

## Phase 3 (not submitted)

≈ 109 GPU-hours on one GPU (≈ 4.5 days continuous) — `PHASE3_EXECUTION_PLAN.md`. Before submitting: re-check `squeue`, announce the window to the Veriflow and ErrorEcho owners, and keep `%1`.
