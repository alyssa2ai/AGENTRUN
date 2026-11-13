# Related work and novelty assessment (memory-reliability thread)

**13 November 2026.**

**How this was built.** Bibliographic data comes from the arXiv API (`scripts/fetch_literature.py`, which writes `literature/arxiv_metadata.json` and `literature/arxiv_title_search.json`; the fetch ran on 13 Nov 2026).

**Search.** Queries were run on arXiv and Semantic Scholar. Semantic Scholar rate-limited the session (HTTP 429), and a general web search tool was unavailable. Coverage of non-arXiv venues (ACL Anthology, OpenReview-only papers) is therefore incomplete.

**Reading depth.** Every entry below was checked against its **abstract only**. No full text was read. "Not in abstract" means the abstract does not say; it does not mean the paper lacks it. Findings marked as numbers are quoted from the abstracts. Before any related-work section is written, the full texts of the six "closest" papers must be read (`OPEN_ISSUES.md` #3).

**Venue.** Unless stated, the venue is an arXiv preprint (not peer reviewed). The DOI is the arXiv DataCite DOI, `10.48550/arXiv.<id>`.

## 1. Closest work (direct overlap with our claims)

| # | Paper | Research question | Method | Benchmark | Key findings (abstract) | Overlap with AGENTRUN | What remains different |
|---|---|---|---|---|---|---|---|
| 1 | **DISCERN: Preserve at Write, Resolve at Read for Persistent LLM-Agent Memory.** C. Ahuja, V. Tanov, R. Kakarla, J. Taws. arXiv 2611.15729 (11 Nov 2026) | Can memory-backed agents resolve conflicting and outdated memories and abstain correctly? | Bi-temporal provenance graph; a zero-LLM tool surface with four gated terminal actions | ENT-310 (310 queries: 210 answerable, 100 unanswerable); LoCoMo | Recall and currency are near-saturated (0.93–0.98); resolution is the unsolved part. Abstention F1 0.924 versus ≤0.802 for baselines; LoCoMo 0.663 versus 0.638 | **Very high.** Provenance-based resolution and deterministic (non-LLM) gating of terminal actions is essentially our configuration E idea, and it is published | DISCERN does not report (in the abstract) an ablation that adds components one at a time; a same-model text verifier; a model-size sweep; or the harness/step-limit failure mode. It posted 2 days before this audit |
| 2 | **PACMI: Provenance-Aware Cascading Memory Invalidation for Long-Term LLM Agents.** Yiqi Wang et al. (7 authors). arXiv 2610.05732 (5 Oct 2026) | How should invalidation propagate through derived memories? | Provenance graph, four-state validity lattice, stale-premise detection | 100 cases / 300 queries (own) | Exact McNemar tests; removing cascading propagation does not reach significance | High: provenance-based staleness, the same statistical test | Cascading derived memories (we have none). No capacity sweep. No text-verifier baseline in the abstract |
| 3 | **When Is a Memory Safe Enough to Act On? Action-Conditioned Verification for Long-Lived Agents.** Yiqi Wang, Yifei Wang et al. arXiv 2610.31446 (22 Oct 2026) | When should an agent re-verify a memory premise before acting? | Sequential stopping problem with value of information (AMV-Guard) | ToolSandbox, AppWorld | Not in abstract (numbers) | High: verification of memory before action | A learned or decision-theoretic verifier versus our simple same-model verifier and deterministic gate. Uses external agent benchmarks, which we lack |
| 4 | **Knowing When the Evidence Is Enough: Requirement-Directed Search with Horn-Closure Certificates.** Xinyu Zhang, Weiwei Sun. arXiv 2610.34684 (26 Oct 2026), cs.IR | When is retrieved evidence sufficient to answer? | Structural sufficiency certificates (answer / search / abstain) | Not in abstract | Not in abstract | Medium: deterministic abstain decisions | Information retrieval, not agent memory with staleness or conflict |
| 5 | **Delivered, Not Used: Evaluating Agent Memory at Its Point of Use.** Changran Xu, Zeju Li, Qiang Xu. arXiv 2611.01718 (1 Nov 2026) | Does delivered memory actually change agent behaviour? | Point-of-use evaluation | 8,000 SWE-bench Verified episodes | Resolve rates within 0.4 pp of no memory; most delivered entries are irrelevant or unused | Medium: "memory is not used" matches our 1.5B finding (never calls `memory_search`) | Coding tasks, a single setting. Our size sweep shows the delivered-but-unused regime is capacity-dependent |
| 6 | **Confident Fools or Careful Searchers? A Behavioural Study of When LLMs Search Beyond Their Static Internal Memory.** Nipun D. Pathirage, Kwan Srijomkwan. arXiv 2610.41124 (30 Oct 2026) | When do LLMs decide to search? | Search-decision scores (NAS/KIS) | 400 multiple-choice questions, 5 commercial LLMs | Not in abstract (numbers) | Low–medium: the decision to consult external memory | Commercial models, multiple choice; no agent harness |

## 2. Benchmarks for memory staleness and conflict

| Paper | Venue | Benchmark | Relevance |
|---|---|---|---|
| **STALE: Can LLM Agents Know When Their Memories Are No Longer Valid?** H. Chao, Y. Bai, R. Sheng et al. arXiv 2605.06527 (7 May 2026) | preprint | 400 expert-validated scenarios, 1,200 queries, contexts up to 150K tokens; State Resolution, Premise Resistance, Implicit Policy Adaptation | Our S4 (stale) and S5 (unsupported premise) map onto two of its dimensions. Its "implicit conflict" (no explicit timestamp) is exactly where our gate has no purchase. **Best external test for us** |
| **Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions (MemoryAgentBench).** Yuanzhe Hu, Yu Wang, Julian McAuley. arXiv 2507.05257 (7 Jul 2025) | preprint | Four competencies, including selective forgetting (conflict resolution) | External benchmark candidate |
| **Bookkeeping, Composition, or Unreachable Gold? Reading MemoryAgentBench's Conflict-Resolution Scores Against a Frozen Last-Write Resolver.** Egor Pakhomov, Erik Nijkamp. arXiv 2610.09193 (6 Oct 2026) | IAB workshop at NeurIPS 2026 (per arXiv comment) | MemoryAgentBench conflict split | A frozen last-write rule answers 80.25%, and some gold answers are unreachable. **Directly relevant:** a deterministic recency rule, like our gate, can solve much of an existing conflict benchmark. Any use of MemoryAgentBench must report this baseline |
| **When Context Changes: Understanding Update Failures in LLMs (CICM).** Junyu Guo, Yuchen Fang, Shangding Gu et al. arXiv 2609.38866 (30 Sep 2026) | preprint | Controlled In-Context Memory benchmark | "Stale binding": probes still recover the updated value when the model answers with an old one. Attention-drift mechanism in Qwen and Pythia. Mechanistic explanation for the failure our gate patches |
| **LongMemEval.** Di Wu, Hongwei Wang, Wenhao Yu et al. arXiv 2410.10813 | ICLR 2025 (per arXiv comment) | Long-term chat memory, including knowledge updates and abstention | Background; external benchmark candidate |
| **Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo).** A. Maharana, D.-H. Lee, S. Tulyakov et al. arXiv 2402.17753 | preprint (venue not checked) | Long conversations | Background; used by DISCERN, MEMOIR, TOKI |

