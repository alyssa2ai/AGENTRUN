# AGENTRUN: Complete Research Dossier

**Alyssa L. — MITACS research interview — 12 November 2026**

*Persistent memory, retrieval, provenance and verification in multi-tool LLM agents: architecture, experiments, evidence and limitations.*

## How to read this document

Every number in this dossier was recomputed from raw experiment outputs by `build/verify_numbers.py`. That script re-scores each agent run with the frozen scorer and re-derives every aggregate, interval and test with code written independently of the original analysis scripts. All thirteen headline figures quoted in the dossier brief matched exactly. Historical numbers from before November 2026 (the 23-task fine-tuning results) come from the committed result files and were re-tallied by `results/verify_results.py`; they are labelled *historical*.

Four kinds of evidence are kept apart throughout, and each table says which it is:

- **Historical:** the original 23-task fine-tuning results (September 2026, Colab T4).
- **Pilot (campaign 1):** the first controlled memory ablation on 48 tasks (11 November).
- **Fresh validation (campaign 2):** the replication and revised-harness experiments on 96 new tasks (12 November).
- **Exploratory (campaign 2):** the model-size sweep, the retriever-inside-the-agent runs, and the client-matched re-run of AGENTRUN's own benchmarks.

Repository paths are relative to the repository root unless stated. "The study folder" means `research/AGENTRUN_DEEPENING_2026-11-11/`.

<!-- pagebreak -->

# 1. Executive summary

## 1.1 What AGENTRUN is

AGENTRUN is a multi-tool LLM agent runtime. A language model runs a think–act–observe loop. It calls tools (a calculator, a word counter, web search and weather) through the Model Context Protocol (MCP), and it keeps a persistent memory of earlier interactions in a small vector store. The project began as a QLoRA fine-tuning study: can a 7-billion-parameter model (Qwen2.5-7B-Instruct) be specialised for multi-tool use on a free Colab T4 GPU, and how should that be evaluated?

## 1.2 The problem it addresses

A tool-using agent can be *capable*, meaning it can solve a task when everything goes right, without being *reliable*, meaning it behaves correctly when things go wrong. Things go wrong all the time: the earlier conversation is gone, the memory holds an outdated or contradictory record, the evidence for an answer does not exist, or a tool fails. Persistent memory is the standard remedy for lost context. But memory adds new ways to fail, such as retrieving the wrong record, trusting a stale one, picking arbitrarily between two that conflict, or answering when the honest answer is "I don't know". The research question of this dossier is:

> **Research question.** How do persistent memory, retrieval, evidence provenance and verification change the reliability of a multi-tool LLM agent, and how does that depend on model capacity?

## 1.3 What was built and evaluated

- **An audit of the original system.** Memory had never been evaluated; the shipped runtime has no verification and no provenance; memory is an in-process store, not an MCP service.
- **A controlled experimental harness** (`memlab.py`) with five configurations that differ by exactly one component: A stateless, B memory retrieval, C + a text-only verifier, D + provenance (record id, date, source), E + a deterministic staleness and conflict gate.
- **Six scenarios** with programmatic ground truth: lost context, retrieval among distractors, conflicting records, stale records, unsupported questions, tool failure.
- **Two frozen evaluation splits** of fictional, seeded tasks (48 and 96 tasks) with an automated leakage audit (77 of 77 checks pass on the second).
- **About 6,600 agent runs on the SIT HPC** (two NVIDIA L40 GPUs under Slurm) over two days, plus 355 runs on hosted models, a retrieval-at-scale benchmark up to 100,000 records, and a client-matched re-run of AGENTRUN's own benchmarks.

## 1.4 The strongest measured findings

Table: The central result. Task success on 96 fresh tasks, Qwen2.5-7B and Qwen3-8B pooled (192 task blocks per configuration; recomputed from raw outputs).

| Configuration | Original harness | Revised harness |
|---|---|---|
| A stateless | 24.5% | 29.2% |
| B memory retrieval | 56.8% | 81.8% |
| C + text-only verifier | 51.6% | 70.3% |
| D + provenance | 62.0% | 75.5% |
| E + staleness gate | 75.0% | 92.2% |

