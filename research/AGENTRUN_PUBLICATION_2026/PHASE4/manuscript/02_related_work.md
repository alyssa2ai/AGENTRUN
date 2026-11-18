# 2. Related work

> Draft, 18 November 2026. Sources: `RELATED_WORK_AND_NOVELTY.md` (abstract-level review of about 30 arXiv papers, 13 Nov 2026) and `PHASE1/RELATED_WORK_DEEP_DIVE.md` (full-text reading of six papers on 13 Nov, with DISCERN and STALE re-read on 14 Nov). Bibliographic data is from `literature/arxiv_metadata.json` and `literature/arxiv_title_search.json`. Unless a statement below is marked "full text", it rests on the paper's abstract only. The search covered arXiv only; Semantic Scholar rate-limited the session and no general web search was available, so non-arXiv venues are under-covered.

## 2.1 Memory architectures for agents

Persistent memory for language-model agents is usually built as a store outside the context window that the agent reads through retrieval or tool calls. MemGPT manages memory tiers by analogy with an operating system [@packer2023memgpt]; Mem0 extracts, consolidates and retrieves salient facts across sessions [@chhikara2025mem0]; Zep organises memory as a temporal knowledge graph [@rasmussen2025zep]. MEMOIR adds a training-free lifecycle with judge-gated consolidation [@anand2026memoir]. These systems are background for this study: our harness uses a deliberately simple store (hashed bag-of-words retrieval, top 4) so that the object of study is what happens *after* retrieval.

## 2.2 Staleness, conflict and resolution

**Resolution rather than retrieval.** DISCERN (full text) preserves an immutable event log at write time, derives a bitemporal fact store, and at read time lets the agent navigate with deterministic, LLM-free tools; the committed action (answer, update, abstain or clarify) is a decidable function of the graph, guarded by gates that include an *EarnedAbstainGate* that rejects abstaining without searching [@ahuja2026discern]. Its abstract reports that recall and currency are near-saturated and that resolution is the unsolved part. DISCERN's backbones are large hosted models (the smallest in its backbone comparison is 120B), its facts and validity intervals are LLM-extracted, and its ablations do not perturb extraction or timestamps.

**Provenance and invalidation.** PACMI (full text) propagates invalidation through a provenance graph with a four-state validity lattice and corrects outdated premises by adding old and current facts to the answer prompt, i.e. advisorily [@wang2026pacmi]. AMV-Guard (full text) treats re-verification of a memory premise before a state-changing action as a value-of-information stopping problem, evaluated on ToolSandbox and AppWorld with 27–35B cross-backbone checks [@wang2026amvguard]. Governed Persistent Memory (full text) uses a bitemporal state-transition model with deterministic, fail-closed release and reports that its governed lane outperforms an ungoverned local Qwen2.5-7B [@xu2026gpm]. TOKI formalises contradiction resolution as write-time concurrency control over bitemporal operators [@wang2026toki]. StateWise repairs invalid stored state before agent actions in coding agents [@peng2026statewise]. Security-oriented provenance work (PPMF, MemLineage) binds tool authority or lineage to the source of a memory [@xu2026ppmf; @ouyang2026memlineage]. Zhao et al. observe that outdated memory and poisoning call for opposite write decisions and propose an evidence-conditioned accuracy metric [@zhao2026accept]. Zhou et al. give a theory of when memory reuse is safe [@zhou2026manysteps].

**Benchmarks.** STALE (full text) provides 400 scenarios and 1,200 queries over three dimensions, including state resolution and premise resistance [@chao2026stale]. Its construction excludes explicit invalidation (surface negation, direct correction, explicit obsolescence marking), so it contains none of the lexically signalled cases that Evarb targets; it is the natural external test of what a lexical arbiter cannot do. MemoryAgentBench includes a conflict-resolution competency [@hu2025memoryagentbench]; Pakhomov and Nijkamp show that a frozen last-write rule answers a large share of its conflict split and that some gold answers are unreachable [@pakhomov2026bookkeeping]. LongMemEval and LoCoMo evaluate long-term conversational memory, including knowledge updates and abstention [@wu2024longmemeval; @maharana2024locomo].

**Why models fail on updates.** CICM (full text) studies in-context updates mechanistically. Probes still recover the updated value when the model answers with the old one ("stale binding"). The paper compares an explicit reminder with an internal attention intervention across Qwen2.5 and Llama sizes, and finds that how well models comply with the advisory reminder depends on the model family [@guo2026cicm]. This is the closest prior evidence on whether small models follow advisory signals about which value is current, although the setting is single-answer dialogue rather than an agent with a three-way terminal action.

**Use of memory.** Xu et al. find that delivered memory often does not change agent behaviour on SWE-bench Verified [@xu2026delivered]; Pathirage and Srijomkwan study when models decide to search beyond parametric memory [@pathirage2026confident]. Zhang and Sun issue deterministic answer/search/abstain decisions from sufficiency certificates in retrieval [@zhang2026horn].

