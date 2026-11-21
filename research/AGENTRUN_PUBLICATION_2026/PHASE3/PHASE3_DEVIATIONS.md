# Phase 3 — deviations, recoveries and disclosures

Everything in this file concerns the execution of the frozen Phase 3 campaign. **No deviation here changed the
preregistration, Evarb-0.2, the sealed eval3 data, any model or decoding setting, any original run manifest or any
raw output.** The campaign ran to completion: 18 cells × 3216 rows = 57,888 rows, 0 duplicates, 0 unparsable lines,
0 harness errors, all checksums verified.

Companion documents: `PHASE3_G4_FORENSIC_REPORT.md` (the investigation), `PHASE3_PLATFORM_CONTINUITY.md` (the
generated G5 report), `platform_evidence.json` (the raw evidence with epistemic status), `LIMITATIONS.md`.

---

## D1 — Unplanned node reboot mid-campaign, with a host-platform transition

**What happened.** The compute node `<compute-node>` rebooted at `2026-11-20T10:11:58` (verified: `scontrol show node
<compute-node>`, `BootTime`). The node had been up since `2026-10-03T06:51:20` (verified: `journalctl --list-boots`).
Across that reboot:

| | Before | After | Status |
|---|---|---|---|
| Linux kernel | `6.8.0-139-generic` | `6.8.0-149-generic` | after: **verified**; before: **inferred** |
| NVIDIA kernel module | `580.173.02` | `580.178.04` | after: **verified**; before: **inferred** |
| `torch` / `transformers` / CUDA runtime | `2.15.0+cu132` / `5.22.2` / `13.2` | unchanged | **verified** |
| Frozen code (14 files) | identical | identical | **verified** |

The "before" values are inferred, not read: the previous boot began before the NVIDIA packages were upgraded on
`2026-10-11 06:53:41` (`/var/log/dpkg.log`: `nvidia-dkms-580-server 580.173.02 → 580.178.04`), so the node continued
running the already-loaded `580.173.02` module against `580.178.04` userspace. That is independently corroborated by
the recorded failure of `nvidia-smi` on this node on 2026-11-11 with a driver/library version mismatch, and by
`nvidia-smi` working again after the reboot. The previous boot's kernel log is not readable from the `<user>`
account, so the pre-reboot module version cannot be read directly. One privileged command would settle it:
`journalctl -b -1 -k | grep NVRM` on `<compute-node>`.

**How it surfaced.** As a 0.2 GiB change in read-only telemetry. `client.gpu_mem_gib` —
`round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1)`, `hf_client.py:58` — moved from `44.6` to
`44.4`. This is the only `client` subfield that differs anywhere in the campaign.

**Scope.** Two of eighteen cells have rows on both platforms; the other sixteen finished before the reboot (latest
`2026-11-19T06:20:17Z`).

| | `qwen3_8b_T07_s3` | `llama32_3b_greedy` | Campaign |
|---|---|---|---|
| Rows before the reboot | 2345 (72.9%) | 3107 (96.6%) | 56,908 (98.3%) |
| Rows after the reboot | **871 (27.1%)** | **109 (3.4%)** | **980 (1.69%)** |
| Whole tasks on the new platform | 72 | 9 | — |
| Tasks split across platforms | 1 (`eval3-0202`, 5 old / 7 new) | 1 (`eval3-0267`, 11 old / 1 new) | 2 of 268 |
| Post-reboot rows per configuration | 72–73 | 9–10 | — |

**Why the contrasts are not confounded by it.** `run_p2.py` iterates tasks in sorted `task_id` order (outer) and the
12 frozen configurations (inner), skipping completed `(task_id, config)` pairs. A resumed segment is therefore a
contiguous suffix in task order that carries all 12 configurations for every whole task it contains, so the platform
transition is balanced across `B, G, R, T, RT, EB, EBG, LA, LG, EBG-all, EBG-unsafe, EBG-noR3` to within one row per
configuration. A platform-induced shift would move all 12 arms of a task together, which the paired, family-clustered
design differences out. **The residual within-task confound is exactly two tasks**, named above.

**What cannot be established.** Whether `580.173.02` and `580.178.04` produce different generations for these models
is **unknown** and cannot be made known from this campaign: the two quarantined fragments contain zero complete rows,
so no `(task, config)` pair exists on both platforms to compare. Establishing it would require re-running completed
cells, which §10 of the preregistration does not permit and which would be a post-hoc choice taken with knowledge of
which cells were affected.

