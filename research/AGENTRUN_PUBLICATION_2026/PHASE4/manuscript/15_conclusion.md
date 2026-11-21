# 15. Conclusion and future work

Small tool-using agents with persistent memory fail in a particular way when their records disagree: they follow a
reliability label instead of the text, and enforcing that label at the terminal action makes the failure worse. This
paper tested a specific alternative — arbitration that states the *evidence basis* for each resolution and enforces
only what that basis supports — under a preregistration frozen before the confirmatory data existed.

The preregistered result is positive and stable. Across 57,888 runs on 268 sealed tasks, gated evidence-basis
arbitration beat enforced record-and-temporal labels by 17.1 pp of task success, advisory temporal labels by
14.5 pp, an LLM arbiter under the same policy by 15.9 pp, and unlabelled memory by 15.3 pp, all Holm-corrected, in
the same direction for all six models and stable across three item-set definitions. Harmful answers fell from 22.6%
to 3.1%, and the false-resolution rate on genuinely unresolvable groups fell from 19.0% to 1.9%.

Three findings qualify what that means. Most of the gain is in the labels, not the enforcement: evidence-basis
labels alone are worth 11.8 pp over metadata labels, with gating adding 6.0 pp. Ungated enforcement of the same
labels scores 9.7 pp higher still, while doubling harm and restoring the arbitrary picks the mechanism was built to
prevent — so gating trades accuracy for safety rather than dominating, and this benchmark does not price that trade.
And the same gating driven by an LLM arbiter produced no gain and more harm, which suggests the general lesson is
not about gating but about what enforcement is allowed to enforce.

The best configuration still answers only 61.3% of tasks correctly, and its residual failure is over-conservatism:
20.2% false conflicts and 11.5% unnecessary abstentions, against 3.1% harm. The mechanism moved errors where it was
designed to move them. Whether that is the right place for them is a deployment judgement this study does not make.

**Future work.** Four directions follow directly. (1) A benchmark that assigns explicit costs to a wrong confident
answer and to a missed correct one, so the gating trade in Section 9.5 can be decided rather than described.
(2) Extending the arbiter beyond lexical English cues and ISO value dates, where its documented limitations —
long-range negation, "correcting" as a correction cue, `negated_both_stand` — currently live. (3) A transcript study
of EBG's remaining false conflicts, to separate items the arbiter could have resolved from items where abstaining is
correct; this needs the eval3 release. (4) Model-family coverage: the Llama results show the mechanism helping
through a different route, and a family whose dominant failure is abstention needs a different evaluation of what
"reliability" means.

Two methodological artefacts also come out of the campaign rather than the results. Run manifests should record the
host kernel, GPU driver and boot identifier, not only the framework versions: in this campaign a mid-campaign
platform change was visible only as a 0.2 GiB difference in a telemetry field. And an integrity gate should separate
what identifies a run from what merely observes its host, fail closed on anything unclassified, and report the
difference it is willing to tolerate. Both changes are implemented and tested in the released code.
