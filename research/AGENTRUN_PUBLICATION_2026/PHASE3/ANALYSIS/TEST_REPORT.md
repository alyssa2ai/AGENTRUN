# Phase 3 test report — 2026-11-21, SIT HPC

Interpreter: `~/AGENTRUN_HPC/20261111/environment/venv/bin/python` (Python 3.12.3), pytest 9.2.0.
`pytest` was installed into the campaign virtual environment on 2026-11-21, after the campaign was complete and
sealed (`PHASE3_DEVIATIONS.md` D6); no GPU run followed, and the 14 frozen code hashes still verify.

| Suite | Location | Result |
|---|---|---|
| Phase 2 mechanism suite, full | campaign source tree `~/AGENTRUN_HPC/20261111/source/.../PHASE2` | **92 passed**, exit 0 |
| Phase 2 mechanism suite, minus `test_clients.py` | HPC clone `~/AGENTRUN_HPC/finalize/AGENTRUN/.../PHASE2` | **88 passed**, exit 0 |
| `tests/test_clients.py` | HPC clone | **collection error** — see below |
| Phase 3 suite (pipeline + G4 + G5) | HPC clone `.../PHASE3/tests` | **28 passed**, exit 0 |

## The `test_clients.py` import problem, stated rather than omitted

In the HPC **clone**, `tests/test_clients.py` fails at collection:

```
evarb/clients.py:24: from hf_client import HFClient
AGENTRUN_DEEPENING_2026-11-11/scripts/hf_client.py:20:
    from agentrun_v2.parser import PARSER_VERSION, parse_model_output
E   ModuleNotFoundError: No module named 'agentrun_v2'
```

**Cause.** `agentrun_v2` is not tracked in git, so it is absent from the clone. It is present in the campaign source
tree (`~/AGENTRUN_HPC/20261111/source/agentrun_v2`), which is where every experiment cell actually ran — which is
why the same suite returns **92 passed** there, including the four `test_clients.py` cases. The failure is an
artefact of the clone's contents, not of the code or of the campaign.

**Consequence for the results.** None. The parser that `test_clients.py` exercises is pinned by SHA-256 in every run
manifest and verified by the integrity gates, and `agentrun_v2.parser`'s version string (`two-pass-v2+client-fallback`)
is recorded identically in all 20 manifest lines. Because pytest aborts collection on an import error, the clone run
must be invoked with `--ignore=tests/test_clients.py` to exercise the other 88 tests; that is a reporting
inconvenience, not a gap in coverage.

**Fix for the future.** Either track `agentrun_v2` in the repository or add it to the package requirements, so that
a fresh clone can run the whole suite. Not done here, because it would change tracked content after the freeze for
no scientific benefit.

## What the Phase 3 suite covers

- `test_phase3_pipeline.py` — end-to-end analysis pipeline on p2val2 development data, including a derived second
  decoding cell with missing pairs: decoding averaging within task, missing-as-failure, Holm flags, execution-log
  parsing, and the preregistered verdict rules. No eval3 data is used.
- `test_finalize_gates_v2.py` — the G4 client-identity policy: a `gpu_mem_gib`-only difference passes and is
  reported; a changed client adapter, parser version or framework version fails with the field path and values
  printed; an unknown client field fails until classified, including when identical across starts; missing client
  metadata fails; every one of the 18 identity fields is individually enforced; the `g4-v1` validator is preserved
  verbatim and hash-checked. Against the real campaign manifests: all 18 cells pass, exactly `qwen3_8b_T07_s3` and
  `llama32_3b_greedy` report telemetry, and the 16 single-start cells are untouched.
- `test_platform_continuity.py` — the reporting-only G5 check: never fails a pipeline, classifies every recorded
  fact as verified, inferred or unknown, requires reasoning on an inferred fact and a "would settle it" on an
  unknown one, and reproduces the real campaign numbers (980 of 57,888 rows after the node boot, in exactly two
  cells, with `eval3-0202` and `eval3-0267` split across starts).

## Other checks run on 2026-11-21

| Check | Result |
|---|---|
| Integrity gates G1–G4 on the real campaign (`finalize_gates.py`, g4-v2) | **PASS**, 18/18 cells DONE, 2 observational notes |
| `verify_phase3.py` completeness and identity check | **no integrity problems** |
| Raw-file checksums (`sha256sum -c SHA256SUMS`, `phase3_raw`) | **54/54 OK** |
| Sealed eval3 checksums | **OK** |
| `FREEZE_evarb.json` file hashes, preregistration hash, seal-manifest hash | **evarb mismatches [] / prereg True / seal manifest True** |
| 14 frozen code hashes vs. every manifest line | **identical across all 20 starts**; live files still match |
| Independent analysis cross-check | **all values agree** (60/60 counts, 4/4 primary differences) |
| Manuscript citation and placeholder check | **PASS** — 37 bib entries, 37 cited, 0 undefined, 0 uncited, 0 placeholders |
| G5 platform-continuity report | 2/18 cells straddle the node boot, 980/57,888 rows (1.693%) |
