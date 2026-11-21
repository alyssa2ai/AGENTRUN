# Phase 3 — forensic report on the two G4 gate failures

**Investigator:** Claude Code session, 2026-11-21
**Status of the campaign at the time of writing:** 18/18 cells DONE, Slurm queue empty, finalization job 4270 stopped at stage `gates` with `STATE: FAILED (gates)`.
**Nothing was rerun, edited, deleted or regenerated during this investigation.** All reads were read-only; no eval3 task text, gold label, score or per-task outcome was read or recorded. (Two incidental per-run outcome lines appeared in a `head` of a Slurm log before the filter was tightened; they were not read for content, not recorded, and no aggregate was computed from them.)

---

## 0. Verdict in one paragraph

Both failures have the same single cause. The only `client` subfield that differs between the two starts of the two affected cells is `gpu_mem_gib`, which changed from `44.6` to `44.4`. That field is read-only telemetry — `round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1)` — and is never used to configure the model, the loader, the decoding or anything else. Every identity-bearing field is byte-identical across the two starts: model, snapshot path, adapter, dtype, temperature, seed, `max_new_tokens`, decoding, parser version, family adapter, torch, transformers, CUDA runtime, all 14 frozen code hashes, the split hash and the 12 configuration names. **The flagged field is therefore metadata-only (category A at the level of the field).** However, the *reason* the telemetry changed is a real one: the compute node `sit-gpu` rebooted at `2026-11-20T10:11:58` into a newer Linux kernel and a newer NVIDIA kernel driver, and the two affected cells are the only two whose rows straddle that reboot. **So this is not a cosmetic event, and I am not classifying it as plain A.** The honest classification is given in §3: metadata-only for the flagged field, genuine host-platform change underneath it, affecting 980 of 57,888 rows (1.69%), balanced across the 12 configurations except for exactly two boundary tasks.

My recommendation is to keep both cells, disclose the deviation, narrow the G4 check so it names the field it is comparing instead of comparing the whole `client` blob, and rerun only the finalization pipeline. Justification in §5.

---

## 1. The two failures

### 1.1 What the gate said

`/home/gpuuser12/AGENTRUN_HPC/finalize/finalize_4270.out`:

```
gates: FAIL; cells DONE 18/18
  G4 qwen3_8b_T07_s3: manifest field client differs between starts
  G4 llama32_3b_greedy: manifest field client differs between starts
```

G4 is implemented in `research/AGENTRUN_PUBLICATION_2026/PHASE3/scripts/finalize_gates.py` (sha256 `8c1870f0725131c12ee4a4b3b67687426c3490b9d6967643b41f1364dc9e704d`, committed in `b7c8b7a`), lines 66–68:

```python
for k in ("client", "temperature", "seed", "split_sha256", "code_sha256", "configs"):
    if len({json.dumps(m.get(k), sort_keys=True) for m in man}) > 1:
        fails.append(f"G4 {c}: manifest field {k} differs between starts")
```

`client` is compared as one opaque JSON blob, so any subfield difference — including pure telemetry — fails the gate, and the message does not say which subfield or what the values were.

### 1.2 Number of starts and which manifest belongs to each

Both cells have exactly two manifest lines; all 16 other cells have one. `manifest.jsonl` is append-only (`run_p2.py`, `open(out / "manifest.jsonl", "a")`), so line *n* is start *n*.

| Cell | Start | Slurm job | `started_utc` | `resumed_with_done` | Slurm log |
|---|---|---|---|---|---|
| `qwen3_8b_T07_s3` | 0 | 4315 | 2026-11-19T05:48:56Z | 0 | `phase3_4315_15.out` (overwritten on requeue, see §1.6) |
| `qwen3_8b_T07_s3` | 1 | 4326 | 2026-11-20T10:17:51Z | 2345 | `phase3_4326_15.out` |
| `llama32_3b_greedy` | 0 | 4324 | 2026-11-19T06:24:05Z | 0 | `phase3_4324_17.out` (overwritten on requeue) |
| `llama32_3b_greedy` | 1 | 4327 | 2026-11-20T10:18:08Z | 3107 | `phase3_4327_17.out` |

