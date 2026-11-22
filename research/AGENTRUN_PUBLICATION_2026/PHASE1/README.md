# Phase 1: research deepening

**13–14 November 2026.** Start with `PHASE1_FINAL_REPORT.md`.

| Path | What |
|---|---|
| `PHASE1_FINAL_REPORT.md` | Outcome, completion criteria, headline results, blockers |
| `PILOT_RESULTS.md` | Recovery of the 13 Nov runs (§1), RCS pilot (§3), TEA follow-up (§5) |
| `HPC_RESOURCE_SHARING.md` | Coordination with Veriflow on SIT HPC; diagnostics used |
| `RELATED_WORK_DEEP_DIVE.md` | Full-text review of the six closest papers; §4 temporal-arbitration re-check |
| `ARCHITECTURE_AND_FAILURE_ANALYSIS.md` | The memlab pipeline as implemented; where RCS/TEA attach (§5) |
| `FAILURE_TAXONOMY.md` | Counted failure categories; §6 corrections and pilot mechanisms M8–M14 |
| `CANDIDATE_MECHANISMS.md` | Options; addendum on RCS and TEA |
| `SELECTED_RESEARCH_DIRECTION.md` | §A current direction (14 Nov); §B the 13 Nov version |
| `EXPERIMENTAL_RESEARCH_DESIGN.md` | Phase 2/3 plan (v2) |
| `prototype/rcs.py` | RCS prototype, configs A/B/E/G/R, dev split `p1dev` (unchanged since the 13 Nov runs) |
| `prototype/tea.py` | Temporal Evidence Arbitration: evidence-basis labels; configs T/RT |
| `prototype/p1hold.py`, `FREEZE_p1hold.json` | Held-out development split, frozen before `tea.py` existed |
| `prototype/run_pilot.py`, `launch_pilot.sh` | 13 Nov runner and direct-node launcher (do not use while Slurm works) |
| `prototype/run_tea.py`, `tea_pilot.sbatch` | 14 Nov runner and Slurm job (one GPU) |
| `prototype/test_rcs.py`, `test_tea.py` | Deterministic fixture tests (no LLM) |
| `scripts/pilot_deep_analysis.py` | Cross-run analysis, family-level tests → `data/pilot_deep_*` |
| `scripts/arbiter_offline_eval.py` | Label accuracy of the legacy gate and TEA on p1dev, p1hold, eval2 → `data/arbiter_offline_eval.json` |
| `scripts/analyze_pilot.py`, `failure_taxonomy.py`, `abstention_breakdown.py`, `extract_examples.py` | Per-run tables; Campaign 2 failure analysis |
| `scripts/make_manifest.py` | Writes `HASH_MANIFEST.txt` |
| `raw_pilot/` | Raw runs copied from `<compute-node>` (runs.jsonl, manifest.jsonl, tasks.jsonl, DONE) |
| `logs/` | Queue logs (13 Nov) and Slurm job 4173 logs (14 Nov) |
| `HASH_MANIFEST.txt` | sha256 of every file in this folder |

The frozen harness (`AGENTRUN_DEEPENING_2026-11-11/scripts/memlab.py`, sha256 `dc28584c…`) and all earlier raw results are unchanged. The benchmark-v2 sealed set was not touched.

Reproduction commands: `PHASE1_FINAL_REPORT.md` §7.
