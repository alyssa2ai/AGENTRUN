# Related work deep dive: closest mechanisms

**13 November 2026.**

**Method.** Unlike the Stage 1 matrix (abstracts only), the six closest papers were read in **full text**. They were downloaded from `arxiv.org/html/<id>` (GPM from the PDF) on 13 Nov 2026, converted to plain text, and read section by section for:

- method;
- the component that makes the terminal decision;
- benchmark and protocol;
- results;
- limitations.

Quotations are short and attributed to sections. Bibliographic data is in `../literature/arxiv_metadata.json`.

**Limitations of this review.**

- Searches for further 2025–2026 work could not be run broadly. A delegated search agent failed with a configuration error, and the web search tool was not available in this session. The scan beyond these six papers is therefore the Stage 1 list (30 arXiv papers), not an exhaustive search.
- Only arXiv was searched.

**The question that matters for AGENTRUN.** Our failure analysis shows small agents *retrieve* the right records but take the *wrong terminal action*, and that whether an advisory reliability label is obeyed depends on model size (`FAILURE_TAXONOMY.md` M1–M2). So for each paper we asked four things:

- (a) Does it compare advisory labels with enforced resolution?
- (b) Does it study model-size dependence?
- (c) Does it measure the cost of enforcement when the metadata is wrong or insufficient?
- (d) Does it use small open-weight agents (≤14B)?

## 1. Paper-by-paper

### DISCERN: Preserve at Write, Resolve at Read for Persistent LLM-Agent Memory
- **Authors:** Chirag Ahuja, Vladislav Tanov, Ramcharan Kakarla, Jonathan Taws
- **Status:** arXiv 2611.15729, preprint, 11 Nov 2026

**Method.**
- **Write time:** an immutable event log, with an entity-family graph and a bitemporal fact store as derived views. Facts are LLM-extracted.
- **Read time:** an agentic navigation loop over "deterministic, read-only, zero-LLM tools" (§3.2), including `check_temporal`.
- **Commitment:** "the committed action reduces to a decidable function of the graph" (§3.2). Exactly one of answer / update / abstain / clarify fires.
- **Governance gates:**
  - an *EarnedAbstainGate* ("abstaining or guessing without searching is rejected");
  - an *EarnedAnswerGate* (forces an ambiguity check);
  - a deterministic DeclineRouter;
  - a citation-or-abstain renderer that "bounces once" an uncited answer.

**Who decides.** Deterministic code over an LLM-built graph. Resolution is **enforced**, not advisory.

**Benchmark.** ENT-310: synthetic, generated with Claude Opus 4.8, human-vetted; 310 queries. Also LoCoMo.

**Protocol.**
- Generator: Claude Sonnet 4.6.
- Scoring: a four-judge council (Sonnet 4.6, Opus 4.8, Qwen3-235B, GPT-oss-120B).
- Seeds: headline numbers are three-seed means; ablations are single-seed.

**Results.** ENT-310 macro 0.861; LoCoMo macro 0.663 (abstract and §6). Backbone sensitivity (§5.3, single seed): 0.890 Opus, 0.887 Sonnet, 0.707 Qwen3-235B, 0.610 GPT-oss-120B. The authors attribute the drop to "weaker tool-use and structured-output adherence".

**Limitations (stated).** Per-pillar counts are small, ablations are single-seed, and the benchmark is synthetic.

**(a)–(d):**
- (a) Not addressed. There is no condition where the same reliability information is given to the model as labels instead of being enforced.
- (b) Only across four large hosted backbones; the smallest is 120B.
- (c) Not addressed. The decision rule is exact "given that graph"; graph-extraction errors are not stress-tested against the gates.
- (d) No.

**Overlap with AGENTRUN.** Very high on mechanism. Our RCS rule R3 is essentially the EarnedAbstainGate, and enforced resolution at the terminal action is DISCERN's core.

**Gap left.** Whether enforcement is *needed*, and at which capacity, compared with advisory labels; behaviour of ≤14B agents; the cost of enforcement when metadata is insufficient.

### PACMI: Provenance-Aware Cascading Memory Invalidation for Long-Term LLM Agents
- **Authors:** Yiqi Wang et al. (7 authors)
- **Status:** arXiv 2610.05732, preprint, 5 Oct 2026