Paths:
`/home/gpuuser12/AGENTRUN_HPC/phase3_raw/eval3_qwen3_8b_T07_s3/manifest.jsonl` — sha256 `1f35ea2d34f86d0909816feed2e84d84a2e5211ccd7a3e0584ac0a4fdbf49d27`
`/home/gpuuser12/AGENTRUN_HPC/phase3_raw/eval3_llama32_3b_greedy/manifest.jsonl` — sha256 `e3a348e53e7a88d4044909b581221b12a1c7a7f96cbc68869f36cb1fc49b58eb`

### 1.3 The exact differing values

Full field-level diff of the two manifest lines of each cell:

| Cell | Differing key | Start 0 | Start 1 |
|---|---|---|---|
| `qwen3_8b_T07_s3` | `client.gpu_mem_gib` | `44.6` | `44.4` |
| | `resumed_with_done` | `0` | `2345` |
| | `slurm_job_id` | `"4315"` | `"4326"` |
| | `started_utc` | `2026-11-19T05:48:56Z` | `2026-11-20T10:17:51Z` |
| `llama32_3b_greedy` | `client.gpu_mem_gib` | `44.6` | `44.4` |
| | `resumed_with_done` | `0` | `3107` |
| | `slurm_job_id` | `"4324"` | `"4327"` |
| | `started_utc` | `2026-11-19T06:24:05Z` | `2026-11-20T10:18:08Z` |

`resumed_with_done`, `slurm_job_id` and `started_utc` are expected to differ between starts and are not checked by G4. **`client.gpu_mem_gib` is the only difference inside the `client` object, in both cells.**

Every other `client` subfield is identical across the two starts in both cells:

```
adapter, adapter_sha256, backend, cuda, decoding, dtype, family, family_adapter,
gpu, max_new_tokens, model, model_path, parser_version, seed, temperature,
thinking, torch, transformers
```

In particular: `model_path` points at the same HF snapshot hash in both starts (`…/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`, `…/models--meta-llama--Llama-3.2-3B-Instruct/snapshots/0cb88a4f764b7a12671c53f0838cd831a0843b95`); `torch` = `2.15.0+cu132`, `transformers` = `5.22.2`, `cuda` = `13.2`, `gpu` = `NVIDIA L40`, `family_adapter` = `evarb.clients.FamilyClient/1`, `parser_version` = `two-pass-v2+client-fallback` in all four manifest lines.

### 1.4 What kind of field this is

Not a class name, not a package version, not a configuration value, not an adapter. It is a **hardware observation**, taken once in the client constructor and copied into the manifest for the record:

`research/AGENTRUN_DEEPENING_2026-11-11/scripts/hf_client.py:56-58`

```python
self._versions = {"torch": torch.__version__, "transformers": transformers.__version__,
                  "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
                  "gpu_mem_gib": round(torch.cuda.get_device_properties(0).total_memory / 2 ** 30, 1)}
```

`_versions` is consumed only by `HFClient.describe()` (`hf_client.py:60-65`), which is only used to build the manifest. The model is loaded with `device_map={"": 0}` and no `max_memory` argument (`hf_client.py:45`), so the reported total has no path by which it could influence placement, offloading, batch sizing, quantisation or generation. **The field is causally inert with respect to execution.**

### 1.5 Did the client implementation change? No.

- `code_sha256` — 14 files (`evarb/*.py`, `rcs.py`, `tea.py`, `memlab.py`, `hf_client.py`, `run_p2.py`) — is **identical in all 20 manifest lines of the campaign** (one distinct hash map across all 20).
- The 14 files on the cluster today still hash to exactly those values (`run_p2.code_hashes()` recomputed live: 14/14 match, 0 mismatches).
- Every one of the 20 job starts printed `freeze evarb-0.2 mismatches []` and `prereg 221013b3cee87c00 frozen 221013b3cee87c00 status SEALED` as its first two log lines, including both starts of both affected cells.
- `split_sha256` = `602eb748850847462ebeb0dea0cd7b030cd4d00c209c9411b5fa5e1b9b534410` and the 12-element `configs` list are identical in all 20 lines.

