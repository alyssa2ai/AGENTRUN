# 6. Implementation

This section describes what was built and how it was run, so that the numbers in Sections 7–10 can be traced to code
and to specific jobs. Nothing here is an experimental result.

## 6.1 Components

| Component | File(s) | Role |
|---|---|---|
| Agent harness | `memlab.py` | the agent loop, tool schemas, tool executors, the scorer |
| Arbiter and policy | `evarb/` (9 modules, version 0.2) | cue detection, evidence-basis assessment, arbitration, the basis-gated enforcement policy, notice rendering |
| Phase 1 comparison mechanisms | `rcs.py`, `tea.py` | the record-conflict scanner (configurations R, RT) and the temporal-expression annotator (T, RT) |
| LLM arbiter | `evarb/llm_arbiter.py` | the model-based arbiter baseline (LA, LG), driven by the same client as the agent |
| Model client | `hf_client.py`, `evarb/clients.py` | a local Hugging Face causal-LM client with a Hermes-style tool template, wrapped per model family by `FamilyClient` |
| Parser | `agentrun_v2.parser` | tool-call extraction from raw generations, with a client-side fallback path |
| Runner | `scripts/run_p2.py` | one cell = one model × one decoding × 268 tasks × 12 configurations; resumable; writes the manifest |
| Analysis | `scripts/analyze_p2.py` | the preregistered statistics |
| Integrity gates | `PHASE3/scripts/finalize_gates.py`, `verify_phase3.py` | G1–G4 (Section 6.5) |
| Platform report | `PHASE3/scripts/platform_continuity.py` | the reporting-only G5 check (Section 11) |
| Cross-check | `PHASE3/scripts/crosscheck_phase3.py` | an independent re-computation of the headline numbers |
| Reports | `PHASE3/scripts/build_reports.py`, `write_results_section.py` | tables, CSVs and the numeric results draft; adds no statistics |

The 14 files that can affect what an agent does — the nine `evarb` modules, `rcs.py`, `tea.py`, `memlab.py`,
`hf_client.py` and `run_p2.py` — are hashed into **every** manifest line at **every** job start. The hash map is
identical across all 20 starts of the campaign.

## 6.2 Model execution

Models run locally through Hugging Face Transformers 5.22.2 on PyTorch 2.15.0 (CUDA runtime 13.2), in bfloat16, on
one NVIDIA L40, loaded from a pinned local snapshot directory with `device_map={"": 0}`. Generation uses at most 700
new tokens per call. Greedy cells set `do_sample=False`; sampled cells set `do_sample=True`, `temperature=0.7`,
`top_p=0.9`, with `torch.manual_seed(seed)` called once when the client is constructed. Chat templates are applied
with thinking disabled where the model supports it. Tool calls are parsed from the raw generation by AGENTRUN's own
parser, and the raw text, the parser version and the parse path are all logged, so a parse failure is visible as
such rather than silently scored as a wrong answer.

## 6.3 Orchestration

Each cell is a Slurm job requesting one GPU. A controller job (`phase3_controller_v2.sbatch`) keeps at most two
cells in flight — one per L40 — resubmits a cell that stops short, and exits only when all 18 cells have written a
`DONE` marker. It writes an append-only event log and a status file, and on completion a SHA-256 manifest of every
raw file. The finalization job (`phase3_finalize.sbatch`) is CPU-only and runs the gates, the staging, the platform
report, the verification, the analysis, the cross-check, the report generation, the numeric results draft and a
SHA-256 seal, stopping at the first failure and recording the stage it stopped at. The campaign therefore needs no
interactive session: the laptop that submitted the first job plays no part in what follows.

## 6.4 Resume semantics

The runner iterates tasks in sorted `task_id` order (outer loop) and the 12 frozen configurations (inner loop),
appending one JSON row per `(task, config)` pair and flushing after each. On restart it reads the rows already
present and skips those pairs. A cell therefore survives an interruption without re-executing completed work, and a
resumed segment is always a contiguous suffix in task order carrying all 12 configurations for each whole task it
contains. Section 11 explains why that property matters for this campaign, and what it does not cover.

## 6.5 Integrity gates

Every job refuses to start unless the `evarb-0.2` files match `FREEZE_evarb.json`, the sealed eval3 directory passes
`sha256sum -c`, and the preregistration's SHA-256 equals the value recorded at the freeze. All 20 starts printed
`freeze evarb-0.2 mismatches []` and the sealed preregistration hash `221013b3cee87c00`.

Before any analysis, four gates must pass:

- **G1** all 18 preregistered cells have a `DONE` marker;
- **G2** every cell holds exactly 268 × 12 = 3216 unique `(task, config)` pairs, with no duplicate and no unparsable
  line;
- **G3** the last Slurm segment of every cell exited 0;
- **G4** every manifest line of a cell agrees on temperature, seed, split hash, code hashes, configurations and on
  every field of the client's **identity**.

G4's client policy (version `g4-v2`) partitions the client metadata. Eighteen fields — backend, family, family
adapter, model, model path, PEFT adapter and its hash, temperature, seed, decoding, maximum new tokens, dtype,
thinking mode, parser version, torch, transformers, CUDA runtime and GPU model — must be present in every start and
equal across starts; a difference or an absence fails the gate and prints the field path and the values. Exactly one
field, `gpu_mem_gib`, is declared *observational*: it is the device's total memory as reported by the driver, it is
recorded in the manifest and nowhere else, and it is excluded from the identity comparison only — its per-start
values are retained and reported. Any client key in neither set fails the gate until it is explicitly classified.
The policy is shared by both validators so they cannot drift apart, and the previous policy is preserved verbatim
alongside it. Section 11 explains why this distinction was needed.

## 6.6 Analysis implementation

`analyze_p2.py` scores each row with the frozen scorer, treats a missing pair or a harness error as a failure,
averages success within task over a model's decodings, forms paired contrasts within model and decoding, clusters by
family = (category, attribute), and runs a two-sided sign-flip permutation test on family-level summed differences
with 100,000 seeded Monte-Carlo draws, a 10,000-resample seeded family bootstrap for the confidence interval, and
Holm correction over the four primary contrasts. `crosscheck_phase3.py` recomputes the per-configuration counts and
the primary effect sizes by an independent route; the pipeline stops unless the two agree exactly. The report
generator reads only those outputs and computes no statistic of its own.
