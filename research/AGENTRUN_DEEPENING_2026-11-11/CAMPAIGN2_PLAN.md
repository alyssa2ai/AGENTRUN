# Campaign 2 (12 November 2026): audit of the first study and what was run next

Written before the campaign-2 results existed. The evaluation split and harness variants were frozen at 2026-11-12 04:54 UTC (`benchmark/FREEZE_eval2.json`); Slurm array 4148 was submitted after that.

## Audit of the first study: weaknesses worth fixing

| # | Weakness | Why it matters | What campaign 2 does about it |
|---|---|---|---|
| 1 | 48 tasks, 8 per scenario; scenario-level cells are too small to interpret | The interesting effects (stale, conflict, unsupported) live at scenario level | New split **eval2**: 96 tasks, 16 per scenario, new names, same generator |
| 2 | The findings were seen once, on one split | A result that does not replicate on fresh tasks is not a result | Re-run the frozen v1 harness on eval2 as a **replication** |
| 3 | Three failure modes were found but nothing was tried against them (answer in the wrong format; memory not consulted; cannot stop searching) | "We found problems" is weaker than "we found problems and measured a fix" | Harness **v1r** (one repair turn) and **v2** (v1r plus two prompt rules), compared with v1 on the same fresh tasks |
| 4 | The claim "reliability machinery matters less for stronger models" compared local 7-8B models with hosted models on a different backend | Confounded by backend, tool-call parser and reasoning mode | **Size sweep inside one family and one backend**: Qwen2.5 1.5B, 3B, 7B, 14B on the L40 |
| 5 | The retriever was shown to fail at scale only in a retrieval-only test | No evidence that it changes what the agent answers | **End-to-end**: every memory store padded with 2,000 background records; hash256 vs BM25 vs bge-small inside the agent loop |
| 6 | The project's own benchmark was never re-run with a matched client, with traces, on a frozen environment | This is the open question from the fine-tuning study (the E4 confound) | **Legacy 23 tasks and the 55-task v2 dev split**, base vs repository adapter, budgets 3 and 6, through the repository's own v2 runner and scorers; three sampled repeats on the legacy tasks |
| 7 | One greedy trial per model | No estimate of run-to-run spread for the new harness | Two sampled repeats (T = 0.7) of the v2 harness on Qwen2.5-7B |

Not addressed (out of reach today): free-text memories without keys, agent-written memories, a deliberately wrong memory, a second model family, more than one verifier model.

## Why a new split and not the old one

The v1r and v2 changes were designed after reading failures on the first eval split. Testing them on those same 48 tasks would be tuning on the test set. So:

- the first eval split stays reserved for the frozen v1 harness;
- v2 was checked on the 12 dev tasks only (job 4145), with no revision afterwards;
- eval2 was generated from a new seed with names from a third, disjoint slice of the name pool, and frozen before any eval2 run;
- v1 is re-run on eval2, so every v1r/v2 comparison is paired on identical tasks.

The 23 legacy tasks and the v2 dev split are not gated by `docs/research_protocol_v1.md` (only the sealed test split is). The sealed test split was not used and was not copied to the cluster.

## The harness variants

| Variant | System prompt | Repair turn |
|---|---|---|
| v1 | frozen 2026-11-11 | no |
| v1r | same as v1 | if the final message is not a parsable answer, one fixed notice asks for a `submit_answer` call |
| v2 | v1 plus rule 6 ("search memory before deciding a fact is unavailable or giving up on a failing tool") and rule 7 ("never repeat a call that returned a valid result; if neither memory nor the registry has the fact, abstain") | yes |

## Questions campaign 2 can answer

1. Do the first study's orderings (B > A, C < B, D > C, E >= D on small models) replicate on 96 fresh tasks?
2. How much of the lost performance is recovered by a repair turn alone, and by the two prompt rules?
3. Does the value of provenance and of the reliability gate shrink with model size inside one family?
4. Does swapping the retriever change end-task success once the store has 2,000 records?
5. On AGENTRUN's own 23 tasks, with a matched client and a frozen environment, how do the base model and the adapter compare, and how much do repeated runs vary?

## Jobs

`hpc/campaign2.sbatch`, array 4148, indices 0 to 20, two at a time, in priority order. Results will be reported in RESULTS_CAMPAIGN2.md with complete and incomplete runs listed separately.