1. **Memory helps.** +32.3 percentage points pooled (95% CI +21.9 to +42.2, p < 0.0001), in every model from 3B parameters up, on two independent fresh splits.
2. **A same-model verifier that sees only text hurts.** −5.2 points (original harness, p = 0.006) and −11.5 points (revised, p < 0.0001). It rejects correct answers it cannot trace to a source.
3. **Provenance plus a deterministic staleness rule make memory dependable on stale data.** Stale-record tasks: 4 of 32 with plain retrieval, 25 of 32 with the rule (32 of 32 with the revised harness).
4. **Memory can stop an agent from abstaining.** Without memory, Qwen3-8B correctly declined 15 of 16 unanswerable questions; with the full system, 1 of 16. It did not invent answers. It searched in a loop until it ran out of steps. Two prompt rules restored 16 of 16 and raised overall success by 15.8 points on both models.
5. **Capacity matters non-monotonically.** Inside one model family (Qwen2.5, 1.5B to 14B), the reliability components pay off most at 7B. The 1.5B model never consults memory, and the 3B model gains from memory only.
6. **Retrieval quality reaches the answers.** With 2,000 extra records in memory, AGENTRUN's default retriever cuts task success from 71.4% to 41.7%; BM25 restores 70.3%.
7. **The fine-tuned adapter does not generalise.** It scores 23 of 23 on the original benchmark in five out of five matched runs, but on 55 fresh tasks it is no better than its base model (92.7% vs 94.5%).

## 1.5 What remains unresolved

- Seven of 21 jobs in the second HPC campaign never started, because the Slurm controller became unreachable. Missing: dense retrieval inside the agent, the repair-only harness variant, the adapter on the memory benchmark, and sampled repeats of the revised harness.
- All tasks are synthetic, templated facts with clean entity–attribute keys.
- The model-size sweep covers one family, one greedy trial per cell, and one tool implementation. The 14B model showed an unexplained switch to Thai in its free-text reasoning.
- Differences in harmful answers are too rare to test statistically.
- The sealed 130-task test split built in October has not been used.

<!-- pagebreak -->

# 2. Research motivation and problem statement

## 2.1 What goes wrong with a stateless agent

A stateless LLM agent sees only its context window: the system prompt, the current conversation and the tool results of this episode. Nine failure modes follow, and the experiments in this dossier observe each of them in real transcripts:

1. **Context limits.** Facts from earlier sessions are simply absent. In every experiment here, the stateless configuration A solves none of the context-loss, retrieval, conflict or stale-record tasks, because the answer exists only in memory.
2. **Loss of information across sessions.** "In an earlier session I told you the budget" is unanswerable without persistence.
3. **Retrieving irrelevant information.** A memory search returns the most similar records, which often belong to another project or another attribute.
4. **Conflicting knowledge.** Two records state different values for the same fact on the same day.
5. **Outdated memories.** An old value and a newer value coexist; similarity search does not know which is current.
6. **Unsupported answers.** The agent states a value for which it has no evidence.
7. **Incorrect tool execution.** Malformed calls, unsupported operations (for example `round(...)` in a calculator that only does arithmetic), or tools that time out.
8. **Repeated tool calls.** The agent re-issues a call that already returned "not found".
9. **Failure to abstain.** The agent cannot conclude "the evidence is insufficient" and keeps searching until a step limit stops it.

## 2.2 Why "add a vector database" is not enough

A vector store fixes the first two problems and makes the next three more likely. Similarity search ranks by surface resemblance, not by truth, recency or authority. It will happily return a superseded record, return two contradictory records without saying so, or return near-misses for a question that has no answer. Unless the agent is given the means to judge what it retrieved, more memory means more confident errors. That is the motivation for testing provenance (where and when a record came from), verification (an explicit check of the answer against the evidence) and a deterministic reliability rule (which record is current) as separate, measurable components.

## 2.3 Capability versus reliability

The distinction is central to this work and to the scoring:

- **Capability** is whether the agent can produce the right answer when the answer is available, which is measured as task success on answerable tasks.
- **Reliability** is whether the agent's *behaviour* is appropriate across conditions: it answers when the evidence supports an answer, flags a conflict when the evidence conflicts, abstains when there is no evidence, and recovers from tool failures. It also requires that when it is wrong, it is wrong safely, by abstaining rather than asserting a false value.

For this reason every run is classified into one outcome, and **task success** is reported separately from **harmful assertions**. An over-cautious agent loses task success but causes no harm; a confident wrong answer is harmful even if it is rare. Chapter 7 defines every outcome.

## 2.4 Research question and hypotheses

The working question is: *How can persistent memory, retrieval, provenance and verification improve the reliability of multi-tool LLM agents, and how do these mechanisms behave across different model capacities?* It was broken into five hypotheses, fixed before the first evaluation run (`RESEARCH_QUESTION.md` in the study folder):

Table: Hypotheses and their current status (details in Chapters 10–13).

| | Hypothesis | Status |
|---|---|---|
| H1 | Memory improves task completion when context is missing | Supported on both fresh splits and in every model from 3B up |
| H2 | Verification reduces unsupported or incorrect answers | Not supported as stated: text-only verification lowers success; its effect on harmful answers is too small to test |
| H3 | Provenance improves handling of stale and conflicting records | Supported on 7-8B models; small or absent on larger hosted models |
| H4 | The combined system beats any single component | Supported at 7-8B; not at 3B, 14B or on the larger hosted models |
| H5 | The components cost latency, tokens and add their own errors | Supported: about +33% latency and +35% tokens; more false conflicts |

<!-- pagebreak -->

# 3. Evolution of AGENTRUN

![Project timeline. Blue: the original fine-tuning project; pink: the research deepening on the SIT HPC.](figures/fig03_timeline.png)

## 3.1 The original AGENTRUN (August–September 2026)

The first system had two independent halves (Diagram A in Chapter 4).

**The runtime.** `agent.py` runs a Gemini model in a think–act–observe loop of at most six steps. It launches `mcp_server.py` (a FastMCP server) as a subprocess over stdio, discovers its four tools with `list_tools()`, and executes the model's function calls through `session.call_tool`. Before each user turn it searches `memory.py`'s `VectorMemory` for the three most similar past entries and prepends them to the prompt; after each final answer it stores "User asked: … Agent answered: …" as a new memory. `ft_agent.py` runs the same loop with a Qwen model served from a Colab notebook over HTTP; it uses the MCP tools but no memory.

**The fine-tuning study.** QLoRA adapters for Qwen2.5-7B-Instruct were trained on small sets of tool-use trajectories and evaluated on a fixed, machine-scored, 23-task multi-tool benchmark (`eval/tasks.py`, 12 categories). Every condition was run once, greedily, with a three-step budget, against live web search and weather APIs.

Table: Historical results on the 23-task benchmark (committed result files, re-tallied by `results/verify_results.py`).

| Condition | Adapter (training trajectories) | Parser | Passed | Accuracy |
|---|---|---|---|---|
| Base | none | single-pass | 22 / 23 | 95.7% |
| V1 | V1 (35) | single-pass | 18 / 23 | 78.3% |
| E4 | V1 (35), unchanged | two-pass | 18 / 23 | 78.3% |
| V2 | V2 (46 = 35 + 11 targeted) | two-pass | 23 / 23 | 100.0% |

What these numbers do and do not show:

- **Base to V1: a regression after specialisation.** Fine-tuning on 35 trajectories lowered the score from 22 to 18 tasks.
- **V1 to E4: not a parser-only ablation.** E4 held the V1 adapter fixed and changed the server-side tool-call parser from single-pass to two-pass. The aggregate did not move, but four individual tasks flipped. E4 was also scored by a different, notebook-local evaluation client with different tool schemas and executors, on a later date with live data, and only pass/fail was recorded. So the V1-to-E4 comparison changes the parser *and* the client.
- **E4 to V2: an iterative intervention, not a controlled experiment.** V2 added 11 training trajectories written *after inspecting V1's failures on these same 23 tasks*, and its training run also changed the optimizer and memory settings. The repository calls this *evaluation adaptation*: the prompts of the 11 trajectories are disjoint from the benchmark prompts (checked by a unit test), but they were designed against this benchmark. The 100% is therefore not evidence of generalisation.