### 1.6 Why there were two starts: an unplanned node reboot, not a controller transition

The controller did not decide to restart these cells. Sequence, from `scontrol`, the journal, the controller log and the job logs:

```
2026-11-19T05:48:48Z  controller submits cell 15 (qwen3_8b_T07_s3)   -> job 4315
2026-11-19T06:23:50Z  controller submits cell 17 (llama32_3b_greedy) -> job 4324
2026-11-19T07:29:06Z  last readable journal entry of boot -1 (node going down)
2026-11-20T10:11:58   sit-gpu BootTime  (scontrol show node sit-gpu)
2026-11-20T10:12:11   SlurmdStartTime
2026-11-20T10:12:26Z  Slurm requeues 4315 and 4324; both restart and exit=1 within the same second
2026-11-20T10:12:26Z  controller v2 (job 4257) restarts
2026-11-20T10:17:26Z  controller quarantines 1153 bytes of eval3_qwen3_8b_T07_s3/runs.jsonl
2026-11-20T10:17:27Z  controller resubmits cell 15                   -> job 4326
2026-11-20T10:17:27Z  controller quarantines 3617 bytes of eval3_llama32_3b_greedy/runs.jsonl
2026-11-20T10:17:27Z  controller resubmits cell 17                   -> job 4327
2026-11-20T10:22:38Z  cell 17 DONE (3216 runs)
2026-11-20T11:18:26Z  cell 15 DONE (3216 runs)
2026-11-20T11:22:30Z  all 18 DONE, SHA256SUMS written, controller exits
```

The `exit=1` of the requeued 4315/4324 is fully explained by their stderr: both crashed in the resume path at `run_p2.py:89`, `r = json.loads(line)` → `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`. The node went down mid-write, leaving a truncated final line in each `runs.jsonl`. The controller's quarantine handled exactly that:

| Quarantine file | Bytes | Complete rows | Truncated fragments | Ends with newline | sha256 |
|---|---|---|---|---|---|
| `eval3_qwen3_8b_T07_s3/runs.jsonl.partial_20261120T101726Z` | 1153 | **0** | 1 | no | `8562263d10d49c219c9175a14dcc94a47e98b3d3a65f4d62426f48ca8cf14f5a` |
| `eval3_llama32_3b_greedy/runs.jsonl.partial_20261120T101727Z` | 3617 | **0** | 1 | no | `e05fd635ac8500b3af10a86d9327bb0b911a9ae2d17aa733dd54276ee9a59290` |

Each quarantine contains **zero complete rows** — only the single partial row that was being written when the node died. No completed run was discarded, and the interrupted `(task, config)` pair was simply re-executed after the resume. This is the behaviour `PREREGISTRATION.md` §7 anticipates ("a cell … is re-submitted once (the runner resumes)").

One consequence worth recording: Slurm's requeue **overwrote** `phase3_4315_15.out` and `phase3_4324_17.out` (mtime `2026-11-20 10:12:26`), so the original 2026-11-19 Slurm logs of those two first starts no longer exist. Their manifest lines survive intact and carry the code hashes and freeze state, so nothing evidentially essential was lost, but the per-start console logs of starts 0 are gone.

### 1.7 Why the telemetry changed: kernel and NVIDIA driver moved at that reboot

The 0.2 GiB difference is not noise and not a different GPU board. Evidence:

