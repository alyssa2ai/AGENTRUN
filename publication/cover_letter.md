# Cover Letter

Dear Program Chairs,

We submit for your consideration the manuscript *"Disentangling Parser
and Data Effects in Tool-Using LLM Fine-Tuning: A Controlled Ablation
on Qwen2.5-7B."*

The manuscript reports a controlled ablation in which the serving-layer
tool-call parser is varied while the fine-tuned adapter and training
data are held fixed, on a fixed 23-task machine-checkable benchmark.
The ablation produces zero net aggregate improvement while changing the
per-task composition of failures, and a subsequent intervention that
adds 11 targeted trajectories recovers all five remaining failures.

We believe the manuscript fits a workshop on agent evaluation, tool
use, or evaluation reliability. The manuscript discloses three
important limitations: N=1 per condition, a 23-task benchmark, and an
iterative development process in which the second adapter's training
data was informed by observed failures of the first. We do not claim
generalization and we do not present the 23/23 result as a
state-of-the-art outcome. The contribution is methodological.

All code, training trajectories, benchmark definitions, and result
artifacts are released.

Sincerely,
Alyssa L