**Why 23 tasks could not establish generalisation.** With 23 tasks and one run per condition, a single task is 4.3 percentage points; Base to V2 is one task. The tasks were used during development; the V2 training data was shaped by them; there was no held-out split; and the live tools made reruns non-reproducible. These limitations motivated benchmark v2 (October: 185 tasks in 17 families, a 55-task development split and a 130-task sealed test split, with leakage checks) and the controlled studies that follow.

## 3.2 First research deepening: campaign 1 (11 November 2026)

The audit showed that memory, the feature the project's research question was about, had never been measured. Campaign 1 built the experimental harness and ran the first controlled ablation:

- 48 frozen evaluation tasks (8 per scenario) plus 12 development tasks, all with fictional entities.
- Five configurations A–E on every task, paired.
- Hosted models (gpt-oss-120b, gpt-oss-20b, qwen3.8-27b through an API), stopped at 71 complete task blocks by a 200,000-token daily quota.
- Local models on the SIT HPC: Qwen2.5-7B, Qwen3-8B and Qwen2.5-7B with the repository adapter (greedy), plus three sampled repeats: 1,440 agent runs.
- A retrieval-only benchmark comparing AGENTRUN's hash embedding with BM25 and two dense models at 2,000 to 100,000 records.

**What was learned:** memory helps strongly; a text-only verifier hurts small models; provenance and the gate help; and three unsolved failure modes appeared: agents that do not consult memory, agents that loop instead of abstaining, and small models that answer in the wrong format.

## 3.3 Second research deepening: campaign 2 (12 November 2026)

An audit of campaign 1 listed what was weak and designed one experiment for each weakness (`CAMPAIGN2_PLAN.md`, committed before any campaign-2 result existed):

- **A fresh 96-task split** (16 per scenario, new names from a disjoint slice of the name pool), frozen before any run, to replicate campaign 1.
- **A revised harness (v2)** to address the three failure modes: one repair turn plus two prompt rules, developed on the 12 dev tasks only. The original harness (v1) was re-run on the same fresh tasks as the control.
- **A model-size sweep** within one family and one serving stack: Qwen2.5-Instruct 1.5B, 3B, 7B and 14B.
- **Retrieval inside the agent:** every memory store padded with 2,000 background records, comparing the hash retriever with BM25.
- **A client-matched re-run of AGENTRUN's own benchmarks** (the 23 original tasks and the 55-task v2 development split), base versus adapter.

It ran as Slurm array 4148 (21 jobs). Fourteen completed with exit code 0; seven were never dispatched because the Slurm controller became unreachable (Chapter 16).

<!-- pagebreak -->

# 4. Complete system architecture

This chapter separates three things that are easy to conflate: the **original runtime** (what AGENTRUN ships), the **research harness** (experimental code written for this study), and **components that exist only in the harness** and have not been integrated into the runtime.

## 4.1 Diagram A: the original runtime

![Diagram A. The original AGENTRUN architecture as found in the repository. Memory is an in-process Python store used only by the Gemini agent; MCP carries the four tools.](figures/fig01_architecture_original.png)

Table: Components of the original runtime and where they live.

| # | Component | Implementation | Notes |
|---|---|---|---|
| 1 | User / task input | `main.py` (interactive), `eval/tasks.py` (benchmark) | |
| 2 | Agent runtime | `agent.py` `Agent.run`; `ft_agent.py` `QwenRemoteClient.run` | at most 6 steps (Gemini) or 3 (benchmark budget) |
| 3 | LLM client | `google.genai` chat (Gemini); HTTP to `serving/colab_server*.py` (Qwen) | the Qwen server also parses tool calls |
| 4 | MCP interface | `mcp_server.py` (FastMCP, stdio) | tools only: calculator, word_count, web_search, get_weather |
| 5 | Persistent memory | `memory.py` `VectorMemory`, file `memory_store.json` | Gemini agent only; text, embedding, timestamp |
| 6 | Memory retrieval | `VectorMemory.search` | top 3 by cosine, similarity at least 0.2 |
| 7 | Embedding and ranking | `memory.embed_text` | 256-d hashed bag of words and bigrams; no neural model |
| 8 | Tool execution | `session.call_tool`; `tools.py` | errors returned as text starting with "ERROR" |
| 9 | Evidence collection | `RunTrace` (tool calls, observations) | for the benchmark scorer, not for the model |
| 10 | Provenance tracking | **not implemented** | the stored timestamp is never read |
| 11 | Verification | **not implemented** | `results/verify_results.py` re-tallies result files; it does not check answers |
| 12 | Temporal reliability checks | **not implemented** | |
| 13 | Conflict detection | **not implemented** | |
| 14 | Response generation | the model's final text | |
| 15 | Logging | `RunTrace`; `results/*.json` | |

