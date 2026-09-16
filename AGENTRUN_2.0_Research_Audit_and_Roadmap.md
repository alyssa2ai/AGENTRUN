# AGENTRUN 2.0 — Research Audit, Novelty Assessment & Roadmap

*Prepared as a research-scientist / reproducibility-auditor pass over `alyssa2ai/AGENTRUN`, the linked Zenodo record, and the public `alyssa2ai` portfolio. Grounded in what was actually inspected (README.md, docs/reproducibility.md, full repo file tree, GitHub profile). Where I could not inspect something directly (individual `.py` files, the Zenodo PDF itself, the other 15 repos in depth), I say so explicitly rather than guessing.*

---

## A. Executive Verdict

**Is AGENTRUN worth deepening? Yes — but not as "make v3 get 100% on a harder benchmark."** The current project's real asset isn't the 100% number; it's that you *already* did the hard, unusual thing most undergrad projects skip: you found a regression (95.7%→78.3%), diagnosed it at the trace level, and were honest that the fix is confounded (parser + data changed together) and that the 23-task benchmark is too small to support generalization claims. That intellectual honesty is publishable *behavior*, not just the numbers.

**The strongest opportunity is not "bigger model, more tools, higher score."** It's turning the existing confound (infra bug vs. data effect) into the actual research contribution: a controlled study of **how much apparent "tool-use fine-tuning failure" is actually a serving/parsing artifact vs. a real model/data effect**, using your own V1→V2 transition as the case study, then generalizing it with a proper ablation, a fresh benchmark, and multiple seeds. This is a small, cheap, well-scoped empirical paper — realistically a workshop paper or a solid "systems/negative-results" contribution, not an ICLR/NeurIPS main-track paper. That's fine. It is exactly the right size for an undergraduate international-internship application.

Verdict: **deepen AGENTRUN along the parser/data-confound axis, do not chase a bigger model or a flashier system.**

---

## B. What Has Actually Been Achieved (verified against the repo)

I fetched the repo root, the README, and `docs/reproducibility.md` directly. Here is what is *actually* there, not just claimed:

| Claim | Verified? | Evidence |
|---|---|---|
| Agent loop with tool execution | ✅ | `agent.py`, `ft_agent.py`, `mcp_server.py`, `tools.py` present |
| MCP-based tool layer | ✅ | `mcp_server.py` + `providers/` (weather, search adapters) |
| QLoRA fine-tuning (Qwen2.5-7B, 4-bit NF4) | ✅ | `training/colab_train_7b.py`, `colab_train_7b_v2.py`, `adapter_config.json` |
| 23-task machine-checkable benchmark | ✅ | `eval/tasks.py`, `eval/harness.py`, `eval/report.py` |
| Base/V1/V2 result artifacts | ✅ | `results/eval_results_{base,v1,v2}.json`, matching `.md` reports |
| Trace-level failure analysis | ✅ (claimed + partially shown) | README's "Key Failure-Mode Recovery" table cites specific task IDs |
| Parser bug identified and fixed | ✅ | Explicitly documented as a separate serving-layer change between V1 and V2 |
| Long-term memory module | ✅ (exists, not part of the published experiment) | `memory.py`, `memory_store.json` |
| Docker | ❌ | No Dockerfile/`docker-compose.yml` anywhere in the repo tree |
| Kubernetes | ❌ | No manifests, Helm charts, or `k8s/` directory |
| CI/CD | ❌ | No `.github/workflows/`, no CI config of any kind |
| Automated tests | ❌ | No `tests/` directory, no test files |
| Experiment tracking (W&B/MLflow) | ❌ | Not referenced anywhere in README or reproducibility doc |
| Dataset/environment versioning (DVC, lockfile) | ❌ | Only a plain `requirements.txt`; no `poetry.lock`/`uv.lock`/pinned CUDA/driver versions |
| Deployment / live demo | ❌ | Inference is served from an ephemeral Colab notebook through an ngrok tunnel — not a persistent deployment |
| Public model artifacts (adapters) | ❌ (by design) | README explicitly excludes `.safetensors` weights from the repo |
| Published paper on Zenodo | Partially confirmed | Your GitHub profile links `doi.org/10.5281/zenodo.22346935` and calls it a "published preprint," but a general web search did not surface the record independently — likely just not indexed yet rather than a real problem, but worth double-checking the DOI resolves publicly before citing it on applications. |
| Commit history depth | ❌ thin | The repo shows **3 commits total** — there is no meaningful commit-level audit trail to reconstruct iteration history from; the story lives in the docs, not the git log |