## 2.3 Verification and self-correction

Same-model self-correction without external feedback often fails to improve reasoning and can degrade it [@huang2023selfcorrect; @kamoi2024survey]. Retrieval-side critique and correction are studied in Self-RAG and Corrective RAG [@asai2023selfrag; @yan2024crag]. Our LLM-arbiter baselines (LA, LG) use the agent's own model to arbitrate records. They are not self-correction of the answer, but their errors are of the same kind: an unaided small model judging evidence.

## 2.4 Comparison

Table 2.1 summarises the six papers read in full text against the design dimensions of this study. Entries for prior work are taken from `PHASE1/RELATED_WORK_DEEP_DIVE.md` §2 and §4. The last column describes what this study *tests*, not what it finds.

**Table 2.1.** Closest work, by design dimension.

| Dimension | DISCERN | PACMI | AMV-Guard | GPM | STALE / CUPMem | CICM | This study |
|---|---|---|---|---|---|---|---|
| Who makes the terminal decision | deterministic code over an LLM-built graph | LLM with prompt-level correction | decision-theoretic verification gate | deterministic services | LLM; constrained readout | the model (reminder or internal steering) | the agent; policy may send one reversible notice |
| Same information as advisory label vs enforced, compared | no | no | no (vs always/never/static policies) | no (governed vs ungoverned) | not directly | reminder vs routing | yes (T vs RT; EB vs EBG; LA vs LG) |
| Labels state their evidence basis; enforcement gated on it | no (uniform gates) | no | no | no | no | no | **tested** (EBG vs EBG-all) |
| Deterministic vs LLM arbiter under the same policy | no | no | no | no | no | no | **tested** (EBG vs LG) |
| Agents ≤ 14B, open weights | no | no | no | baseline only | partly (Qwen3.5-9B) | yes, not agentic | yes (3B–14B) |
| Cost of a wrong reliability label measured | no | partly | modelled | fail-closed by design | implicit conflicts | no | harmful-answer rates per configuration (S4) |
| Evaluation | ENT-310, LoCoMo | own (100 cases) | ToolSandbox, AppWorld | own, sealed | own, public | own | own, sealed, synthetic (eval3) |

## 2.5 What is new and what is not

**Not new, and not claimed.** The following are established by prior work or are true by construction:

1. Memory improves memory-dependent tasks.
2. Provenance, bitemporal ordering or deterministic gating improve staleness and conflict handling [@ahuja2026discern; @wang2026pacmi; @xu2026gpm; @wang2026toki]. On an existing conflict benchmark, a deterministic last-write rule already does well [@pakhomov2026bookkeeping].
3. Ordering by a stated validity date before the record date. This is standard bitemporal practice, and DISCERN's design.
4. Forcing a search before an abstention or answer. Our search-before-submit rule (R3/P3) is essentially DISCERN's EarnedAbstainGate.
5. Same-model verification without external signal can hurt [@huang2023selfcorrect; @kamoi2024survey].
6. Agents often fail to use delivered memory, and models can bind a stale value while still encoding the update [@xu2026delivered; @guo2026cicm].
7. A staleness or conflict benchmark. eval3 is synthetic, templated and model-annotated; STALE (400 expert-validated scenarios) and DISCERN's ENT-310 (human-vetted) are larger and have human validation, which eval3 lacks.
8. Combining known components into one system is not a contribution in itself.

**What may be defensible.** Among the papers we read, we found none that:

1. **exposes the evidence basis and strength of each resolution to the agent and gates enforcement on that strength,** so that an ordering inferred from record dates or an unreferenced correction is advised rather than enforced, while an explicit referenced correction is enforced. The enforcing systems we read apply their gates uniformly over the structure they build at write time;
2. **measures, on the same small open-weight models, what happens to the answer when the reliability structure is wrong.** We measure both the harm of following wrong labels and the harm of enforcing them; the systems we read decide over a write-time structure and do not report the answer-level cost of errors in that structure;
3. **compares a deterministic arbiter and an LLM arbiter under an identical downstream policy** on agents of 3B–14B, so that arbitration quality and policy are separated.

Whether these design choices are *useful* is the empirical question of this paper, and the answer is [RESULTS PENDING — filled from PHASE3 verified outputs]. The novelty statement is narrow. The temporal rules themselves are standard. What we contribute is the measurement of label-induced and enforcement-induced harm on small agents, and a preregistered test of whether basis-gated enforcement reduces that harm without losing the benefit of enforcement. Because the literature search was limited to arXiv and stopped on 14 November 2026, and because most papers were read at abstract level only, the statement "we found none" should be read as "in the work we examined" [CITATION NEEDED: a broader search of non-arXiv venues (ACL Anthology, OpenReview) and of work posted after 14 Nov 2026 before submission].
