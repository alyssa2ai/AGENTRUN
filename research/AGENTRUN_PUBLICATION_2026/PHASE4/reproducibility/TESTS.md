# Tests

```bash
pip install pytest                           # not needed for the experiment itself; see ENVIRONMENT.md
cd research/AGENTRUN_PUBLICATION_2026
(cd PHASE2 && python -m pytest tests -q)     # mechanism, arbiter, policy and loop, analysis helpers, known limitations, Phase 1 regressions
python -m pytest PHASE3/tests -q             # pipeline on p2val2 development runs; G4 client-identity policy; G5 platform report
```

- **`PHASE2/tests/`**:
  - `test_known_limitations.py` pins the documented failures of Evarb-0.2 (long-range negation, "both figures stand", the cue "correcting") so that they cannot be silently fixed after the freeze;
  - `test_analysis.py` checks pairing, exact sign-flip, Holm, BH and the bootstrap;
  - `test_clients.py` imports the `agentrun_v2` package. That package is not tracked in git, so this file is skipped or fails where the package is absent; the other files run anywhere.
- **`PHASE3/tests/test_phase3_pipeline.py`**:
  - builds a second decoding cell with 30 missing pairs from a real p2val2 run;
  - runs the frozen analysis, the independent cross-check, completeness verification, metrics and report generation;
  - checks the averaging of decodings within task, the missing-as-failure rule, the Holm flags, the parsing of execution-log start and exit lines, and the preregistered verdict rules.
- **`PHASE3/tests/test_finalize_gates_v2.py`** proves the G4 client-identity policy (`g4-v2`): a change in the declared observational field `gpu_mem_gib` alone passes and is reported; a changed client adapter, parser version or framework version fails; an unknown client field fails until it is explicitly classified, even when it is identical across starts; missing client metadata fails; each of the 18 identity fields is individually enforced; the previous validator is preserved verbatim and hash-checked. Where the campaign's raw results are present it also checks them: all 18 cells pass, exactly the two known cells report telemetry, and the 16 single-start cells are untouched.
- **`PHASE3/tests/test_platform_continuity.py`** proves the reporting-only G5 check never fails a pipeline, classifies every recorded fact as verified, inferred or unknown, and (against the real campaign) reports 980 of 57,888 rows after the node boot in exactly two cells.
- **Reproducibility check:** `DRY=1 bash PHASE3/scripts/run_phase3_analysis.sh verify && … analyze && … report` reproduces `PHASE3/ANALYSIS/DRYRUN/` byte for byte (checked 18 Nov 2026; the analysis took 10.4 min on a laptop).
- **`test_clients.py` on the cluster.** This file imports `agentrun_v2`, which is not tracked in git and is not present in the cluster checkout, so it errors on collection there. It is reported as a known, named skip rather than omitted from the test report: the rest of `PHASE2/tests` runs, and nothing it covers is used by the confirmatory analysis (the parser it exercises is pinned by hash in every run manifest instead).
- **Last recorded results:**
  - 19 Nov 2026, laptop: PHASE2 tests and PHASE3 tests pass;
  - cluster (job 4268): PHASE3 tests pass, and PHASE2 tests pass apart from `test_clients.py`;
  - 21 Nov 2026, cluster: see `PHASE3/ANALYSIS/TEST_REPORT.md` for the full run, including the `test_clients.py` import failure and the new G4/G5 suites.