**Decision.** Both cells are retained. §3 of the preregistration pins the mechanism, harness, runner, analysis and
data — all hash-verified identical across both starts — and §4 pins the hardware only as "bf16, one L40", which held.
The GPU driver and host kernel are not pinned. §7 explicitly provides for resume. §10 restricts a restart to a freeze
mismatch, a seal mismatch or a runner defect, none of which occurred.

---

## D2 — Slurm requeue, truncated write and quarantine recovery

**What happened.** Jobs 4315 (`qwen3_8b_T07_s3`) and 4324 (`llama32_3b_greedy`) were in flight when the node went
down. Slurm requeued both at `2026-11-20T10:12:26`; both exited 1 immediately in the resume path
(`run_p2.py:89`, `json.loads` → `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`), because the node had
died mid-write leaving a truncated final line in each `runs.jsonl`. The controller quarantined the damaged tail and
resubmitted:

| Quarantine file (retained in place) | Bytes | Complete rows | Truncated fragments | sha256 |
|---|---|---|---|---|
| `eval3_qwen3_8b_T07_s3/runs.jsonl.partial_20261120T101726Z` | 1153 | **0** | 1 | `8562263d10d49c219c9175a14dcc94a47e98b3d3a65f4d62426f48ca8cf14f5a` |
| `eval3_llama32_3b_greedy/runs.jsonl.partial_20261120T101727Z` | 3617 | **0** | 1 | `e05fd635ac8500b3af10a86d9327bb0b911a9ae2d17aa733dd54276ee9a59290` |

No completed run was discarded. The single interrupted `(task, config)` pair in each cell was re-executed after the
resume. Jobs 4326 and 4327 completed both cells to the full 3216 rows with 0 duplicates.

**Collateral loss.** Slurm's requeue **overwrote** the console logs of the first starts, `phase3_4315_15.out` and
`phase3_4324_17.out` (mtime `2026-11-20 10:12:26`). Those two logs no longer exist. The corresponding manifest lines
survive intact and carry the code hashes, freeze state and start timestamps, so the evidential chain is unbroken, but
the per-start console output of those two starts cannot be reproduced.

---

## D3 — A resumed sampled cell re-seeds instead of continuing its random stream

`HFClient.__init__` calls `torch.manual_seed(seed)` once per process (`hf_client.py:54`). A resume is a fresh
process, so the post-resume segment restarts the sampling stream from the base seed rather than continuing the stream
an uninterrupted run would have had.

- **Affected:** `qwen3_8b_T07_s3` only — the one sampled cell that was resumed.
- **Not affected:** `llama32_3b_greedy` is greedy (`do_sample=False`), so it has no sampling stream; no other cell
  was resumed.
- **Effect on validity:** none. The preregistration fixes T = 0.7 with seeds 1, 2, 3 (§4) and makes no claim about
  stream continuity; re-seeding does not bias the sampling distribution.
- **Effect on reproducibility:** exact byte-reproduction of this one cell now requires reproducing the interruption at
  the same row. This is disclosed in the reproducibility package.

---

## D4 — G4 validator correction (`g4-v1` → `g4-v2`)

**Defect.** `g4-v1` compared the manifest `client` object as one opaque JSON blob, which made read-only host
telemetry indistinguishable from a change of client implementation and produced a message that named neither the
subfield nor the values. Finalization job 4270 therefore stopped at `STATE: FAILED (gates)` on 2026-11-20 with two
uninformative `manifest field client differs between starts` failures.

**Correction (`g4-v2`, 2026-11-21).** `client` is split into two explicitly declared sets, closed by default:

- `CLIENT_IDENTITY` — 18 fields (`backend`, `family`, `family_adapter`, `model`, `model_path`, `adapter`,
  `adapter_sha256`, `temperature`, `seed`, `decoding`, `max_new_tokens`, `dtype`, `thinking`, `parser_version`,
  `torch`, `transformers`, `cuda`, `gpu`). Each must be **present in every start** and **equal across starts**. A
  difference or an absence is a hard failure that prints the exact field path and the differing values.
- `CLIENT_OBSERVATIONAL` — exactly one field, `gpu_mem_gib`. Excluded from the identity comparison **only**. Every
  start's original value is retained and reported in `gates.json` (`client_observational_diffs`) and on stdout.
