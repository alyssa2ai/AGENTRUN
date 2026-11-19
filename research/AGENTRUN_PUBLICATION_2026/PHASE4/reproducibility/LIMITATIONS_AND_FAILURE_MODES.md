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
- **Reproduction risks:**
  - GPU non-determinism across hardware and library versions;
  - Hugging Face snapshots must match `MODELS.md`;
  - `HF_HUB_OFFLINE=1` requires a pre-populated cache;
  - `nvidia-smi` may be unavailable on some nodes.
