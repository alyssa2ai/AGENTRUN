# 9. Ablation studies

EBG combines four things: evidence-basis labels shown to the agent, a reversible notice at the terminal action,
**gating** that enforces only strong-strength resolutions, **safe submission** that keeps the pre-notice answer when
the response to a notice is unusable, and **search-before-submit**. The preregistered exploratory contrasts separate
them. Two of the four components carry essentially the whole effect; one is close to inert on success but changes
the failure profile; and one — gating — is a deliberate trade of success for safety rather than a free improvement.

The mechanism-level columns below come from the descriptive metrics over all six models. *Conflict preserved* is the
share of genuinely unresolvable groups the agent still reports as a conflict; *false resolution* is the share it
asserts an ordering for anyway.

| Config | Success (pooled primary) | Harmful | Conflict preserved | False resolution | Unnecessary abstention | Format error |
|---|---|---|---|---|---|---|
| B | 46.0% | 7.0% | 65.2% | 12.8% | 19.5% | 3.2% |
| G | 43.5% | 7.9% | 72.8% | 9.2% | 16.0% | 3.7% |
| T | 46.9% | 7.4% | 79.6% | 3.6% | 16.9% | 3.1% |
| R | 45.0% | 16.1% | 74.2% | 12.3% | 9.4% | 6.1% |
| RT | 44.2% | 22.6% | 66.8% | 19.0% | 11.1% | 6.2% |
| LA | 47.9% | 13.2% | 57.8% | 21.9% | 18.4% | 3.5% |
| LG | 45.4% | 21.3% | 42.4% | **37.0%** | 17.1% | 3.3% |
| EB | 55.3% | 2.7% | 81.6% | 2.0% | 16.7% | 3.1% |
| **EBG** | **61.3%** | **3.1%** | **88.5%** | **1.9%** | 12.8% | 3.3% |
| EBG-all | 71.1% | 6.9% | 77.3% | 12.9% | 13.9% | 3.3% |
| EBG-unsafe | 61.5% | 3.3% | 89.0% | 1.6% | 9.9% | **6.4%** |
| EBG-noR3 | 60.0% | 3.4% | 83.3% | 1.9% | 17.6% | 2.9% |

## 9.1 The labels do most of the work (EB − T = +8.5 pp, EB − G = +11.8 pp)

Replacing metadata-derived labels with evidence-basis labels, with no enforcement at all, raises success by 11.8 pp
over G and 8.5 pp over the temporal annotator T, and cuts the harmful rate from 7.9% and 7.4% to 2.7%. False
resolution falls from 9.2% (G) and 3.6% (T) to 2.0%. Most of the benefit of the mechanism is in *what the agent is
told*, before anything is enforced. This is the part of the result we consider best supported.

## 9.2 Gating adds a real but smaller increment (EBG − EB = +6.0 pp)

Adding the gated notice to the labels adds 6.0 pp [3.9, 8.2] of success with no detectable change in harm
(+0.5 pp [−0.1, 1.2]), lifts conflict preservation from 81.6% to 88.5%, and cuts step-limit failures from 2.0% to
1.0%. The notice mostly recovers runs where the agent had the right labels and still submitted the superseded value.

## 9.3 Search-before-submit is worth about 1.3 pp (EBG vs EBG-noR3)

Removing it costs 1.3 pp of success (61.3% to 60.0%) and raises unnecessary abstention from 12.8% to 17.6%: agents
that do not re-read memory before answering abstain more. Small, cheap, and in the expected direction.

## 9.4 Safe submission buys format robustness, not success (EBG − EBG-unsafe = −0.2 pp, n.s.)

Success is statistically indistinguishable with and without safe submission (−0.2 pp [−1.0, 0.7], p = 0.78), and so
is harm. What it changes is the failure profile: format errors nearly double without it, 3.3% to 6.4% pooled (2.8% to
5.8% on primary models), while unnecessary abstention falls from 12.8% to 9.9%. Without the fallback, a mangled
reply to a notice becomes a format failure; with it, the pre-notice answer stands, which sometimes means an
abstention. We would keep the component for robustness, but the success claim does not rest on it.

## 9.5 Gating versus ungated enforcement: the central trade (EBG − EBG-all = −9.7 pp)

Enforcing *every* arbitration, not only strong-strength ones, scores **9.7 pp higher** than EBG (71.1% against
61.3%; CI [−15.2, −4.3], BH p = 0.0013). It also:

- more than doubles the harmful rate, 3.1% → 6.9% (difference −3.7 pp [−6.6, −1.3] in EBG's favour);
- restores arbitrary picks from 13 to 166 runs;
- raises false resolution from 1.9% to 12.9%, and drops conflict preservation from 88.5% to 77.3%.

This is the clearest answer in the study to the second half of our research question, and it goes against the
mechanism we proposed. **Indiscriminate enforcement does increase harmful answers** — but on this benchmark it also
produces more correct answers than gated enforcement does. Gating is a trade, not a dominance. Which side of it one
should take depends on the relative cost of a wrong confident answer and a missed correct one, which this benchmark
does not price. We state the trade rather than resolve it, and we note two qualifications. The gap is sensitive to
the item set: it is −4.8 pp [−9.7, 0.3], not significant, on the double-agreement subset, and −17.1 pp on the
flagged complement, which suggests part of it lives in items where the annotators themselves disagreed. And success
and harm are not commensurable units: 9.7 pp of success against 3.8 pp of additional harm and a tenfold increase in
arbitrary picks is a judgement, not an arithmetic comparison.

## 9.6 Gating helps only when the arbiter is reliable (LG − LA = −2.4 pp, harm +8.1 pp)

The same gating machinery, driven by an LLM arbiter instead of the deterministic one, does not help: success is
statistically unchanged (−2.4 pp [−5.6, 0.6], p = 0.167) and harm rises by 8.1 pp [6.1, 10.2]. Under LG, false
resolution reaches 37.0% and conflict preservation falls to 42.4% — the worst of any configuration, worse than no
mechanism at all. For Qwen2.5-7B the LLM arbiter's gated variant falsely resolves 75.9% of genuine conflicts.

The useful generalisation is therefore not "enforcement helps" and not "gating helps", but that enforcement inherits
the reliability of whatever supplies its labels. Enforcing a deterministic, evidence-grounded arbiter's strong
resolutions helps; enforcing a record-metadata scanner's (RT) or a language model's (LG) is actively harmful. The
value of the evidence-basis idea is that it gives enforcement something defensible to enforce, and a principled
place to stop.
