# 12. Discussion

## 12.1 What the study shows

The research question was whether evidence-basis-aware arbitration improves persistent-memory reliability for small
tool-using agents, and whether indiscriminate enforcement can increase harmful answers. Both halves now have an
answer, and they do not point the same way.

On the first half, the preregistered comparison is unambiguous within its scope. The full mechanism beat enforced
record-and-temporal labels by 17.1 pp of task success, advisory temporal labels by 14.5 pp, an LLM arbiter under the
same gated policy by 15.9 pp, and unlabelled memory by 15.3 pp, with every interval well clear of zero after Holm
correction, in the same direction for all six models, and stable across three item-set definitions. Harm fell with
it: 3.1% of EBG runs were harmful against 22.6% under RT, and arbitrary picks fell from 252 to 13.

On the second half, the answer is yes — and it cuts against our own design. Enforcing every arbitration rather than
only strong-strength ones raised false resolution from 1.9% to 12.9%, restored arbitrary picks from 13 to 166, and
more than doubled the harmful rate. It also scored 9.7 pp *higher* on task success. Gating buys safety with
accuracy; it does not dominate.

## 12.2 The mechanism that actually carries the effect

The ablations locate the benefit more precisely than the headline contrasts do. Most of it is in the labels: giving
the agent evidence-basis statuses with no enforcement at all (EB) is worth +11.8 pp over metadata labels and
+8.5 pp over advisory temporal labels, and cuts harm from ~7.5% to 2.7%. Gating adds a further +6.0 pp. Safe
submission adds nothing measurable to success (−0.2 pp, p = 0.78) while halving format errors, and
search-before-submit adds 1.3 pp.

The LG − LA contrast tells us why this ordering matters. The same gating machinery driven by an LLM arbiter produced
no success gain and 8.1 pp *more* harm, with 37.0% false resolution. Enforcement inherits the reliability of
whatever supplies its labels. Enforcing a record-metadata scanner's labels (RT) tripled harm relative to plain
memory; enforcing a language model's (LG) tripled it too; enforcing a deterministic arbiter's strong, evidence-cited
resolutions did not. The contribution is best stated as: *the evidence basis is what makes enforcement safe to apply
and tells you where to stop applying it* — not that gating or enforcement is good in itself.

## 12.3 The label-harm finding replicates

The study began with a development observation: metadata-derived reliability labels made small agents worse than no
labels, because the agents followed the label instead of the text. On sealed confirmatory data this replicates
without modification. G scored 43.5% against B's 46.0%, with more harm (7.9% vs 7.0%) and more false conflicts
(31.4% vs 26.4%). Enforcing those labels (RT) made it worse again: 44.2% success and 22.6% harm. A reliability
signal that the evidence does not support is not merely useless to a small agent; it is actively misleading, and
enforcement amplifies it.

## 12.4 Where it does not generalise

Model family matters more than model size for *how* the mechanism helps. For the three Qwen models the story is the
one the hypotheses describe: harmful answers become correct ones, with harm differences of −24.5 to −27.7 pp. For
Llama-3.1-8B it is not: that model abstains on 44% of EBG runs and fails to format an answer on 11%, is the least
harmful model in the study under every configuration, and gains its +6.8 pp over RT by converting abstentions into
answers. Its harm difference is −0.3 pp, because there was almost no harm to remove. The preregistration anticipated
this risk from the development split, where Llama showed +1.1 pp; eval3 gives a small positive effect whose interval
excludes zero, which is better than the development data suggested but is not the same effect as the one measured on
Qwen. We do not claim universal superiority across families.

Nor is the absolute picture good. The best configuration answers 61.3% of tasks correctly and 46.0% of the tasks
that have a definite answer. Llama-3.2-3B, which failed the readiness criterion before the campaign, remains near
the floor. These are small models on synthetic, template-regular, English, ISO-dated records in one harness. Nothing
here speaks to frontier models, to natural memory logs, or to conflicts without lexical cues.

## 12.5 Development evidence, exploratory results and confirmatory results

Three kinds of evidence appear in this paper and should not be read alike. The Phase 1 pilot numbers in Section 1
and the p2val2 observations in Section 4.10 are **development evidence**: they motivated the design and the
hypotheses and are not tests of them. The four Holm-corrected contrasts and S4 are **confirmatory**: preregistered,
frozen before the data existed, and reported here with whatever sign they came out. Everything in Section 9, the
three item-set sensitivity analyses, and the two platform sensitivity analyses in Section 8.4 are **exploratory**;
the last two are additionally post-hoc, specified after the platform transition came to light. We draw no
confirmatory conclusion from any of them, including the EBG − EBG-all trade that we consider the most interesting
result in the paper.

## 12.6 How much the deviations limit the conclusions

Three execution facts constrain what can be claimed, and we weigh them explicitly rather than listing them.

**The platform transition (Section 11).** 980 of 57,888 rows (1.69%), in two of eighteen cells, were produced after
the host kernel and NVIDIA driver changed. Because the runner's loop order makes a resumed segment carry all twelve
configurations for every whole task it contains, the transition is balanced across configurations to within one row,
and dropping the affected cell entirely moves the pooled estimates by at most 0.1 pp. The residual confound is two
tasks out of 268 whose own rows are split across platforms. We judge this a disclosure, not a threat to the primary
conclusions — but the honest statement of its limit is that we cannot demonstrate the driver change was inert,
because no task and configuration was run on both platforms.

**The two affected configurations.** One is a single T = 0.7 seed of one primary model, contributing a quarter of
one of sixteen primary cells; the other is the format-limited secondary cell that is never pooled. Neither carries a
confirmatory claim on its own.

**Qwen3-8B re-seeding.** The resumed cell restarted its sampling stream rather than continuing it. This does not
bias the sampling distribution, since the design fixes the seeds and makes no claim about stream continuity, but it
means that one cell cannot be reproduced byte for byte without reproducing the interruption.

Taken together these limit *reproducibility* of two cells and leave one unanswerable question about driver effects;
they do not reach the preregistered contrasts, which are stable to removing the affected data entirely.

## 12.7 What would change our mind

Four results would undermine the contribution as stated. A replication in which evidence-basis labels without
enforcement (EB) did not beat metadata labels would remove the part of the effect we consider best supported. A
benchmark that prices wrong confident answers against missed correct ones, on which ungated enforcement came out
ahead overall, would make gating the wrong default rather than a defensible one. A model family on which EBG lowered
success would bound the claim further than Llama-3.1-8B already does. And a transcript study showing that EBG's
remaining 20.2% false conflicts are items the arbiter *could* have resolved from the text would move the mechanism's
known limitations from a documented residue to a design flaw.