- **Not GPU identity.** Cell 15 ran on `CUDA_VISIBLE_DEVICES=0` in *both* starts; cell 17 ran on `CUDA_VISIBLE_DEVICES=1` in *both* starts. Both devices moved 44.6 → 44.4 across the reboot, so the device the job landed on cannot explain it. `nvidia-smi` today reports both L40s identically: `46068 MiB`, ECC `Enabled`.
- **The node had been up since before a driver upgrade.** `journalctl --list-boots`: boot `-1` ran `2026-10-03T06:51:20` → `2026-11-19T07:29:06`; boot `0` starts `2026-11-20T10:12:26`.
- **The NVIDIA driver was upgraded while the node stayed up.** `/var/log/dpkg.log`: `2026-10-11 06:53:41 upgrade nvidia-dkms-580-server 580.173.02-0ubuntu0.24.04.1 → 580.178.04-0ubuntu0.24.04.1` (the previous upgrade, to `580.173.02`, was `2026-07-24`). A node booted on 2026-10-03 was therefore still running the `580.173.02` kernel module while userspace had moved to `580.178.04` — which is exactly the `nvidia-smi` "driver/library mismatch" recorded on this node on 2026-11-11.
- **The reboot resolved the mismatch.** `/proc/driver/nvidia/version` now reports `580.178.04`; `modinfo nvidia` → `version: 580.178.04`, `/lib/modules/6.8.0-149-generic/updates/dkms/nvidia.ko.zst` built `2026-11-13 06:14:15`; `/sys/module/nvidia` created `2026-11-20 10:12:02`. `nvidia-smi` now works, where it failed before.
- **The host kernel also changed.** Boot `-1` ran `6.8.0-139-generic` (installed 2026-09-05); boot `0` runs `6.8.0-149-generic` (installed 2026-11-13, not booted until the reboot).

A driver revision changing its reserved carve-out by ~215 MiB is ordinary and fully accounts for 44.6 → 44.4.

**Residual uncertainty (stated, not papered over):** the kernel-log banner of boot `-1` is not readable from the `gpuuser12` account (not in `adm`/`systemd-journal`), so the pre-reboot *loaded* module version is inferred from boot time versus package dates plus the documented mismatch symptom, rather than read directly. An admin can confirm it in one command; see §6.

---

## 2. Comparison against the other 16 cells

| Check across all 20 manifest lines (18 cells) | Result |
|---|---|
| Distinct `code_sha256` maps | **1** |
| Distinct `split_sha256` | **1** (`602eb748…`) |
| Distinct `configs` lists | **1** (12 configs) |
| Distinct `evarb_version` / `p2_loop_version` / `n_tasks` / `python` | **1** each (`evarb-0.2`, `evarb-loop-0.2`, `268`, `3.12.3`) |
| Distinct `client.gpu` / `parser_version` / `family_adapter` / `(torch, transformers, cuda)` | **1** each |
| Distinct `client` objects **excluding** `gpu_mem_gib` | **18** — exactly one per cell, as designed |
| `client.gpu_mem_gib` distribution | `44.6` ×18, `44.4` ×2 |
| Cells with `starts > 1` | **2** — `qwen3_8b_T07_s3`, `llama32_3b_greedy` |
| `rows` / `duplicates` / `unparsable` / `harness_errors` per cell | `3216` / `0` / `0` / `0` for all 18 |
| `sha256sum -c SHA256SUMS` over `phase3_raw` | **54/54 OK**, 0 failures |
| Freeze + preregistration line in every job log | 20/20 `mismatches []`, `221013b3cee87c00`, `SEALED` |

The two `44.4` values are the two second starts. **The discrepancy is isolated to the two cells that straddled the reboot, and it is systematic within them** (both moved by the same amount, in the same direction, at the same moment). It is not a controller change, not a code change, and not an environment drift during normal operation.

Every one of the other 16 cells finished **before** the reboot (latest: `qwen3_8b_T07_s2`, `2026-11-19T06:20:17Z`; reboot `2026-11-20T10:11:58`). Those 16 cells are therefore wholly on the old platform.

**Git / frozen-code provenance.** The frozen mechanism sits under commit `48d6e44` ("Phase 2 complete — p2val2 agent-level validation, eval3 sealed, preregistration frozen"); the finalization and gate code under `b7c8b7a`. The HPC clone `~/AGENTRUN_HPC/finalize/AGENTRUN` is on `research/memory-ablation-2026-11` at `b7c8b7a` with a clean working tree. No code was touched during the campaign.

