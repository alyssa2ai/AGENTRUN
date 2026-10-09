# Contributing

AGENTRUN is a research repository. Its main obligation is that every reported number stays traceable to committed code and artifacts. Contributions are welcome within the rules below.

## Ground rules

1. **Do not edit historical results.** `results/eval_results_{base,v1,e4,v2}.json` record runs that have already happened. A new run gets a new, clearly labelled file and an entry in `docs/experiment-log.md`. It never overwrites an existing result.
2. **Do not change `eval/tasks.py` or the scoring in `eval/harness.py`** without starting a new, separately named benchmark version. Edits to these files invalidate comparison with every reported condition.
3. **Proposed is not executed.** Experiments such as E5 (random-augmentation control), E7 (multiple seeds) and E8 (fresh held-out benchmark) are listed as future work. Do not describe them as done unless their artifacts are committed.
4. **Never commit credentials.** Use a local `.env` (git-ignored) and the placeholders in `.env.example`. Clear secrets from notebook cells and outputs before committing.
5. **Do not commit model weights, checkpoints or tokenizers.** These are covered by `.gitignore`.

## Checks to run before opening a pull request

```bash
python -m pip install -r requirements-dev.txt
ruff check .
python -m pytest
python results/verify_results.py && git diff --exit-code RESULTS_VERIFIED.md results/results_verified.*
```

CI (`.github/workflows/tests.yml`) runs the same checks. None of them needs a GPU, a network connection, or an API key.

## Releasing

Follow [`docs/release-checklist.md`](docs/release-checklist.md). It also covers publishing a new Zenodo version.
