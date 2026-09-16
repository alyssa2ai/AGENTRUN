# Provenance — Random Seeds & Determinism

**Label: VERIFIED — NOT SET**

No random seeds were set in the training scripts (`colab_train_7b.py`,
`colab_train_7b_v2.py`) or the evaluation scripts (`run_eval_base.py`,
`run_eval_finetuned.py`, `run_eval_v2.py`). This was confirmed by reading each
script; no `torch.manual_seed`, `random.seed`, `numpy.random.seed`, or
`transformers.set_seed` call exists in any of them.

## What this means

| Aspect | Status | Detail |
|---|---|---|
| Training seed | **UNKNOWN** | Model init, dataset shuffling, and weight init used default behavior. |
| Eval seed | **UNKNOWN** | Greedy decoding (`do_sample=False`) is deterministic *given the same model output*, but CUDA ops on GPU are not bit-exact without an explicit seed. |

## Recommendation for future runs

Set and log `torch.manual_seed(seed)` and `random.seed(seed)` before
training/eval. When using 4-bit NF4 quantization on Colab T4, note that CUDA
non-determinism can affect reproducibility even with the same seed.

## Canonical record

See `experiment_provenance.json` → `random_seeds`.