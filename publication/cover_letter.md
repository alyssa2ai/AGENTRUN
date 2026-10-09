# Cover Letter (draft, venue-neutral)

> Draft for a possible future submission. It has not been sent anywhere.
> The WI-IAT submission was withdrawn on 2026-10-09.

Dear Program Chairs,

We submit for your consideration the manuscript *"Disentangling Parser
and Data Effects in Tool-Using LLM Fine-Tuning: A Controlled Ablation
on Qwen2.5-7B"* (subtitle revised to *"A Case Study on Qwen2.5-7B"*).

The manuscript reports an adapter-fixed ablation on a fixed 23-task
machine-checkable benchmark. In it, the serving-layer tool-call parser was
changed and, as an artifact audit later showed, so was the evaluation
client. The aggregate score did not change, but four per-task outcomes
flipped. A subsequent failure-informed intervention that adds 11 targeted
trajectories recovers all five remaining failures.

We believe the manuscript fits a workshop on agent evaluation, tool
use, or evaluation reliability. The manuscript discloses its main
limitations: N=1 per condition, a 23-task benchmark, an evaluation-client
change within the E4 ablation, and an iterative development process in which the second adapter's training
data was informed by observed failures of the first. We do not claim
generalization and we do not present the 23/23 result as a
state-of-the-art outcome. The contribution is methodological.

All code, training trajectories, benchmark definitions, and result
artifacts are released.

Sincerely,
Alyssa L