**One concrete finding you should fix immediately:** README.md and `docs/reproducibility.md` **disagree on the actual training hyperparameters**. README lists LoRA alpha=16, target modules `{q,k,v,o}_proj`, per-device batch size 2 with grad-accum 4. `docs/reproducibility.md` lists LoRA alpha=32, target modules `{q,k,v,o,gate,up,down}_proj`, batch size 1 with grad-accum 16. These cannot both be the config that produced the reported numbers. This is exactly the kind of small reproducibility defect that a reviewer or interviewer *will* find in five minutes, and it currently undermines the "reproducibility" claim more than any missing Docker file would. Fix this before anything else — check which script (`colab_train_7b_v2.py`) was actually run and correct whichever doc is wrong.

---

## C. Current Scientific Weaknesses (brutally honest)

1. **The headline number (100%) is not a generalization claim, and your own README already says so** — this is good, keep it, but it means the number cannot be the centerpiece of an application; the *diagnostic process* has to be.
2. **V1→V2 is a single, unblinded, hindsight-informed intervention.** You saw V1's failures, then built V2's data specifically to fix them, and changed the parser at the same time. Standard category-level information leakage. You already know this — it's in your limitations section — but right now it's stated, not resolved.
3. **N=1 everything.** One model, one seed, one benchmark, one decoding strategy (greedy), one run per condition. No variance estimate exists, so "18/23" vs "22/23" (a 4-point swing) could partly be noise you have no way to quantify.
4. **23 tasks is too small to support fine-grained category claims.** Some categories (e.g., "adversarial ambiguity") have exactly 1 task. A single flipped task moves the reported category accuracy by 100 percentage points. Category-level claims should be treated as illustrative, not statistical.
5. **No independent/external benchmark.** Everything is measured on a benchmark you wrote yourself, so "generalization" cannot currently be claimed in any form.
6. **The infra-vs-data confound is unresolved.** This is your single biggest opportunity (see Section E), not just a weakness.
7. **No deployment/CI/tests is fine for a solo research repo at this stage** — reviewers at ML venues will not penalize you for missing Kubernetes. They *will* penalize missing seeds, missing ablations, and missing an external benchmark. Prioritize accordingly (see Section P).

---

## D. Literature Landscape (what the field actually expects)

You don't need an exhaustive review to know where you stand — the shape of the relevant literature is well established and stable enough to summarize without needing to search it fresh:

- **Tool-use/function-calling benchmarks** (e.g., ToolBench/ToolLLM-style benchmarks, the Berkeley Function-Calling Leaderboard, API-Bank, AgentBench, WebArena/WebShop-style environments) typically report results on **hundreds to thousands of tasks**, across **multiple models**, with **explicit train/test task disjointness enforced by construction** (not just "we kept prompts different"), and often report **tool-selection accuracy separately from end-to-end task success**.
- **Agent fine-tuning work** (ReAct-style SFT, FireAct, AgentTuning, ToolLLaMA-style QLoRA/LoRA fine-tunes) nearly always reports **multiple seeds or at least multiple training runs**, and increasingly separates "did the model call the right tool" from "did the overall trajectory succeed," because these two things fail for different reasons.
- **Failure-analysis / evaluation-leakage literature** (contamination studies, adaptive-benchmark critiques) is exactly the frame your own limitations section is gesturing at — this is a real, active concern in the field (people are actively worried that iterative "fix what you see fail" workflows silently overfit evaluation sets), which is good news: it means your confound *is* the interesting research question, not just a flaw to apologize for.
- **What "publishable" looks like at these venues**, distilled: a real ablation isolating causal factors, a benchmark (or held-out slice) the authors did not iterate against, at least 2–3 seeds or repeated runs with reported variance, and an honest limitations section (you already do the last one well).