## 3. Memory systems with provenance, temporal state or governance

| Paper | Key idea (abstract) | Relation |
|---|---|---|
| **Governed Persistent Memory: Source-Bound State Semantics and Fail-Closed Release for Long-Horizon Agents.** Guodong Xu. arXiv 2608.12476 (12 Aug 2026) | Bitemporal state-transition model, fail-closed release. Governed lane 2,400/2,400 versus 600/2,400 for **ungoverned local Qwen2.5-7B** | Same base model as ours, deterministic governance beats the model. Pre-empts "deterministic gate beats model" as a novel claim |
| **TOKI: A Bitemporal Operator Algebra for Contradiction Resolution in LLM-Agent Persistent Memory.** Ziming Wang. arXiv 2606.06240 (4 Jun 2026) | Contradiction resolution as write-time concurrency control; LLM judge on the write path admits anomalies | Formal treatment of what our gate does informally |
| **StateWise: Diagnosing and Repairing Persistent Operational State Before Agent Actions.** Yongyuan Peng et al. arXiv 2610.05241 (4 Oct 2026) | Repair invalid stored records before action (coding agents) | Pre-action memory validation |
| **Memory Provenance Laundering in LLM Agents: A Non-Amplification Firewall for Persistent Memory (PPMF).** Jinghan Xu, Yiyong Xiao, Wanru Shao. arXiv 2607.29167 (31 Jul 2026) | Provenance lost during consolidation; authorise tools by source authority | Provenance for security, not staleness |
| **MemLineage: Lineage-Guided Enforcement for LLM Agent Memory.** Ciyan Ouyang, Rui Hou. arXiv 2605.14421 (14 May 2026) | Cryptographic provenance and lineage DAG for memory | Security-oriented provenance |
| **Accept Changes, Reject Attacks: Robust Memory Management for LLM Agents.** Runze Zhao, Dongruo Zhou, Sumit Kumar Jha et al. arXiv 2610.41056 (29 Oct 2026) | Outdated memory versus poisoning call for opposite write decisions; evidence-conditioned accuracy (ECA); fine-tuned manager | ECA is a better metric than plain success for our retrieval runs |
| **MEMOIR: A Training-Free Memory Lifecycle for Long-Horizon LLM Agents.** Mayank Anand et al. arXiv 2611.07631 (5 Nov 2026) | Judge-gated consolidation and retrospective attribution; LoCoMo | Lifecycle; staleness via retrieval priority |
| **Many Steps into One: Reasoning Contraction and the Limits of Safe Memory Reuse for LLM Agents.** Jianghong Zhou et al. arXiv 2610.17544 (13 Oct 2026) | Success/failure counters are poor change detectors; 7.0–13.5× more stale answers than certified memories | Theory of stale-memory reuse |
| **How Much Conversation History Does an AI Agent Need?** Danny Kim, Fernando Koch. arXiv 2611.09662 (6 Nov 2026) | Passage budgets on 1,100 BEAM questions | Context-budget background |
| **Memory as Infrastructure.** Mike Helwig. arXiv 2609.05510 (31 Aug 2026) | Operational experience report | Background only |
| **Persistent Memory and Iterative Improvement in an LLM Agent for Chinese-Character Drawing.** Peilin Wu, Yi-Zhuang You. arXiv 2610.24090 (16 Oct 2026) | Memory gives modest gains (+4.6 pp) | Background: memory gains are often small |
| MemGPT (2310.08560), Mem0 (2504.19413), Zep (2501.13956) | Memory architectures | Standard background |
| **FortMem** | Found on Semantic Scholar only (CIKM, 35th); no arXiv id; metadata **not verified** | Do not cite until verified |

