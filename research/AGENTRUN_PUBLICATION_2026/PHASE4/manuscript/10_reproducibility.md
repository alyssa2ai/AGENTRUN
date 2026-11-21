# 10 Reproducibility and artifact availability

**Implementation.** The agent harness (`memlab`), the evidence-basis arbiter and policy (`evarb`, version 0.2), the comparison mechanisms (RCS for R/RT, TEA for T, and the LLM arbiter for LA/LG), the runner (`run_p2.py`) and the analysis (`analyze_p2.py`) are Python. Models run locally through Hugging Face Transformers 5.22.2 and PyTorch 2.15.0 (CUDA 13.2), in bfloat16, with at most 700 new tokens per call and chat templates with thinking disabled where the model supports it. Each of the 18 cells ran as a Slurm job on one NVIDIA L40. Cell-level provenance is recorded in a manifest line written at every start: model snapshot, decoding, seed, the SHA-256 of every mechanism and harness file, library versions, GPU and Slurm job id.

**Frozen materials.** Every Phase 3 job refused to start unless:
- the evarb-0.2 files matched `FREEZE_evarb.json`;
- the sealed eval3 directory passed `sha256sum -c`;
- the preregistration's SHA-256 matched the value recorded at the freeze (`221013b3…`).

The runner also refused any task file whose hash differed from the sealed one.

**Analysis.** All reported numbers are produced by one command from the raw run files:
- the frozen analysis, with 100,000 seeded permutations and seeded family bootstraps;
- an independent re-computation of the per-configuration counts and the four primary effect sizes, which must agree exactly;
- a report generator that adds no statistics.

The entire pipeline, including the integrity gates, ran without manual steps as a CPU-only Slurm job after the last cell finished. On the shareable development split (p2val2), the same pipeline reproduces its outputs byte for byte.

**Availability.**
- Code, frozen manifests, the preregistration, the development splits and their runs, all aggregate Phase 3 results (JSON/CSV) and the reproducibility package (`PHASE4/reproducibility/`: environment, model snapshots, Slurm scripts, analysis instructions, SHA-256 manifests) are released with the repository.
- The confirmatory eval3 items, their annotations and the per-run transcripts are withheld until publication, so that the test set remains uncontaminated. Their hashes are public in `FREEZE_eval3.json`, so a later release can be checked against the frozen versions.
- Model weights are not redistributed; the exact Hugging Face snapshots are listed in `PHASE4/reproducibility/MODELS.md`.