---

## 3. Scientific impact and classification

### 3.1 Classification

Against the four categories given:

- **The flagged field itself: category A.** `client.gpu_mem_gib` is read-only telemetry with no path to execution (§1.4), and every execution-determining field is identical (§1.3, §1.5).
- **The underlying cause: a genuine host-platform change, i.e. category C restricted to the platform layer.** The host kernel went `6.8.0-139` → `6.8.0-149` and the NVIDIA kernel driver `580.173.02` → `580.178.04` at `2026-11-20T10:11:58`. The *client implementation* did not change and no preregistered parameter changed, so this is not C in the "client changed" sense and it is not B (the two starts are not two representations of equivalent implementations — they are the same implementation). It is a fourth thing: **identical, hash-verified client and configuration, executed on a changed host platform, with the flagged metadata field being a read-only observation of that platform.**

I am explicitly **not** reporting this as plain category A, because doing so would describe a real platform transition as cosmetic.

### 3.2 Exact scope of the affected rows

`run_p2.py` iterates tasks sorted by `task_id` (outer) and the 12 configurations in frozen order (inner), skipping `(task_id, config)` pairs already present. The post-reboot segment is therefore a **contiguous suffix in task order**, covering all 12 configurations for each whole task it contains.

| | `qwen3_8b_T07_s3` | `llama32_3b_greedy` |
|---|---|---|
| Rows total | 3216 | 3216 |
| Rows before the reboot (old platform) | 2345 (72.9%) | 3107 (96.6%) |
| Rows after the reboot (new platform) | **871 (27.1%)** | **109 (3.4%)** |
| Tasks wholly on the new platform | 72 | 9 |
| Tasks split across platforms | **1** (`eval3-0202`: 5 old / 7 new) | **1** (`eval3-0267`: 11 old / 1 new) |
| Post-reboot rows per configuration | 72 or 73 (max spread 1) | 9 or 10 (max spread 1) |
| Duplicate `(task_id, config)` pairs | 0 | 0 |

Campaign-wide: **980 of 57,888 rows (1.69%)** were produced on the new platform; 2 of 18 cells, 2 of 268 tasks internally split.

### 3.3 What this does and does not threaten

- **The within-cell paired contrasts are not confounded.** Because the split is by task and every whole task carries all 12 configurations, the platform change is balanced across `B, G, R, T, RT, EB, EBG, LA, LG, EBG-all, EBG-unsafe, EBG-noR3` to within one row per configuration. A platform-induced shift would move all 12 arms of a task together, which is exactly what the paired, family-clustered design differences out.
- **The precise residual confound is two tasks.** `eval3-0202` (in `qwen3_8b_T07_s3`) and `eval3-0267` (in `llama32_3b_greedy`) each have some configurations executed on the old platform and the rest on the new one, so for those two tasks alone the within-task pairing mixes platforms. 2 of 268 tasks, in 1 of 4 Qwen3-8B decodings and in the never-pooled format-limited cell respectively.
- **Analysis-level dilution.** Per `PREREGISTRATION.md` §8, success per task is the mean over a model's decodings. For Qwen3-8B that is 4 decodings × 3216 = 12,864 rows, of which 871 (6.8%) are post-reboot. `llama32_3b_greedy` is the format-limited secondary cell, "reported separately, never pooled" (§4), so its 109 rows touch nothing in the primary test.
- **A second, independent deviation found while investigating (not what G4 flagged).** `hf_client.py:54` calls `torch.manual_seed(seed)` once in the client constructor; the sampling stream then runs forward through the cell. A resume starts a **fresh process and reseeds**, so for `qwen3_8b_T07_s3` (T=0.7, seed 3) the post-reboot segment does not continue the RNG stream an uninterrupted run would have had. This does not bias anything — the seed is a reproducibility device, and the preregistration fixes "T=0.7 seeds 1, 2, 3", which held — but exact byte-reproduction of that one cell now requires reproducing the interruption. It is the only sampled cell that was resumed; `llama32_3b_greedy` is greedy, so it is unaffected. This should be disclosed alongside the platform note.
- **What cannot be measured.** No direct determinism probe is available: the quarantined fragments contain zero complete rows (§1.6), so there is no `(task, config)` pair that was executed on both platforms and could be compared. Whether `580.173.02` and `580.178.04` select different kernels for these models cannot be tested without re-running, which is excluded by §4 below.

