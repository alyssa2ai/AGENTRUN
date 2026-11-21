# Limitations and known failure modes

The full, unsoftened list is in `PHASE3/LIMITATIONS.md` and manuscript §6. The points that matter most for reproduction:

- **Mechanism (frozen, pinned in tests):**
  - long-range negation is not handled;
  - "both figures stand" scored 0/4 on p2val2;
  - "correcting" is not a recognised cue.
- **Historical and as-of questions:** every method scores 0 on them at component level.
- **Data:**
  - synthetic, template-regular items;
  - ISO-only value dates;
  - English only;
  - no human validation;
  - the eval3 writer (Qwen2.5-14B) is also an annotator and an evaluated secondary model.
- **Models:**
  - 3B–14B open-weight models only;
  - Llama-3.1-8B needs a family adapter and is partly format-limited;
  - Llama-3.2-3B failed the readiness criterion and is reported separately.
- **Execution:**
  - Cells 9–17 ran up to two at a time, one per GPU, so wall-time latency (reported, not tested) is not strictly single-occupancy for those cells.
  - The 14B cell had a 36 h wall-time limit instead of 12 h.
  - On 18 Nov, three per-run eval3 outcome labels from cell 8's progress log were displayed to the operator. No task text, gold label or aggregate was seen, and nothing was changed.
  - **Host platform transition (2026-11-20).** The node rebooted mid-campaign; the Linux kernel and the NVIDIA kernel driver changed. 980 of 57,888 rows (1.69%), in `qwen3_8b_T07_s3` and `llama32_3b_greedy`, were produced on the new platform. The frozen code, model snapshots, decoding parameters and framework versions are hash-identical before and after. The split is balanced across the 12 configurations to within one row; two tasks (`eval3-0202`, `eval3-0267`) have their own rows split across platforms. Full account, with the epistemic status of every fact: `PHASE3/PHASE3_DEVIATIONS.md`, `PHASE3/PHASE3_PLATFORM_CONTINUITY.md`, `PHASE3/PHASE3_G4_FORENSIC_REPORT.md`.
  - **Interrupted writes.** The reboot truncated the row being written in each of those two cells. The controller quarantined the damaged tail (1153 and 3617 bytes, each containing zero complete rows) and resubmitted; both cells completed to 3216 rows with no duplicates. The quarantined fragments are retained. Slurm's requeue overwrote the console logs of the two interrupted starts; those are permanently lost, while the manifest lines survive.
  - **Re-seeding on resume.** `qwen3_8b_T07_s3` restarted its sampling stream at row 2345 (see `ENVIRONMENT.md`, Determinism).
- **Reproduction risks:**
  - GPU non-determinism across hardware and library versions;
  - Hugging Face snapshots must match `MODELS.md`;
  - `HF_HUB_OFFLINE=1` requires a pre-populated cache;
  - `nvidia-smi` may be unavailable on some nodes;
  - the two cells listed under Execution cannot be reproduced row for row on a single fixed driver version, because they were not produced on one;
  - whether the two NVIDIA driver versions differ in generation behaviour is **unknown** and cannot be settled from this campaign: no (task, config) pair exists on both platforms.