**Method.**
- A provenance graph with a four-state validity lattice.
- Cascading invalidation to downstream memories.
- Validity-aware retrieval.
- A premise checker that, on detecting an outdated premise, "adds the identified old and current facts to the answer prompt" (§4).

**Who decides.** The LLM, with prompt-level (advisory) correction.

**Benchmark.** Own: 100 cases / 300 queries in five domains, each with a two-hop dependency chain.

**Protocol.**
- Final-answer model and judge: DeepSeek-V4-Pro; intermediate operations (relation classifier, premise checker): DeepSeek-V4-Flash (Appendix A); temperature 0.
- 10,000 case-level bootstrap resamples (all queries of a case together); exact McNemar.

**Results.** Not re-extracted here. The abstract notes that removing cascading "does not reach significance", and §5.5 discusses "why cascading has limited answer-level effect".

**(a)–(d):**
- (a) No; advisory only.
- (b) No.
- (c) Partly: it reports over- and under-invalidation of the graph.
- (d) No; hosted DeepSeek models.

**Overlap.** Provenance-based staleness; the same statistical toolkit (cluster bootstrap, McNemar).

**Gap.** Enforcement versus advisory; small models.

### When Is a Memory Safe Enough to Act On? Action-Conditioned Verification for Long-Lived Agents (AMV-Guard)
- **Authors:** Yiqi Wang, Yifei Wang et al.
- **Status:** arXiv 2610.31446, preprint, 22 Oct 2026

**Method.** Turn retrieved memories into action premises, calibrate a consequence-aware risk, then verify premises greedily by value of information, with stopping and replanning (§3).

**Who decides.** A calibrated decision-theoretic gate before **state-mutating actions**.

**Benchmark.**
- ToolSandbox: 3,520 frozen instances (train 2,240 / dev 640 / test 640), three observation seeds.
- AppWorld: 100 tasks × clean or stale memory.

**Protocol.**
- Backbones: DeepSeek-V4.1-Flash, plus cross-backbone checks with Qwen3.5-27B and Qwen3.5-35B.
- Native state-based evaluators, so no LLM judge.
- Reports coverage together with harm.

**(a)–(d):**
- (a) Compares against "always proceed / always verify / static" policies, not advisory labels.
- (b) No.
- (c) Verifier reliabilities are modelled.
- (d) 27–35B, not ≤14B.

**Overlap.** Verification before acting on memory.

**Gap.** AMV-Guard targets *harmful actions*. Our measured failure is *over-cautious* terminal actions (false conflict, abstention) in question answering.

### Governed Persistent Memory: Source-Bound State Semantics and Fail-Closed Release for Long-Horizon Agents (GPM)
- **Author:** Guodong Xu
- **Status:** arXiv 2608.12476, preprint, 12 Aug 2026; 23 pages

**Method.** An auditable bitemporal state-transition model; deterministic, fail-closed structured release.

**Who decides.** Deterministic services. Enforced.

**Benchmark.**
- GPM-ReleaseBench: 3,600 cases, hash-frozen.
- A sealed end-to-end service evaluation: 2,400 clusters.

**Results.** Governed lane 2,400/2,400 versus 600/2,400 for **ungoverned local Qwen2.5-7B at temperature 0** (Table 3). A version-1 study used Qwen2.5-1.5B and Llama-3.2-1B on LongMemEval and EventQA.

**Limitations (stated, §8).** Internally designed synthetic benchmarks; "an explicit command grammar and eight query families, not arbitrary dialogue".

**(a)–(d):**
- (a) No. Governed versus *ungoverned*, not versus the same metadata given as labels.
- (b) No.
- (c) Partly: fail-closed by design.
- (d) Yes, as the baseline only.

**Overlap.** Deterministic governance on the same base model as ours.

**Gap.** The intermediate condition (label without enforcement) and the size axis.

### STALE: Can LLM Agents Know When Their Memories Are No Longer Valid?
- **Authors:** Hanxiang Chao et al.
- **Status:** arXiv 2605.06527, preprint, 7 May 2026

**Method.** A benchmark plus a prototype, CUPMem. Its "write-side adjudication" is done by an LLM; at query time a "constrained readout under authorized state" blocks invalid premises (§5).