**What AGENTRUN currently lacks relative to this bar:** scale (23 vs. hundreds of tasks), seeds, a clean held-out generalization set, and the parser/data ablation. **What it has that a lot of undergrad portfolio projects don't:** a real, documented regression-then-recovery story and a genuinely interesting confound to resolve.

---

## E. Novelty Opportunities (ranked)

1. **[Recommended] Disentangling infrastructure failure from model/data failure in agent fine-tuning evaluation.** Use your own V1 (broken parser) vs. V2 (fixed parser) transition as the seed case, then run the missing 2×2 (parser × data) ablation properly, with a fresh benchmark and seeds. Novelty: modest but real — most agent-eval papers don't explicitly separate "the model didn't call the tool right" from "the serving layer mis-parsed a correct call." Feasibility: high, cheap, uses code you already have. Fit: workshop paper, systems-for-ML track, or strong internship/master's writing sample.
2. **Failure-driven vs. random/coverage-matched data augmentation for tool-use recovery.** Isolate whether *targeted* augmentation (what you did) beats *equal-sized random* augmentation, holding the parser fixed. Directly tests whether "failure-driven" is doing real work or whether more data of any kind would have fixed it. Novelty: good, directly addresses a real methodological question in self-improvement/curriculum literature. Feasibility: medium (needs a random-augmentation dataset of matched size).
3. **Tool-complexity scaling curve (4→8→12 tools) and failure-rate degradation.** Interesting but expensive relative to payoff — building 8 new tools and a matched benchmark is a lot of engineering for one scaling curve. Rank lower unless #1 and #2 are done first.
4. **Cross-model replication (Qwen2.5-7B vs. one comparable 7–8B open model, e.g., Llama-3.1-8B-Instruct).** Valuable for showing the parser-confound finding isn't Qwen-specific, but should come *after* #1 is nailed down on one model — otherwise you're multiplying an unresolved confound across models instead of resolving it once.
5. **A reusable failure taxonomy for tool-use agents, validated across your own and one external benchmark.** Good secondary contribution, cheap to produce as a byproduct of #1 and #2 rather than as a standalone project.

**Recommended primary research question:**

> *"When a QLoRA fine-tuning intervention appears to fix tool-use failures, how much of the observed recovery is attributable to the training-data change versus to a concurrent change in the serving/parsing infrastructure — and does this distinction hold up on a benchmark that was not used to design the intervention?"*

This is scoped, cheap, honest about being a case study, and directly resolves the one flaw every reader of your README will immediately spot.

---

## F. Complete Experiment Matrix

| ID | Condition | Model | Parser | Data | Benchmark | Purpose |
|---|---|---|---|---|---|---|
| E1 | Base + old parser | Qwen2.5-7B base | original | none | original 23-task | reference (already have: 22/23) |
| E2 | Base + fixed parser | Qwen2.5-7B base | fixed | none | original 23-task | isolates infra effect on base model |
| E3 | V1 + old parser | +LoRA v1 (35 traj) | original | 35-traj | original 23-task | reference (already have: 18/23) |
| E4 | V1 + fixed parser | +LoRA v1 (35 traj) | fixed | 35-traj | original 23-task | **the missing cell** — isolates how much of V1's regression was parser, not model |
| E5 | +LoRA (35 traj) + fixed parser + random aug to 46 | random augmentation, matched size | fixed | 46-traj random | original 23-task | tests whether *targeted* augmentation matters vs. just more data |
| E6 | V2 (as published) | +LoRA v2 (46 traj, targeted) | fixed | 46-traj targeted | original 23-task | reference (already have: 23/23) |
| E7 | V2, 3 seeds | +LoRA v2 | fixed | 46-traj targeted | original 23-task | variance estimate on the headline result |
| E8 | Base, V1, V2 | all three | fixed | — | **fresh held-out benchmark** (new tasks, not used to design V2) | the real generalization test |

Metrics to report for every cell: task success rate, tool-selection accuracy (right tool chosen, regardless of final answer correctness), argument-correctness rate, and a parser-failure flag (call was semantically correct but mis-parsed) — this last one is the metric that actually answers your research question and does not currently exist in your eval harness.

