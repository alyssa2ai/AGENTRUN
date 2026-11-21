# Technical details

Implementation detail that belongs with the code rather than in the paper. The paper's §6 gives the summary;
this file says where to read the rest.

| Topic | Where |
|---|---|
| Arbiter: cue extraction, scope qualifiers, precedence | `PHASE2/scripts/evarb/arbiter.py`; spec in `EVIDENCE_ARBITRATION_SPEC.md` §3–§4; paper §4.2 and Figures 2–3 |
| Policy: rules P1–P4, gating modes, notice rendering, safe submission | `PHASE2/scripts/evarb/policy.py`, `render.py`; paper §4.3 |
| Model client: template, generation settings, parser, seeding | `AGENTRUN_DEEPENING_2026-11-11/scripts/hf_client.py`; paper §6.2 |
| Harness: tools, scorer, outcome categories | `PHASE2/scripts/memlab.py`; paper §7.3 |
| Runner and resume semantics | `PHASE2/scripts/run_p2.py`; paper §6.4 |
| Integrity gates G1–G4 and the client-identity policy | `PHASE3/scripts/finalize_gates.py`, `verify_phase3.py`; paper §6.5 and Figure 9 |
| Reporting-only platform check (G5) | `PHASE3/scripts/platform_continuity.py`, `platform_evidence.json` |
| Analysis | `PHASE2/scripts/analyze_p2.py`; cross-check in `PHASE3/scripts/crosscheck_phase3.py`; paper §5.3 and §9 |
| Full environment, model snapshots, batch scripts | `PHASE4/reproducibility/` |

## Three implementation facts that affect how results should be read

1. **Resume order.** The runner iterates tasks in sorted order (outer) and the twelve conditions (inner), so a
   resumed segment is a contiguous suffix in task order carrying all twelve conditions for every whole task it
   contains. This is why the mid-campaign platform transition is balanced across conditions.
2. **Seeding.** The client calls `torch.manual_seed` once per process, so a resumed sampled cell restarts its
   sampling stream rather than continuing it. One cell is affected.
3. **Arbiter cost.** The deterministic arbiter makes no model calls. The LLM-arbiter conditions add calls, which
   are logged and counted separately from the agent's; cost and latency are reported, not tested.