**Who decides.** An LLM adjudicator at write time; constrained (enforced) readout.

**Benchmark.** 400 scenarios, 1,200 queries, contexts up to 150K tokens. Three dimensions: State Resolution, Premise Resistance, Implicit Policy Adaptation.

**Protocol.** Many models, from GPT-4o-mini to GPT-5.4, Gemini 3.1 Pro, Llama-3.3-70B and Qwen3.5-9B/27B.

**Results.** CUPMem raises GPT-4o-mini from 8.7% to 68.0% overall (§5).

**(a)–(d):**
- (a) Not directly.
- (b) Model families are compared on the benchmark, but not compliance with labels.
- (c) "Implicit conflict" means no explicit metadata. That is exactly where a timestamp gate cannot work.
- (d) Partly (Qwen3.5-9B).

**Overlap.** Our S4/S5 scenarios map onto two of its dimensions.

**Gap.** STALE is the natural **external** test for our mechanism's limits (E4).

### When Context Changes: Understanding Update Failures in LLMs (CICM)
- **Authors:** Junyu Guo, Yuchen Fang, Shangding Gu et al.
- **Status:** arXiv 2609.38866, preprint, 30 Sep 2026

**Method.**
- A benchmark of in-context updates.
- Mechanism analysis: probes, attention, and a one-layer theory.
- A test-time fix: "adjust selected attention heads" toward the current value (§6). It is compared against an explicit **reminder** that appends the parser-identified current value.

**Who decides.** The model. The intervention is internal (attention routing) or advisory (reminder).

**Models.** Pythia-160M, Qwen2.5-3B/7B/14B, Llama-3.2-3B, Llama-3.1-8B, Mistral-7B, GPT-4o, GPT-5 and others.

**Results (Table 2).**
- Qwen2.5-3B: original 16.46%, routing 95.21%, **reminder 99.27%**.
- Llama-3.2-3B: 27.71% / 93.12% / **68.85%**.
- Llama-3.1-8B: 41.71% / 88.63% / 65.38%.
- §6: routing beats the reminder "in both Llama models and Gemma, although reminders remain stronger in Qwen".

**Limitations (stated, §8).** Controlled dialogues; no estimate of deployment prevalence; routing needs internal access and a structured parser.

**(a)–(d):**
- (a) **Closest to our question.** It compares an advisory reminder with an internal intervention, and finds advisory compliance is **model-family dependent**.
- (b) Several sizes, but in single-answer dialogue, not an agent with a three-way terminal action.
- (c) No.
- (d) Yes.

**Tension with our data.** CICM's Qwen2.5-3B follows an explicit reminder 99% of the time. Our Qwen2.5-3B ignores a "superseded" label 14 of 16 times in config E. Differences that could explain this:
- (i) CICM states the current *value*; we label *records*;
- (ii) our agent has a `conflict` option and a long rule-laden system prompt;
- (iii) our label is inside a JSON tool result.

This is a testable, specific question, and the Phase 1 pilot touches it.

## 2. Where AGENTRUN stands relative to these

| Dimension | DISCERN | PACMI | AMV-Guard | GPM | STALE/CUPMem | CICM | AGENTRUN (now) |
|---|---|---|---|---|---|---|---|
| Who makes the terminal decision | code over a graph | LLM + prompt | VOI gate | code | LLM, constrained readout | model (+ internal steering) | LLM; E adds labels; RCS adds one deterministic check |
| Advisory vs enforced compared | no | no | no | no | no | reminder vs routing | **yes** (G vs R, pilot) |
| Size axis ≤14B | no | no | no | baseline only | partial | yes (non-agentic) | **yes** (1.5B–14B) |
| Metadata-insufficiency cost | no | partial | modelled | fail-closed | implicit conflicts | no | **S7/S8 stress cases** (pilot) |
| External benchmark | LoCoMo | own | ToolSandbox, AppWorld | LongMemEval, EventQA | own (public) | own | **none yet** |
| Statistics | 3 seeds, judge council | case bootstrap, McNemar | 3 seeds | Clopper–Pearson | — | — | family-level exact tests |

## 3. What remains genuinely open