**Do this in order: E4 first** (it's the single missing cell that resolves your stated confound and costs almost nothing — you already have the fixed parser and the V1 adapter). Then E8 (fresh benchmark) before E5/E7, because generalization evidence matters more to reviewers than more seeds on a benchmark you already might be overfit to.

---

## G. Model Comparison Strategy

**Minimum for a defensible study: one model family, self-comparison (base → V1 → V2), which you already have.** Do not add a second model family until E1–E8 above are done — adding Llama-3.1-8B now would just multiply an unresolved confound across two models instead of resolving it once.

**If you do add a second model later** (recommended only after the ablation is clean), pick based on: open weights, similar parameter count (7–8B) so compute stays comparable, active community adoption (so a reviewer recognizes it), and a genuinely different tokenizer/chat template (so parser bugs of the *same kind* you found are a meaningful cross-check, not a coincidence). Llama-3.1-8B-Instruct or Mistral-7B-Instruct-v0.3 are reasonable, well-supported choices. One model family, one added cross-check model is the right scope — do not go to 3+ models; it adds compute cost without adding much evidential value at this project's scale.

---

## H. Benchmark / Leakage Strategy

Your original 23 tasks are now permanently "seen" for design purposes — they can stay as a fixed regression benchmark, but must never again be used to justify a new intervention. For the fresh benchmark (E8):

- Write it **before** looking at any new model outputs, and freeze it (hash the file, note the git commit) before running anything.
- Match the original benchmark's category distribution (math, multi-tool, adversarial, no-tool-expected, etc.) so it's comparable, but use **new task instances**, not paraphrases of the old ones — a near-duplicate is still leakage.
- Keep it disjoint from the *training* trajectories too, not just the eval set — check that no fresh-benchmark task shares a template with `training_data_augmented.jsonl`.
- Consider a **train / dev / frozen-test** split going forward: use a small dev slice for any future "look at failures, then adjust" iteration, and never touch the frozen test slice until the very last run of a given paper draft.

---

## I. Failure Taxonomy

Categories consistent with what your README already documents from actual traces (don't invent categories you haven't observed):

- **Infrastructure/parser failure** — correct model intent, mis-parsed by the serving layer (your actual V1 finding)
- **Tool omission** — model answers without calling a required tool
- **Premature termination** — stops after one tool in a multi-tool task
- **Step-budget exhaustion** — correct plan, runs out of `max_steps`
- **Manual computation instead of tool use** — model computes a value itself when the benchmark requires the calculator
- **Tool-error mishandling** — division-by-zero / error cases not handled correctly
- **False-premise failure** — fails to challenge an incorrect premise in the prompt

This taxonomy is a reasonable byproduct of E1–E8, not a project on its own — validate it by having it account for ~90%+ of observed failures across both the original and fresh benchmark before calling it "reusable."

---

## J. Reproducibility & Deployment Audit

**Mandatory (do these):**
- Fix the README vs. reproducibility.md hyperparameter mismatch (Section B).
- Pin exact package versions (`pip freeze > requirements-lock.txt`), Python version, and note the actual Colab GPU/driver/CUDA version used for each run.
- Record and publish the random seed for every training run and eval run; currently none is mentioned anywhere.
- Add a single `run_all.sh`/Makefile target that reproduces one full condition end-to-end (data → train → serve → eval → report) — this is what a reviewer actually tries to run, and right now it's a 7-step manual Colab/ngrok dance.

**High-value:**
- Replace the ngrok-tunnel-to-ephemeral-Colab-notebook serving path with a small persistent inference script (even a local one, if compute allows a quantized 7B on your own hardware or a free-tier Space) so "reproduce this" doesn't depend on a live tunnel URL someone has to hand you.
- A lightweight experiment log (even a CSV/JSON of run → config hash → result) beats a full MLflow/W&B setup at this scale — don't over-invest in tooling.

**Explicitly not worth it right now — do not do:**
- **Docker**: mildly useful for environment pinning, but your actual reproducibility gap is the manual Colab/ngrok workflow, which Docker doesn't fix (Colab training still won't run in a container the way you're using it). A simple `requirements-lock.txt` + documented CUDA/driver version gets you 90% of the benefit for a fraction of the effort.
- **Kubernetes**: there is no serving load, no multi-replica requirement, and no orchestration problem here. This would be pure resume-keyword engineering with zero research or even engineering payoff for a single-researcher benchmark project. Do not add it.
- **CI/CD pipeline**: nice eventually, but you don't have tests to run yet — write tests first (unit tests for the parser and the eval harness scoring logic, which is exactly the code that had a real bug) before CI has anything to check.

---

## K. Portfolio Comparison

Based on your public GitHub profile (not a deep code audit of each repo — that would need per-repo inspection I haven't done):

| Project | Likely tier | Why |
|---|---|---|
| **AGENTRUN** | Research-grade (in progress) | Has a real experiment, real failure analysis, honest limitations — the strongest research signal in the portfolio |
| **Waggle-mcp** | Strong engineering evidence | Graph-backed memory layer, hybrid retrieval, provenance/contradiction handling — a legitimate systems project, complementary to AGENTRUN's memory module rather than redundant with it |
| **agentic-rag-researcher** | Strong engineering / possibly research-adjacent | Multi-tool RAG + iterative refinement; check whether it has any evaluation at all — if not, it's engineering evidence, not research evidence |
| **nanogpt-from-scratch** | Strong fundamentals evidence | Good for demonstrating you understand transformers bottom-up; not a research contribution, keep it as a fundamentals signal |
| **CropScoutAIoT** | Notably interesting — worth a closer look | You describe finding a "training/deployment preprocessing mismatch" causing failure under edge conditions — that is itself a small failure-analysis story, structurally similar to what makes AGENTRUN good. Don't deepen it as a second research track, but it's good supporting evidence of a consistent "finds and diagnoses failure modes" research identity. |
| **Pawsight** | Portfolio/demo-grade with a nice touch | EfficientNetB0 + Grad-CAM is solid applied CV, but interpretability-as-a-feature isn't the same as an interpretability *research* contribution |
| **GROMACS/HPC work** | Portfolio/demo-grade, different track | Interesting breadth signal (scientific computing) but a different research identity from agentic AI; don't try to merge the two into one narrative |

**Recommendation:** AGENTRUN stays central. Waggle-mcp is worth keeping visible because "memory infrastructure" pairs naturally with "agent reliability" as a research identity, without duplicating AGENTRUN's contribution. I'd need to actually read the other repos' code (not just their one-line descriptions) to responsibly say more than this — happy to do that if you point me at specific ones.

---

## L. Venue Strategy

| Venue | Fit | What's needed beyond current state |
|---|---|---|
| **ICLR / NeurIPS / ICML main track** | Poor fit at current scope | These expect broad benchmarks, multiple models, strong baselines against prior tool-use methods — a big step up from a 23-task single-model case study |
| **AISTATS** | Poor fit | Statistical/methodological bar is high; your current N=1-seed setup wouldn't clear it |
| **ACL/EMNLP (findings or workshop)** | Possible after E1–E8, workshop track only | Relevant tool-use/agent workshops at these venues are a realistic target once you have the ablation + fresh benchmark |
| **Relevant agent/tool-use workshops (ICLR/NeurIPS/ACL workshops on LLM agents, tool use, or reliability)** | **Best realistic target** | Workshops explicitly welcome smaller-scale, well-controlled negative-results/diagnostic studies exactly like the one in Section E |
| **arXiv preprint + Zenodo (as you're already doing)** | Good, keep doing this | Lets you cite the work on applications regardless of formal acceptance |

**Primary target:** an LLM-agent/tool-use workshop at a major 2026/2027 venue (ACL, NeurIPS, or ICLR workshop track), once E4 and E8 are done. **Secondary:** a solid arXiv/Zenodo writeup even without formal acceptance — this is already what you're doing and it's the right minimum bar for internship applications. **Safe/realistic target:** treat the whole thing as a rigorous case-study writeup, cited on applications as "under submission to [workshop]" rather than forcing a top-tier submission. **Workshop fallback:** any ICLR/NeurIPS 2027 LLM-agent or reliability workshop — check calls as they open closer to the date.

---

## M. ICLR 2027 Decision

Abstract deadline September 18, 2026 and paper deadline September 25, 2026 are roughly **10–17 days from today (September 8, 2026)**. Honest scores for the current project against ICLR main-track expectations (0–10):

| Dimension | Current | After 2 weeks | After 1–2 months |
|---|---|---|---|
| Novelty | 3 | 4 | 5 |
| Research question clarity | 4 | 7 | 8 |
| Experimental rigor | 2 | 4 | 7 |
| Generalization evidence | 1 | 2 | 6 |
| Benchmark quality/scale | 2 | 2 | 4 |
| Statistical rigor | 1 | 2 | 5 |
| Baselines | 1 | 1 | 3 |
| Reproducibility | 3 | 6 | 8 |
| Writing | — (no draft yet) | 4 | 7 |
| Significance | 3 | 4 | 6 |

**Recommendation: do not submit to ICLR 2027 main track.** Even with two weeks of focused work you cannot get generalization, baselines, and statistical rigor to a defensible main-track bar — and a rushed, weak submission is worse for your application record than no submission. Use the next 1–2 months to run E4, E7, and E8, then target a workshop with a rolling or later deadline. This is a better use of the same effort.

---

## N. Phased Roadmap

- **P0 (this week):** Fix the README/reproducibility.md hyperparameter mismatch. Pin package versions and seeds. Confirm the Zenodo DOI resolves publicly and matches what's cited on your profile.
- **P1 (1–2 weeks):** Run E4 (V1 + fixed parser) — this is the single highest-value experiment you haven't run, and you already have everything needed for it.
- **P2 (2–4 weeks):** Design and freeze the fresh held-out benchmark (E8, same category distribution, new task instances). Run Base/V1/V2 on it.
- **P3 (3–5 weeks, parallel with P2):** Add tool-selection-accuracy and parser-failure-flag metrics to `eval/harness.py` so E4 and E8 produce more than pass/fail.
- **P4 (4–6 weeks):** Run E7 (3 seeds on V2) and E5 (random-augmentation control) if compute allows.
- **P5 (ongoing):** Write the paper around the resolved confound + fresh-benchmark result. Target a workshop deadline.
- **P6 (only if P1–P5 land clean and you have spare capacity):** second-model replication.

Tool-complexity scaling (Section E, opportunity 3) and Kubernetes/Docker/CI investment are explicitly **not** in this roadmap — see Section O.

---

## O. "Do Not Do" List

- Do **not** add Kubernetes. There is no orchestration problem this project has.
- Do **not** add Docker before fixing the actual reproducibility gap (the manual Colab/ngrok workflow and the hyperparameter mismatch).
- Do **not** scale to 8–12 tools before the parser/data confound is resolved on the current 4-tool setup — it multiplies the unresolved variable instead of resolving it.
- Do **not** add a second model family before E4 and E8 are done.
- Do **not** submit to ICLR 2027 main track.
- Do **not** present the 100% V2 number as evidence of "improved reliability" or "generalization" anywhere (CV, LinkedIn, application essays) — your own README already avoids this; keep that discipline everywhere else too.
- Do **not** start a brand-new flashy project to fill a "systems" gap — Waggle-mcp already covers that; deepen, don't multiply.

---

## Q. Final Recommendation

If I were supervising this project, the next five things I'd have you do, in order:

1. **Fix the hyperparameter mismatch between README.md and docs/reproducibility.md today** — it's a five-minute fix that removes the most easily-spotted credibility gap in the repo.
2. **Run E4 (V1 adapter + fixed parser) this week.** It's nearly free — you already have both artifacts — and it directly answers the question every reader of your current README will ask.
3. **Freeze a fresh 15–20 task held-out benchmark before you look at any new results**, matched in category distribution to the original 23, and run Base/V1/V2 on it.
4. **Add tool-selection-accuracy and a parser-failure flag to the eval harness**, so future results say *why* something failed, not just pass/fail.
5. **Write up E4 + the fresh-benchmark result as a short, honest technical report** (arXiv/Zenodo), explicitly framed as resolving your own stated limitation — this is the single artifact most likely to strengthen an international AI/ML internship application, more than any additional feature, model, or deployment polish would.