- **Anything else** — a `client` key in neither set is a hard failure until it is explicitly classified, whether or
  not it differs between starts.

The top-level strict checks (`temperature`, `seed`, `split_sha256`, `code_sha256`, `configs`) are unchanged, as are
G1, G2 and G3.

**Justification for the one waived field.** `gpu_mem_gib` is stored in `HFClient._versions` and consumed only by
`HFClient.describe()` to build the manifest. The model is loaded with `device_map={"": 0}` and no `max_memory`
(`hf_client.py:45`), so the reported device total has no path to placement, offloading, batching or generation.

**Preservation.** The original validator is kept verbatim as `scripts/finalize_gates_v1_frozen.py`, sha256
`8c1870f0725131c12ee4a4b3b67687426c3490b9d6967643b41f1364dc9e704d`, and a test asserts it is unmodified. No original
manifest was edited, replaced or rewritten.

**Tests.** `tests/test_finalize_gates_v2.py` proves: a `gpu_mem_gib`-only change passes and is reported; a changed
client adapter, parser version or framework version fails; an unknown field fails until classified (including when
identical across starts); missing client metadata fails; every one of the 18 identity fields is individually
enforced; and, against the real campaign manifests, all 18 cells pass while exactly the two known cells report
telemetry and the 16 single-start cells are untouched.

---

## D5 — Reporting-only platform-continuity check (G5)

`scripts/platform_continuity.py` (`g5-v1`) derives per-cell start structure from the frozen manifests, joins it with
`platform_evidence.json`, and writes `PHASE3_PLATFORM_CONTINUITY.md` and `ANALYSIS/PLATFORM_CONTINUITY.json`. It
separates **verified**, **inferred** and **unknown** facts, always exits 0, and is read by no statistical
computation. It exists so that a platform transition cannot again surface only as a telemetry rounding difference.

---

## D6 — Environment change made after the campaign, for testing only

`pytest` was installed into the campaign venv (`~/AGENTRUN_HPC/20261111/environment/venv`) on 2026-11-21, because the
test suite could not otherwise be run on the cluster. This happened **after** all 18 cells were complete and sealed,
and no GPU run was executed afterwards. `torch`, `transformers` and every other package the campaign depended on are
unchanged, and the 14 frozen code hashes still verify. Disclosed here because it is a change to the recorded
execution environment, however inert.

---

## D7 — Analysis additions, all labelled exploratory

The preregistered confirmatory analysis is unchanged: same hypotheses, same item set, same unit, same sign-flip
permutation test with 100,000 permutations, same Holm family, same α. Two **post-hoc, exploratory** analyses were
added after the platform transition came to light, and are reported separately from the confirmatory result:

1. `EXPLORATORY_no_straddling_cell` — the primary pooled contrasts recomputed with `qwen3_8b_T07_s3` excluded, so
   Qwen3-8B contributes its three fully pre-reboot decodings. It tests whether the preregistered verdict depends on
   the one cell that straddles the reboot.
2. `EXPLORATORY_qwen3_pre_reboot_only` — the same contrasts on Qwen3-8B's three pre-reboot decodings alone.

**What they can establish:** whether the headline conclusions are sensitive to including the straddling cell.
**What they cannot establish:** whether the driver transition changed generation behaviour. Agreement between the
confirmatory and exploratory results is consistent with the transition being inert, but it is equally consistent with
a real effect too small to move a family-clustered permutation test at this sample size, and it says nothing about
the two tasks whose rows are split within themselves. Neither analysis may be read as a confirmatory test, and
neither changes the preregistered verdict.

---

## Deviation ledger

| ID | Deviation | Changes the preregistered analysis? | Disclosed in |
|---|---|---|---|
| D1 | Host-platform transition mid-campaign (kernel + NVIDIA driver) | No | results, limitations, G5 report |
| D2 | Slurm requeue, truncated write, quarantine recovery; two console logs lost | No | execution log, failure analysis |
| D3 | Re-seed on resume in `qwen3_8b_T07_s3` | No | limitations, reproducibility package |
| D4 | G4 validator `v1` → `v2` | No (integrity gate, not analysis) | this file, forensic report |
| D5 | New reporting-only G5 check | No | this file |
| D6 | `pytest` installed post-campaign | No | this file, reproducibility package |
| D7 | Two exploratory sensitivity analyses added | No — reported separately | results, discussion |