---

## 4. Preservation statement

Confirmed untouched, and verified after the investigation:

- All 18 `runs.jsonl`, `manifest.jsonl` and `DONE` files: `sha256sum -c SHA256SUMS` in `/home/gpuuser12/AGENTRUN_HPC/phase3_raw` → **54/54 OK**.
- Both quarantined fragments retained in place with the hashes in §1.6.
- Affected-cell hashes for the record:

```
1f35ea2d34f86d0909816feed2e84d84a2e5211ccd7a3e0584ac0a4fdbf49d27  eval3_qwen3_8b_T07_s3/manifest.jsonl
8f977bb2bb72f316d8f53ae41e9ca0b1d6ae9ec51b7a587fb2fb66c09a15821a  eval3_qwen3_8b_T07_s3/runs.jsonl
6fb64c3444cd12b540562a12c694c21cb7090644d7cb219280ee05425b808a9e  eval3_qwen3_8b_T07_s3/DONE
e3a348e53e7a88d4044909b581221b12a1c7a7f96cbc68869f36cb1fc49b58eb  eval3_llama32_3b_greedy/manifest.jsonl
6426d3e3a70a43844fb30470792a0686b67a551b80a808475801b04e408d3244  eval3_llama32_3b_greedy/runs.jsonl
aaffc18bcd0dfe6c35379a9a7f802799b392aa28984c806878ebf01427e1e3f5  eval3_llama32_3b_greedy/DONE
```

- No cell rerun, no job submitted, no `evarb-0.2` file touched, no preregistration change, no model or decoding setting touched, no manifest edited or replaced, no gate removed or weakened, no eval3 outcome inspected. `finalize_gates.py` is **unmodified**; job 4270 has **not** been resubmitted.

---

## 5. Recommended resolution

### 5.1 Keep both cells. Do not rerun them.

Grounds, all preregistered in advance:

- `PREREGISTRATION.md` §3 pins the mechanism, harness, runner, analysis, evaluation data and this document. All of those are hash-verified identical across both starts of both cells (§1.5, §2). The GPU driver and host kernel are not pinned; §4 pins the hardware only as "bf16, one L40", which held throughout.
- §7 explicitly provides for resume: "A cell … with > 5% missing pairs is re-submitted once (the runner resumes)". That is precisely what the controller did, and both cells reached the full 3216 rows with 0 duplicates and 0 harness errors.
- §10 permits restarting a cell only for "an integrity failure: freeze mismatch, seal mismatch, or a runner defect". None occurred: freeze clean in all 20 starts, seal clean, and the resume crash was a correctly-handled truncated write caused by the node going down, not a defect in the runner.
- Rerunning now would be a post-hoc choice made with knowledge of *which* cells were affected, taken after the campaign closed — which is a worse position than disclosing a 1.69% platform split, and is the one route by which outcome knowledge could later be argued to have leaked in.

The cells are not "incompatible runs" being silently pooled: they are the same frozen client and configuration, with a documented platform transition inside two of them, disclosed in the results and the limitations.

### 5.2 Narrow validator correction to G4 (proposed, not applied)

The defect in the gate is that it compares `client` as one opaque blob, so inert telemetry is treated as an identity violation and the failure message names neither the subfield nor the values. The correction keeps every execution-identity check and *strengthens* reporting:

```python
# Fields that determine what was executed: any difference between starts is a hard failure.
CLIENT_IDENTITY = ("backend", "model", "model_path", "adapter", "adapter_sha256",
                   "temperature", "seed", "max_new_tokens", "dtype", "decoding",
                   "thinking", "parser_version", "family", "family_adapter",
                   "gpu", "torch", "transformers", "cuda")
# Read-only observations of the host. Recorded and reported, never silently ignored.
CLIENT_OBSERVED = ("gpu_mem_gib",)

if man:
    for k in ("temperature", "seed", "split_sha256", "code_sha256", "configs"):
        if len({json.dumps(m.get(k), sort_keys=True) for m in man}) > 1:
            fails.append(f"G4 {c}: manifest field {k} differs between starts")
    for k in CLIENT_IDENTITY:
        vals = {json.dumps(m["client"].get(k), sort_keys=True) for m in man}
        if len(vals) > 1:
            fails.append(f"G4 {c}: client.{k} differs between starts: {sorted(vals)}")
    unknown = sorted(set().union(*[set(m["client"]) for m in man])
                     - set(CLIENT_IDENTITY) - set(CLIENT_OBSERVED))
    if unknown:  # a new client field must be classified before it can be waived
        fails.append(f"G4 {c}: unclassified client fields {unknown}")
    obs = {k: [m["client"].get(k) for m in man] for k in CLIENT_OBSERVED
           if len({json.dumps(m["client"].get(k), sort_keys=True) for m in man}) > 1}
    if obs:
        r["client_observational_diffs"] = obs          # recorded in gates.json
        print(f"  NOTE {c}: observational client fields differ between starts: {obs}")
```

Properties of this correction:

1. It does **not** remove the G4 check. Every field that could change what was executed still fails the gate on any difference, and the failure message now names the field and prints the values.
2. It is **closed by default**: a `client` key that is neither classified as identity nor explicitly declared observational **fails** the gate. A future field cannot slip through by being unanticipated.
3. The single waived field is `gpu_mem_gib`, justified by `hf_client.py:45,56-58` — read-only, never used to configure anything.
4. The deviation is **recorded, not hidden**: it lands in `gates.json` as `client_observational_diffs` and in the job's stdout as a NOTE.

### 5.3 Add a platform-continuity gate (G5), reporting-only

G4's blind spot is that it would have passed silently had the driver carve-out happened to be unchanged. Add an explicit check that reports, per cell, whether its starts straddle a node boot — derived from `started_utc` versus the node `BootTime` — and writes the result into `gates.json`. It should **report**, not fail, since §7 permits resume; a non-empty result obliges an entry in the deviation log.

### 5.4 Record the deviation

Create `PHASE3_DEVIATIONS.md` carrying §1.6, §1.7 and §3.2 of this report verbatim (reboot timestamp, driver and kernel versions with their evidence, the 980/57,888 row split, the two boundary tasks, and the RNG-reseed note from §3.3), and reference it from `PHASE3_STATUS.md`, `LIMITATIONS.md`, the results section and the manuscript's limitations. The claim to make in the paper is the narrow one: *two of eighteen cells contain rows produced after an unplanned node reboot that moved the host kernel and NVIDIA driver; the frozen mechanism, model snapshots and decoding parameters were hash-identical before and after; the split is balanced across configurations except for two tasks.*

### 5.5 Manifest gap to close for future phases only

`manifest.jsonl` records torch, transformers and the CUDA **runtime**, but not the NVIDIA **driver** version, the kernel release or the boot id — which is why a 0.2 GiB telemetry drift was the only visible trace of a platform change. Add those three to `HFClient.describe()` for Phase 4 and later. **Not retroactively**: the Phase 3 manifests are frozen artefacts and must not be rewritten.

### 5.6 Optional, and only if decided now while still blind

If a sensitivity check is wanted, it must be fixed **before** any outcome is seen, and labelled exploratory: repeat the primary contrasts for Qwen3-8B over its three fully-pre-reboot decodings (greedy, s1, s2), excluding the `T07_s3` cell, and report it beside the preregistered primary. Deciding this now, blind, is legitimate; deciding it after seeing the numbers would not be. My recommendation is to take it, precisely because it costs nothing and removes the only argument an examiner could build from §3.2. If you prefer to keep the analysis exactly as preregistered, that is equally defensible — then §5.4's disclosure carries the whole load.

