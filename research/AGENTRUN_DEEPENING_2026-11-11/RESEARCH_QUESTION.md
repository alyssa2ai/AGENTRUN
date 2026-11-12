# Research question and hypotheses

## Question

How much does persistent memory, and then verification, provenance and a deterministic reliability check on top of it, change the **reliability** of a multi-tool LLM agent, compared with a stateless agent, when earlier context is lost, when retrieved records are stale or contradictory, when the evidence is missing, and when a tool fails?

Reliability is split into two quantities that are never merged:

- **Task success**: the agent did the expected thing (gave the right value, abstained when the evidence was missing, or flagged a conflict when the evidence was contradictory).
- **Harmful assertion**: the agent stated a value that was wrong, outdated, unsupported, or an arbitrary pick between conflicting records. Abstaining when an answer was available is a miss, not a harmful assertion.

## Hypotheses (fixed before the evaluation run)

| | Hypothesis | Test | Would be rejected if |
|---|---|---|---|
| H1 | Persistent memory raises task success when the needed facts are not in the conversation. | B vs A on S1 (context loss) and overall, paired | B is not above A |
| H2 | A verification pass lowers harmful assertions when retrieval returns misleading records. | C vs B on harmful-assertion rate, paired; verifier precision and recall | C does not lower the rate, or the verifier rejects mostly correct drafts |
| H3 | Exposing provenance (record id, date, source) improves handling of stale and conflicting records. | D vs C on S3 and S4, especially the S4 tasks whose date exists only in metadata | D is not above C there |
| H4 | The combined system is more reliable than any single component. | E and D vs B and A on both quantities | the full system is no better than retrieval alone |
| H5 | The added components cost latency, tokens and model calls, and can add their own errors (over-abstention, false conflicts). | efficiency table; safe-miss counts | no measurable cost |

A hypothesis that fails is reported as failed.

## Configurations

| | Memory | Retrieval | Verification | Provenance | Deterministic reliability check |
|---|---|---|---|---|---|
| A stateless baseline | no | no | no | no | no |
| B retrieval | yes | yes | no | no | no |
| C verified retrieval | yes | yes | yes | no | no |
| D + provenance | yes | yes | yes | yes | no |
| E + reliability gate | yes | yes | yes | yes | yes |

A to D are the four configurations requested. E was added because D leaves the comparison of dates and values to the language model; E computes it in code, which separates "the model was shown the provenance" from "the system used the provenance".

## What this study does not ask

- Whether fine-tuning for memory use helps. The repository adapter was run as one of the models, but it was trained for a different tool set, so its results describe transfer, not a memory-trained model.
- Whether memory *writing* is reliable. Records are written by the harness, not by the agent.
- Whether the result holds for natural, unstructured memories. The fixtures are single-sentence facts with clean entity and attribute keys.