One task traced end to end (Gemini agent, "What's my favorite number?", `memory_store.json` holding 12 entries):

1. `main.py` loads `VectorMemory("memory_store.json")`.
2. `Agent.connect` starts `mcp_server.py` over stdio, lists its tools and converts their schemas to Gemini function declarations.
3. `Agent.run` calls `search(prompt, top_k=3)`: the prompt is tokenised, hashed into a 256-dimensional vector and compared by cosine similarity with every stored entry.
4. Matching texts are prepended as `[Relevant facts from long-term memory:] … [Current user message:] …`. No date, source or identifier is passed on, and nothing checks whether two retrieved texts disagree.
5. The model either requests function calls (run through MCP, results appended) or returns a final text.
6. The final text is returned and stored as a new memory. **The agent's own answer is written back into memory without any check that it was correct.**

> **Correction to a common description.** AGENTRUN is sometimes described as having "MCP-based memory". In the code, MCP is the tool layer only. Memory is a Python object inside the agent process, and the Qwen agents used in the fine-tuning study do not use it at all.

## 4.2 Diagram B: the research harness

![Diagram B. The research harness used for all experiments in Chapters 10–14. Configurations A–E switch the memory tool, the verifier, provenance fields and the reliability gate on or off; everything else is identical.](figures/fig02_architecture_research.png)

The harness lives in the study folder: `scripts/memlab.py` (fixtures, memory store, gate, agent loop, verifier, scorer), `scripts/run_ablation.py` (runner), `scripts/hf_client.py` (local-GPU model client), `scripts/stores.py` (padded stores with hash, BM25 or dense retrieval) and `scripts/run_v2_hpc.py` (a bridge to the repository's own v2 runner). It reuses two things from the original code: `memory.embed_text` and `memory.cosine_similarity` for retrieval, and `tools.calculator` for arithmetic.

Table: Which components are original, research-only, or wrappers.

| Component | Status |
|---|---|
| Hash-embedding retrieval, calculator | **Original**, reused unchanged |
| MCP tool server, Gemini agent, `VectorMemory` write-back | **Original**, not used by the harness |
| `memory_search` tool with a per-task JSON store | **Research-only** wrapper around the original retrieval |
| `registry_lookup` tool with scripted failures | **Research-only** fixture |
| `submit_answer` tool (status, value, evidence) | **Research-only** |
| Provenance fields in memory results (D, E) | **Research-only** |
| Verifier call (C, D, E) | **Research-only** |
| Reliability gate (E) | **Research-only** |
| Repair turn and two prompt rules (harness v2) | **Research-only** |
| BM25 and dense retrievers in padded stores | **Research-only** |
| Local-GPU client with the repository's tool-call parser | **Wrapper** around `agentrun_v2.parser` |

**None of the research-only components has been integrated into the production runtime.** The shipped agent corresponds to configuration B: text-only memory retrieval, no verification, no provenance and no gate.

## 4.3 The experimental workflow

![The experimental workflow. Development tasks are used for changes; evaluation splits are frozen, hashed and audited before they are run once per harness.](figures/fig04_workflow.png)

Each campaign follows the same sequence. Tasks are generated from a seed; the evaluation split, the prompts and the configuration are hashed into a freeze record; the static leakage audit runs; the runner refuses to start if any hash differs; every (task, configuration) is run and logged in full; the frozen scorer classifies each run; the transcript audit re-checks isolation; and only then is the paired analysis run.
