# Tests

```bash
cd research/AGENTRUN_PUBLICATION_2026
(cd PHASE2 && python -m pytest tests -q)     # mechanism, arbiter, policy and loop, analysis helpers, known limitations, Phase 1 regressions
python -m pytest PHASE3/tests -q             # Phase 3 pipeline end to end on p2val2 development runs
```

- **`PHASE2/tests/`**:
  - `test_known_limitations.py` pins the documented failures of Evarb-0.2 (long-range negation, "both figures stand", the cue "correcting") so that they cannot be silently fixed after the freeze;
  - `test_analysis.py` checks pairing, exact sign-flip, Holm, BH and the bootstrap;
  - `test_clients.py` imports the `agentrun_v2` package. That package is not tracked in git, so this file is skipped or fails where the package is absent; the other files run anywhere.
- **`PHASE3/tests/test_phase3_pipeline.py`**:
  - builds a second decoding cell with 30 missing pairs from a real p2val2 run;
  - runs the frozen analysis, the independent cross-check, completeness verification, metrics and report generation;
  - checks the averaging of decodings within task, the missing-as-failure rule, the Holm flags, the parsing of execution-log start and exit lines, and the preregistered verdict rules.
- **Reproducibility check:** `DRY=1 bash PHASE3/scripts/run_phase3_analysis.sh verify && … analyze && … report` reproduces `PHASE3/ANALYSIS/DRYRUN/` byte for byte (checked 18 Nov 2026; the analysis took 10.4 min on a laptop).
- **Last recorded results:**
  - 19 Nov 2026, laptop: PHASE2 tests and PHASE3 tests pass;
  - cluster (job 4268): PHASE3 tests pass, and PHASE2 tests pass apart from `test_clients.py`.