1. **When is enforcement necessary?** No paper compares *the same* reliability information delivered as an advisory label versus enforced at the terminal action, across model sizes, in an agent loop. Our Campaign 2 data already show the advisory label works at 7B/8B and fails at 3B. That is a measured capacity threshold, not a design claim.
2. **The cost of enforcement.** Enforced resolution is only as good as its metadata. None of the enforcing systems measures how often enforcement *overrides a model that was right* when the metadata is insufficient (same-day corrections, order stated only in text). Advisory labels let a capable model overrule wrong metadata; enforcement does not.
3. **Small open-weight agents.** The enforcing systems use large hosted backbones; the small-model work (CICM) is not agentic.

**Not open (do not claim):**
- deterministic gating;
- forcing search before abstention;
- a provenance graph;
- bitemporal stores;
- a staleness benchmark;
- "retrieval is solved, resolution is not" (DISCERN says it).

## 4. Addendum (14 November 2026): re-check for the temporal-arbitration candidate (TEA)

**Method.** `WebFetch` failed again with a configuration error. DISCERN (2611.15729) and STALE (2605.06527) were therefore re-opened in full HTML in the desktop app's browser. Paragraphs mentioning valid time, transaction time, bitemporal, supersession, correction, timestamps, extraction, ablation and adjudication were extracted and read. The other four papers were not re-read: they make no claim about text-derived temporal order.

**What the papers do.**

- **DISCERN.**
  - Stores changed values "as bi-temporal edges", stamped with the log time *and* "the valid-from/valid-to interval" (§3, Figure 2a).
  - Superseded values are soft-invalidated.
  - The facts and their validity intervals are **LLM-extracted at write time**. The decision rule is exact only "given that graph rather than a claim of ground-truth correctness" (§3.2).
  - The ablations (§5.2 tool suite, §5.3 backbone) **do not perturb extraction or timestamps**.
  - Separating valid time from record time is therefore DISCERN's design, and also decades-old bitemporal-database practice. **TEA's rule "valid time outranks `recorded_on`" is not novel.**
- **STALE.**
  - Axiom 2 (§3.2) **excludes** explicit invalidation: no "surface-level negation", "direct correction", or "explicit obsolescence marking".
  - STALE therefore contains none of the cases TEA's text rules target (same-day corrections that name the old value; explicitly dated validity).
  - CUPMem (§5, App. F) does write-side LLM adjudication into a typed temporal store, with a constrained readout.
  - STALE remains the right external test of what TEA **cannot** do. On implicit conflicts, TEA should at best fall back to metadata order or to `conflicting`, never resolve.

**What is still open after this re-check.**

1. **The cost of a wrong reliability label, measured on the same models with and without the label.**
   - DISCERN, GPM and CUPMem all decide on a structure built at write time. None reports what happens to the *answer* when that structure is wrong.
   - The Phase 1 pilot measures this directly. Metadata-only labels lower Qwen2.5-7B from 22/24 to 3/24 runs on same-day corrections (B → G, S7; `PILOT_RESULTS.md`), and enforcement (R) does not recover them.
2. **Labels that state their evidence basis, with enforcement gated on that basis.**
   - DISCERN's gates enforce uniformly over the graph. None of the papers read distinguishes "ordered by metadata", "ordered by stated validity", "ordered by an explicit correction" and "no ordering evidence" in what the agent is shown, or uses that basis to decide whether to enforce.
   - This is a narrow but defensible mechanism contribution. Whether it is *useful* depends on Phase 2 (`EXPERIMENTAL_RESEARCH_DESIGN.md`).
3. **Precision of the arbiter as a first-class quantity.**
   - The held-out split shows the deterministic arbiter's characteristic error: it confidently resolves a genuine conflict when a cue is negated (p1hold N3: 0/6).
   - An LLM extractor (DISCERN/CUPMem style) is the obvious stronger baseline. Comparing deterministic and LLM arbitration on precision, recall and downstream harm, on small models, is not reported in these papers.

**Novelty statement for TEA (do not go beyond this).**
- The temporal rules are standard.
- What is new is the measurement:
  - of label-induced harm on metadata-insufficient memory;
  - of how much basis-aware arbitration removes, on 3B–8B open-weight agents in a tool loop;
  - of the new harm it introduces through false resolution.
