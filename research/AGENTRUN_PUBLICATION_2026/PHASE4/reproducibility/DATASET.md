# Dataset

## eval3 (confirmatory; restricted)
- 276 skeleton items (23 categories × 12). **268 mechanically valid tasks in 135 families** (family = category × attribute). 8 items were excluded before sealing by `assemble.py` validation; only their ids are recorded.
- The gold label is fixed by the skeleton before any text exists. Texts were written by Qwen2.5-14B-Instruct. Two model annotators (Llama-3.1-8B-Instruct, Qwen2.5-14B-Instruct) labelled the items blind. **There is no human validation.**
- Entities come from name slice [14000:17600] and distractors from [17600:20000], disjoint from every development split (`seal_checks.py`, run inside the sealing job).
- Sealed on 16 Nov 2026 at 10:46 UTC by Slurm job 4200. File hashes are in `configs/FREEZE_eval3.json` (`sealed_files`), and the hash of the sealed directory's `SHA256SUMS` is `sha256sums_file_sha256`. Every Phase 3 job ran `sha256sum -c` on the sealed directory before starting. The runner refuses a task file whose hash differs from the frozen one (`--expect-sha`).
- Item sets (PREREGISTRATION.md §5):
  - **primary**: all 268 valid items;
  - **sensitivity (a)**: both annotators agree with gold at non-low confidence (`eval3_PRIMARY_IDS.json`; 161 items per `FREEZE_eval3.json`), plus its flagged complement (107 items);
  - **sensitivity (b)**: the Qwen2.5-14B annotator agrees with gold (class and value; low confidence allowed). This set is derived with the frozen `benchmark/agreement.py` rule and `PHASE3/scripts/agreed_ids_b.py`. The derivation reproduces the Phase 2 Qwen-agreed id list exactly on p2val2.
- **Access.** eval3 stays on the cluster and in gitignored directories (`PHASE3/SEALED_LOCAL/`, `PHASE3/RAW_RESULTS/eval3_*`). Release is the authors' decision after publication.

## Development splits (shareable)
dev fixtures, p1dev, p1hold, p2dev, p2val and p2val2 (`PHASE2/data/`, `PHASE2/benchmark/`). They are used for mechanism development and pipeline testing only, and never in confirmatory analysis.
