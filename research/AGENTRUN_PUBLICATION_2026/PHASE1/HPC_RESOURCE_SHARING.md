# HPC resource sharing: AGENTRUN and Veriflow on SIT HPC

**14 November 2026 (UTC).** Every observation below came from read-only commands, listed in §6. No Veriflow or BeyondSilence process, file or job was signalled, modified or read beyond directory listings, Slurm scripts and one validation JSON.

## 1. Infrastructure as observed

| Item | Observed (14 Nov, 02:57–03:08 UTC) |
|---|---|
| Login/controller node | `<cluster-login>`, <cluster-login>. Slurm works: `squeue`, `sinfo` and `sbatch` respond |
| Compute node | `<compute-node>`, <compute-node>: 2 × L40, 96 CPUs, ~504 GB RAM; up 52 days; load average 0.01 |
| Partition | `gpu-nodes`, `Gres=gpu:2` |
| NVML | `nvidia-smi` still fails: "Driver/library version mismatch" (NVML 580.178). CUDA works through PyTorch, so `nvidia-smi` cannot be used to see VRAM |
| Slurm accounting | Disabled (`sacct` does not work). Jobs are tracked with `squeue` and the job's own logs and manifests |

**Slurm status change.** On 13 Nov the previous session found the Slurm controller down. It therefore ran the pilot queues directly on `<compute-node>` with `launch_pilot.sh`, outside Slurm. On 14 Nov the controller works. **From now on every AGENTRUN GPU workload goes through `sbatch`.** `launch_pilot.sh` is kept only as the record of how the 13 Nov runs were made; do not use it again while Slurm is up.

## 2. Previous AGENTRUN processes (13 Nov pilot)

The brief listed PIDs 1860975 and 1860976 (launchers), 1870401 (14B) and 1878788 (Qwen3-8B). None was matched by PID. Processes were identified by command line, owner and start time instead:

- **On `<compute-node>`:** the only user process apart from the session daemons and the diagnostic shell was the BeyondSilence recognition service (§3). There was no `python run_pilot.py`, no `launch_pilot.sh` and no other AGENTRUN process.
- **On the login node:** no user processes.
- **No process held a `/dev/nvidia*` file descriptor** among the processes visible to `<user>`.

**The queue logs show both launchers finished normally:**

- `logs/queue_gpu0.log`: `queue 0 finished 2026-11-13T14:35:26+00:00`
- `logs/queue_gpu1.log`: `queue 1 finished 2026-11-13T14:00:13+00:00`

Every run printed `exit=0`. Nothing needed resuming, and nothing was relaunched. See `PILOT_RESULTS.md` §1.

## 3. Other projects' observed resource use

### Veriflow (`~/VERIFLOW`)

**How it schedules.** Only through Slurm:

- `slurm/*.sbatch`: `--partition=gpu-nodes --nodelist=<compute-node> --gres=gpu:1`, 8 CPUs, 16–64 GB RAM, time limits from 15 min to 4 h.
- Its array script states its own policy: "Always one at a time", submitted with `--array=…%1`.

**Most recent work.**
- A 96-run grid, Slurm array job **4036** (task 0 = job 4037), commit `540206c`.
- Validation output `.tmp/validate_grid_check.json`: 96/96 runs OK.
- Per run: median wall time 160 s, about 4.35 GPU-hours in total, peak VRAM **41,875 MiB** (one L40 is 46,068 MiB).
- `results/grid/analysis.json` and `runs.csv` were written at **02:55:54 UTC on 14 Nov**, two minutes before this session's first check. `.git/FETCH_HEAD` was updated at 02:55:53.
- Veriflow is therefore **actively being worked on** (analysis stage), even though no Veriflow job or process was running.

**At 02:58 and again at 03:07:30 UTC:**
- `squeue` was empty;
- `<compute-node>` was `idle` with 0/96 CPUs and 0/2 GPUs allocated;
- no Veriflow process existed on either node.

**Near-term need.** Unknown. The grid analysis just finished, so a new array could be submitted at any time. Given its policy it would most likely need **one GPU at a time**, using up to about 42 GB VRAM.

### BeyondSilence

`recog_service.py` (PID 3769902, running since 24 Oct, venv `beyondsilence-work/venv-service310`). It held no `/dev/nvidia*` descriptor; it was not touched.

### ErrorEcho, cornea-work and others

Directories exist in the home directory. No processes or jobs were seen. They were not inspected.

## 4. Coordination strategy

1. **One GPU at most for AGENTRUN, through Slurm.**
   - One job with `--gres=gpu:1` and a hard `--time`.
   - Models run *sequentially* inside it; no arrays with `%2`; no second concurrent job.
   - The other L40 always stays free for Veriflow.
2. **Check before every submission.** Run `squeue -a`, `sinfo -N`, and look for recent Veriflow writes. Submit only if no job is pending for a GPU and none is pending for Veriflow.
   - If Veriflow has a job pending or running on one GPU, AGENTRUN may use the other only if no Veriflow job is pending.
   - If Veriflow has jobs pending or needs both GPUs, **AGENTRUN does not submit** and continues CPU-only (analysis, offline arbiter evaluation, documentation).