### 5.7 Then, and only then, rerun the finalization

After the gate correction is approved and committed, resubmit `phase3_finalize.sbatch` **without** the `afterany:4257` dependency (the controller has exited and written `ALL_DONE`). That reruns gates → stage → verify → analyze → report → draft → seal. **No experiment cell is rerun.**

---

## 6. What this investigation could not establish

1. **The pre-reboot NVIDIA module version was inferred, not read.** Boot `-1`'s kernel log is not readable from `gpuuser12`. One admin command settles it: `journalctl -b -1 -k | grep NVRM` on `sit-gpu`, which should print the `580.173.02` banner. Until then the chain is boot date (2026-10-03) + package date (2026-10-11) + the documented `nvidia-smi` mismatch — strong, but circumstantial.
2. **No empirical determinism comparison is possible.** No `(task, config)` pair exists on both platforms (quarantines hold zero complete rows), so the claim "the platform change did not alter generations" is an argument from identical inputs and an inert field, not a measurement. It cannot be upgraded without re-running, which §4 excludes.
3. **The original Slurm console logs of starts 0 of both cells are gone**, overwritten by Slurm's requeue at `2026-11-20 10:12:26`. Their manifest lines, with code hashes and freeze state, survive.
4. **Whether anything else changed at the reboot** (BIOS, firmware, ECC state, persistence mode) is not knowable retrospectively from this account; `nvidia-smi` today reports ECC `Enabled` and persistence `Disabled` on both devices, but there is no pre-reboot reading to compare against — `nvidia-smi` was broken on this node before the reboot.

---

## Appendix — commands and paths used

Cluster: `ssh gpuuser12@192.168.192.11` (login `sitgpumaster`), `ssh gpuuser12@192.168.192.9` (compute `sit-gpu`, read-only checks).

| Artefact | Path |
|---|---|
| Finalization status | `~/AGENTRUN_HPC/PHASE3_FINAL_STATUS.md` |
| Gate output | `~/AGENTRUN_HPC/finalize/finalize_4270.out`, `~/AGENTRUN_HPC/finalize/gates.json` |
| Gate source | `~/AGENTRUN_HPC/finalize/AGENTRUN/research/AGENTRUN_PUBLICATION_2026/PHASE3/scripts/finalize_gates.py` |
| Finalization job script | `…/PHASE3/scripts/phase3_finalize.sbatch` |
| Runner | `~/AGENTRUN_HPC/20261111/source/research/AGENTRUN_PUBLICATION_2026/PHASE2/scripts/run_p2.py` |
| Client | `~/AGENTRUN_HPC/20261111/source/research/AGENTRUN_DEEPENING_2026-11-11/scripts/hf_client.py` |
| Raw cells | `~/AGENTRUN_HPC/phase3_raw/eval3_<cell>/{runs.jsonl,manifest.jsonl,DONE}` + `SHA256SUMS` |
| Slurm logs | `~/AGENTRUN_HPC/20261111/source/research/AGENTRUN_PUBLICATION_2026/PHASE2/logs/phase3_*.out|.err` |
| Controller | `~/AGENTRUN_HPC/phase3_controller/{events.log,status.txt,ALL_DONE}` |
| Preregistration | `…/PHASE2/PREREGISTRATION.md` (sealed hash `221013b3cee87c00`) |

Evidence commands: `scontrol show node sit-gpu`; `journalctl --list-boots`; `cat /proc/driver/nvidia/version`; `modinfo nvidia`; `nvidia-smi --query-gpu=index,name,memory.total,ecc.mode.current,driver_version,persistence_mode --format=csv`; `zgrep nvidia-dkms-580-server /var/log/dpkg.log*`; `sha256sum -c SHA256SUMS`; `run_p2.code_hashes()` recomputed against `manifest.jsonl`.
