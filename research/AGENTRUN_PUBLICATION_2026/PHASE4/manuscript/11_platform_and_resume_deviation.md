# 11. Platform and resume deviation analysis

Two of the eighteen cells were interrupted by an unplanned reboot of the compute node and finished on a changed host
platform. This section states what happened, what it is known to have affected, and what cannot be established from
the data. Nothing in it changes the preregistered analysis; the full ledger is in `PHASE3/PHASE3_DEVIATIONS.md` and
the underlying investigation in `PHASE3/PHASE3_G4_FORENSIC_REPORT.md`.

## 11.1 How the deviation surfaced

The finalization job stopped at its integrity gates with two failures of the form *"manifest field `client` differs
between starts"*, for `qwen3_8b_T07_s3` and `llama32_3b_greedy`. The gate compared the manifest's `client` object as
a single opaque JSON blob, so it could not distinguish a change of client implementation from a change in read-only
host telemetry, and its message named neither the subfield nor the values.

A field-level comparison of the four manifest lines showed one differing subfield, in both cells:
`client.gpu_mem_gib`, from 44.6 to 44.4. That field is the device's total memory as the driver reports it,
`round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1)`. It is stored in the client's version record and
read only when the manifest is written; the model is loaded with an explicit device map and no memory budget, so the
value cannot influence placement, offloading, batching or generation. Every field that determines what was executed
— model, snapshot path, adapter, dtype, temperature, seed, decoding, maximum new tokens, parser version, family
adapter, torch, transformers, CUDA runtime — is identical across the two starts of both cells, as are the split hash,
the configuration list and the 14 frozen code hashes, which are in fact identical across all 20 starts of the
campaign.

## 11.2 What actually changed

The compute node rebooted at 2026-11-20T10:11:58, having been up since 2026-10-03. Across that reboot the host
Linux kernel and the NVIDIA kernel driver both changed. The post-reboot state is directly verified
(kernel 6.8.0-149-generic; NVIDIA module 580.178.04, loaded at 10:12:02). The pre-reboot state is **inferred**, not
read: the node booted before the NVIDIA packages were upgraded on 2026-10-11 from 580.173.02 to 580.178.04, so it
continued running the already-loaded 580.173.02 module against newer userspace — which is corroborated by the
recorded failure of `nvidia-smi` on this node on 2026-11-11 with a driver/library version mismatch, and by the same
command working after the reboot. The previous boot's kernel log is not readable from the account used, so this
remains an inference. The 0.2 GiB difference in reported device memory is consistent with a driver revision changing
its reserved carve-out; device identity is excluded, because both GPUs report identical totals and the two affected
cells occupied different devices in both of their starts.

The reboot also truncated the row being written in each of the two in-flight cells. Slurm requeued both jobs; both
failed immediately in the resume path on the truncated line; the controller quarantined the damaged tail — 1153 and
3617 bytes, each containing zero complete rows — and resubmitted. Both cells then completed to the full 3216 rows
with no duplicates. One collateral loss is permanent: Slurm's requeue overwrote the console logs of the two
interrupted starts. Their manifest lines survive with the code hashes and freeze state intact.

## 11.3 Scope, and why the contrasts are not confounded by it

| | `qwen3_8b_T07_s3` | `llama32_3b_greedy` | Campaign |
|---|---|---|---|
| Rows on the old platform | 2345 | 3107 | 56,908 (98.3%) |
| Rows on the new platform | 871 (27.1%) | 109 (3.4%) | **980 (1.69%)** |
| Whole tasks on the new platform | 72 | 9 | — |
| Tasks split across platforms | 1 (`eval3-0202`) | 1 (`eval3-0267`) | **2 of 268** |

The other sixteen cells finished before the reboot. Because the runner's outer loop is over tasks and its inner loop
over the 12 configurations, a resumed segment carries all 12 configurations for every whole task it contains: the
post-reboot segments are balanced across configurations to within one row per configuration. A platform-induced
shift would therefore move all twelve arms of a task together, which the paired, family-clustered design differences
out. The residual within-task confound is exactly the two boundary tasks named above, one in a single decoding of one
primary model and one in the never-pooled format-limited cell.

## 11.4 Resume and the random stream

The client seeds PyTorch once per process. A resume is a new process, so the post-resume segment of a sampled cell
restarts its sampling stream from the base seed instead of continuing it. Only `qwen3_8b_T07_s3` is affected: the
other resumed cell is greedy, and no other cell was resumed. This does not bias the sampling distribution — the
design fixes T = 0.7 with seeds 1, 2 and 3, and makes no claim about stream continuity — but it does mean that
reproducing that cell byte for byte now requires reproducing the interruption at the same row. It is recorded as a
reproducibility limitation rather than a validity threat.

## 11.5 Decision, and what remains unknown

Both cells are retained. The preregistration pins the mechanism, harness, runner, analysis and data — all
hash-verified identical across both starts — and pins the hardware only as "bf16, one L40", which held; the GPU
driver and host kernel are not pinned. Resume is explicitly provided for, and a restart is permitted only for a
freeze mismatch, a seal mismatch or a runner defect, none of which occurred. Re-running the two cells now would
additionally be a post-hoc choice taken with knowledge of which cells were affected.

What cannot be established from this campaign is whether the two driver versions produce different generations for
these models. No `(task, config)` pair exists on both platforms, because the quarantined fragments contain no
complete rows, so there is nothing to compare; settling it would require re-running completed cells. The exploratory
sensitivity analyses in Section 8.4 test whether the conclusions depend on the straddling cell, which is a weaker
and different question: agreement there is consistent with the transition being inert, but equally consistent with an
effect too small to move a family-clustered permutation test at this sample size, and it says nothing about the two
tasks whose own rows are split.

Two durable corrections follow from this episode rather than from any result. First, the integrity gate now
distinguishes client identity from host observation explicitly, fails closed on any unclassified field, and prints
the field and values on a mismatch. Second, a reporting-only platform-continuity check now derives, from the
manifests alone, which cells straddle a node boot, and records the surrounding facts separated into verified,
inferred and unknown — so that a platform transition can never again reach the analysis visible only as a rounding
difference in a telemetry field. The run manifest should also record the driver version, kernel release and boot
identifier; that is a change for future campaigns, since the Phase 3 manifests are frozen artefacts and were not
rewritten.
