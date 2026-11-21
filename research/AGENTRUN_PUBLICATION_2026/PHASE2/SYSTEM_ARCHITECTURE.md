# System architecture (Phase 2)

**14 November 2026; layout updated 16 November 2026.** The mechanism is frozen as **evarb-0.2** (`FREEZE_evarb.json`).

## 1. Where the mechanism sits

```
user question ─▶ agent loop (memlab v2 prompts, ≤ 6 model steps + 1 for a notice)          evarb/loop.py
                 ├─ memory_search ─▶ MemoryStore.search (frozen, hashed BoW, top-4)          memlab (frozen)
                 │                  └─ same-key records added ─▶ RESOLVER(group) ─▶ labels    evarb/render.py
                 │                        resolver = evarb.arbiter.arbitrate   (EB, EBG*)     evarb/arbiter.py + cues.py
                 │                                 | LLMArbiter.arbitrate      (LA, LG)       evarb/llm_arbiter.py
                 ├─ registry_lookup / calculator (frozen)
                 └─ submit_answer ─▶ POLICY.decide(question, resolutions, retrieved, calls)   evarb/policy.py
                                      ENFORCE | REQUEST_EVIDENCE ─▶ one reversible notice
                                      ADVISE  | NO_ACTION        ─▶ submission stands
               ─▶ safe submission: post-notice failure ⇒ revert to the pre-notice answer   evarb/loop.py
               ─▶ frozen scorer (memlab.score_run)
```

## 2. Modules

| Module | Responsibility | Depends on |
|---|---|---|
| `evarb/cues.py` | Clause splitting; cue kinds; negation / quotation / modality scope; validity dates; rival reference | memlab `_norm` |
| `evarb/arbiter.py` | One group to a `Resolution` (status, basis, strength per record) | cues |
| `evarb/policy.py` | Question intent; basis-gated actions P1–P4; notice text | arbiter |
| `evarb/render.py` | Tool-result labels, mirroring `memlab.memory_tool_result` | arbiter |
| `evarb/loop.py` | Phase 2 agent loop; dispatch of Phase 1 configs to the unchanged `rcs` / `tea` code | memlab, rcs, tea |
| `evarb/llm_arbiter.py` | LLM arbiter baseline with the same schema | a chat client |
| `evarb/clients.py` | Model-family adapter (Llama tool-call format and single-call template) | frozen `hf_client` |

## 3. Frozen components (read only, hash-checked by `scripts/run_p2.py` at every run)

| File | sha256 | Role |
|---|---|---|
| `AGENTRUN_DEEPENING_2026-11-11/scripts/memlab.py` | `dc28584c…` | harness, prompts, tools, scorer |
| `AGENTRUN_DEEPENING_2026-11-11/scripts/hf_client.py` | in each run manifest | local model client |
| `PHASE1/prototype/rcs.py` | `9f0a838b…` | configs A/B/E/G/R |
| `PHASE1/prototype/tea.py` | `37bed1fe…` | configs T/RT |

The Phase 2 code never edits these files. TEA swaps `memlab.reliability_status` only for the duration of a T or RT run, as in Phase 1.

## 4. Configurations

| Config | Labels | Enforcement | Search-before-submit | Safe submission | Origin |
|---|---|---|---|---|---|
| B | none | — | — | — | Phase 1 / memlab |
| G | legacy (`recorded_on` only) | — | — | — | Phase 1 |
| R | legacy | RCS R1/R2 (all) | R3 | no | Phase 1 |
| T | TEA | — | — | — | Phase 1 |
| RT | TEA | RCS (all) | R3 | no | Phase 1 |
| **EB** | **evarb** | — | — | — | Phase 2 |
| **EBG** | **evarb** | **gated (strong only)** | **P3** | **yes** | **Phase 2, proposed** |
| EBG-all | evarb | strong + moderate | P3 | yes | ablation: gating |
| EBG-unsafe | evarb | gated | P3 | **no** | ablation: safe submission |
| EBG-noR3 | evarb | gated | **no** | yes | ablation: search-before-submit |
| LA | LLM arbiter (same model as the agent) | — | — | — | baseline |
| LG | LLM arbiter | gated | P3 | yes | baseline: who arbitrates, with the same policy |

## 5. Data and experiment layout

```
PHASE2/
  evarb/                  mechanism (frozen as evarb-0.2; hashes in FREEZE_evarb.json)
  fixtures/build_dev.py   development fixtures   -> data/dev_groups.jsonl, p2dev_tasks.jsonl, regression_groups.jsonl
  benchmark/              skeleton.py, write_and_annotate.py, assemble.py, agreement.py, seal_checks.py, ANNOTATION_GUIDELINES.md
  data/p2val/             first validation split (v1 semantics; development data since the evarb-0.2 look)
  data/p2val2/            untouched validation split for the frozen evarb-0.2 (v2 semantics)
  data/BASELINE_*         component-level comparison of the four arbitration methods
  scripts/                component_eval.py, component_report.py, llm_arbiter_eval.py, run_p2.py, analyze_p2.py,
                          power_phase3.py, model_smoke.py
  hpc/                    sbatch files (one GPU each, resumable)
  tests/                  unit, regression, integration (mock client), analysis
  raw/                    raw outputs copied from the cluster (hash-verified)
  logs/                   Slurm logs
cluster only: ~/AGENTRUN_HPC/sealed/eval3/   sealed evaluation set (read-only files; hashes in FREEZE_eval3.json)
```

## 6. Environment

- **Laptop:** Python 3.11 (`py -3.11`) for tests and analysis. Dependencies: the standard library, plus the repository's `memory.py` (used by memlab) and `agentrun_v2.parser`. **No GPU is needed** for anything except agent and LLM-arbiter runs.
- **Cluster:**
  - `~/AGENTRUN_HPC/20261111/environment/venv` (Python 3.12.3, torch 2.15.0+cu132, transformers 5.22.2);
  - models from the local Hugging Face cache, run with `HF_HUB_OFFLINE=1`;
  - Slurm partition `gpu-nodes`, `--gres=gpu:1`.
- **pytest** is not installed in the cluster venv. Tests run on the laptop; on the cluster, run scripts verify the frozen split hashes instead.
