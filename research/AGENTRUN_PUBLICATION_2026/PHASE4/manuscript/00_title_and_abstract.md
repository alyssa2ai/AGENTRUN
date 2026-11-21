# Evidence-Basis Arbitration for Conflicting Persistent Memory in Small Tool-Using Agents: A Preregistered Evaluation of Gated Enforcement

## Abstract

Agents with persistent memory must act on records that contradict each other, and the usual remedy — attaching
reliability labels derived from record metadata and enforcing them at the terminal action — can make small models
worse rather than better. We ask whether arbitration that reports the *evidence basis* for each resolution, and
enforces only resolutions that basis supports, improves reliability, and whether enforcing resolutions
indiscriminately increases harmful answers.

We evaluate Evarb-0.2, a deterministic arbiter that assigns each record a status, an explicit evidence basis and a
strength, shows those labels to the agent, and at the terminal action issues one reversible notice but enforces only
strong-strength resolutions. The mechanism, the analysis and the hypotheses were frozen and preregistered before the
confirmatory data existed. The confirmatory campaign ran 18 model × decoding cells over 12 configurations on 268
sealed tasks in 135 families — 57,888 agent runs, with no missing pair, duplicate or harness error — using four
primary open-weight models from two families (3B–8B) and two secondary models, under family-clustered sign-flip
permutation inference with Holm correction.

All four preregistered contrasts are supported. Gated evidence-basis arbitration raised task success over enforced
record-and-temporal labels by 17.1 pp (95% CI [12.2, 22.1], Holm p = 4 × 10⁻⁵), over advisory temporal labels by
14.5 pp, over an LLM arbiter under the same gated policy by 15.9 pp, and over unlabelled memory by 15.3 pp. The
harmful-answer rate fell from 22.6% to 3.1% and arbitrary picks from 252 runs to 13. Ablations locate most of the
benefit in the labels themselves (+11.8 pp without any enforcement) rather than in enforcement (+6.0 pp), and the
development finding that metadata labels *hurt* small agents replicates on sealed data.

Two results qualify the contribution. Enforcing every arbitration rather than only strong ones scored 9.7 pp
*higher* than the gated mechanism while more than doubling harm and raising false resolution from 1.9% to 12.9%:
gating trades accuracy for safety rather than dominating. And the same gating machinery driven by an LLM arbiter
gave no success gain and 8.1 pp more harm, indicating that enforcement inherits the reliability of whatever supplies
its labels. Effects also differ by model family: the Llama models gain by converting abstentions into answers rather
than harmful answers into correct ones. We report the preregistered outcome, the exploratory trade that cuts against
our own design, and an unplanned mid-campaign platform transition affecting 1.69% of rows, whose removal moves the
pooled estimates by at most 0.1 pp.