3. **Slurm arbitrates.** If Veriflow submits while AGENTRUN holds one GPU, Slurm gives Veriflow the other GPU. AGENTRUN never uses `--exclusive`, never asks for 2 GPUs, and never runs on the node outside Slurm.
4. **Bounded jobs.** Phase 1 jobs are capped at 3 h. Phase 2 jobs must be split into units of ≤ 4 h. They are resumable: finished `(task, config)` pairs are skipped on resubmission.
5. **Never:** signal, suspend, renice, `scancel` or `scontrol update` another project's job; touch drivers; or read or write outside `~/AGENTRUN_HPC`.

## 5. AGENTRUN GPU use in this session

| Job | Submitted (UTC) | Resources | Content | State |
|---|---|---|---|---|
| **4173** `agentrun-p1-tea` | 2026-11-14 03:07:59; queue empty, node idle at 03:07:30 | 1 × L40 (`CUDA_VISIBLE_DEVICES=0`), 8 CPUs, 48 GB, `--time=03:00:00` | TEA follow-up: Qwen2.5-3B, Qwen2.5-7B, Qwen3-8B greedy, one after another; p1dev T/RT + p1hold B/G/R/T/RT | **Completed 04:09:09 UTC** (61 min on GPU 0; all six runs `exit=0`; queue empty afterwards). See `PILOT_RESULTS.md` §5 |

**During job 4173:**
- Veriflow wrote analysis files (`results/grid/supplement.json`, `validate_grid.json` at 03:07 UTC) but submitted no Slurm job.
- GPU 1 stayed unallocated for the whole job.
- **Total AGENTRUN GPU use on 14 Nov: about 1.0 GPU-hour.**

**Periods when AGENTRUN waited.** None was needed: the queue was empty when the job was submitted. The 14B follow-up was deliberately **not** run (about 2.7 GPU-hours). 14B was not affected by the misleading labels in the first pilot, so it would add little.

**GPU use on 13 Nov (previous session, outside Slurm).** Both GPUs were used by two direct queues, 11:24–14:35 UTC; queue 0 used 3.2 h and queue 1 used 2.6 h. At that time no Veriflow job was visible, but the controller was down, so Veriflow could not have submitted either. **That use of both GPUs is not repeated.**

## 6. Read-only diagnostic commands used

On `<compute-node>`, through `ssh <user>@<compute-node>`:

```bash
hostname; date; uptime
ps -eo pid,ppid,user,lstart,etime,stat,pcpu,pmem,rss,args --sort=pid
ps -u <user> -o pid,lstart,etime,stat,args
for p in /proc/[0-9]*; do ls -l $p/fd 2>/dev/null | grep -q /dev/nvidia && echo "$(basename $p) $(tr '\0' ' ' < $p/cmdline)"; done
nvidia-smi
```

Pilot outputs on the node, relative to `~/AGENTRUN_HPC/20261111/source/research/AGENTRUN_PUBLICATION_2026/PHASE1`:

```bash
ls -la --time-style=full-iso logs raw_pilot/*
wc -l raw_pilot/*/*.jsonl
grep -hE "^(start|exit=|queue|Traceback)" logs/*.log
cat raw_pilot/*/DONE raw_pilot/*/manifest.jsonl
sha256sum raw_pilot/*/* logs/* prototype/*
```

On `<cluster-login>`, through `ssh <user>@<cluster-login>`:

```bash
squeue -a -o "%.10i %.12P %.30j %.10u %.8T %.10M %.6D %R %b"
sinfo -N -o "%N %P %T %G %C %m"
scontrol show node <compute-node>
ps -u <user> -o pid,lstart,etime,args
```

Veriflow, metadata only:

```bash
ls -la --time-style=full-iso ~/VERIFLOW ~/VERIFLOW/results/* ~/VERIFLOW/slurm ~/VERIFLOW/.tmp
git -C ~/VERIFLOW log -5 --format="%h %ci %s"
grep -h "^#SBATCH" ~/VERIFLOW/slurm/*
cat ~/VERIFLOW/slurm/grpo_array.sbatch
python3 -c "<read .tmp/validate_grid_check.json: n runs, max peak_vram_mib, median wall_seconds>"
```

AGENTRUN submission, with the check in the same command:

```bash
Q=$(squeue -h -a | wc -l); if [ "$Q" = "0" ]; then sbatch prototype/tea_pilot.sbatch; fi
```

## 7. Before the next AGENTRUN GPU job

```bash
ssh <user>@<cluster-login> 'squeue -a; sinfo -N -o "%N %T %G %C"; ls -la --time-style=full-iso ~/VERIFLOW/results/* ~/VERIFLOW/logs/slurm | tail'
```

**Submit only if:**
- no job is pending;
- at most one GPU is allocated;
- the new job asks for `--gres=gpu:1` with a `--time` limit.