## 4. Verification and self-correction (bears on the text-verifier finding)

| Paper | Venue | Relevance |
|---|---|---|
| **Large Language Models Cannot Self-Correct Reasoning Yet.** Jie Huang, Xinyun Chen, Swaroop Mishra et al. arXiv 2310.01798 | ICLR 2024 (per arXiv comment) | Same-model self-correction without external feedback often hurts. **Our C − B penalty is an instance of this known effect, not a new phenomenon** (as `CORRECTIONS.md` item 11 already says) |
| **When Can LLMs Actually Correct Their Own Mistakes? A Critical Survey of Self-Correction of LLMs.** Ryo Kamoi et al. | TACL 2024, 12:1417–1440, DOI 10.1162/tacl_a_00713 | Same |
| **Self-RAG** (2310.11511); **Corrective RAG** (2401.15884) | preprints | Retrieval-side critique and correction |

## 5. Novelty assessment

### What is **not** novel and must not be claimed

1. **Memory improves memory-dependent tasks.** True by construction.
2. **Provenance or a deterministic gate improves staleness and conflict handling.** DISCERN, PACMI, GPM (on the same Qwen2.5-7B), TOKI and the Pakhomov & Nijkamp last-write baseline all cover this.
3. **Same-model verification without external signal can hurt.** Established self-correction literature.
4. **Agents often fail to use delivered memory.** MemUse covers this; CICM covers "stale binding".
5. **A new benchmark of staleness/conflict scenarios.** STALE and ENT-310 are larger and externally validated. memlab is synthetic and templated.
6. **"The first study combining memory, verifier, provenance and gate."** A rare combination of known parts is not a contribution.

### What may still be defensible (needs the full-text check)

1. **Capacity-resolved component ablation within one model family.** The same five-step cumulative ablation was run at 1.5B, 3B, 7B and 14B (plus Qwen3-8B). Which component helps depends on size:
   - 1.5B never uses memory (0 of 256 memory-dependent runs call `memory_search`);
   - 3B benefits from memory only;
   - 7B–8B benefit from provenance and the gate;
   - 14B gains little beyond memory, with stack-specific artefacts.
   
   None of the abstracts above reports a component-by-size interaction. This is an empirical characterisation, not a method, and it currently rests on one family, one greedy run and a synthetic benchmark.
2. **Where the gate's benefit comes from.** Decomposition shows it is almost entirely stale-record selection: S4 accounts for +12.0 of the +16.7 pp. CICM suggests the mechanism, since the model has the current value but binds the old one. A paper could connect the two: a deterministic recency rule fixes a selection failure that probes show is not a knowledge failure. That needs probing experiments we have not run.
3. **Harness effects of the same size as component effects.** Harness v2 (repair turn plus two behavioural rules) gives +15.8 pp, comparable to the gate. Memory-component papers that use one fixed harness may misattribute effects. This is a methodological point; it needs v1r (repair-only) to separate the parts.

### Verdict

As of 13 Nov 2026, the November study **has no clearly novel method**. Its potentially publishable contribution is an **empirical, carefully controlled characterisation** of how the value of each reliability component depends on model capacity and on the harness. Its negative results (verifier harm, unused memory at small scale, memory harming unsupported-premise questions) are kept and positioned against the self-correction and point-of-use literature. See `RESEARCH_CONTRIBUTION.md`.
