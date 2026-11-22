# Publication roadmap

**13 November 2026.** No venue deadlines are given here, because none were verified in this session. Check each venue's current call before choosing.

## Two papers, kept separate

| | Paper A: fine-tuning and evaluation validity (thread 1) | Paper B: memory reliability across capacity (thread 2) |
|---|---|---|
| State | Submission package in `publication/antic2026_submission/` (ANTIC 2026) | No draft. Evidence is exploratory (eval2 only) |
| Core evidence | 23-task diagnostic, benchmark v2 dev, client-matched base-versus-adapter re-runs in Campaign 2, trace audit | Campaign 2: 5,184 agent runs; Campaign 1 as pilot |
| Ready to draft? | Already drafted (not re-audited in this session) | **Methods, related work and exploratory results: yes. Confirmatory claims: no.** Needs E0, E1 and at least one of E2/E4 |
| What it must not claim | The 23-task 100% as generalisation | Novel provenance or gate method; a staleness benchmark of record |

**Whether to merge them.** Not recommended (see `RESEARCH_CONTRIBUTION.md`). Paper B may cite Paper A for the evaluation-client lesson, nothing more.

## Paper B: steps

1. **Close the blockers that need no GPU** (can start now):
   - read the full texts of DISCERN, PACMI, AMV-Guard, GPM, STALE and CICM, and update `RELATED_WORK_AND_NOVELTY.md`;
   - scorer validation (E6);
   - write the eval3 generator change (held-out templates) and the pre-registration document.
2. **Draft the exploratory sections** from eval2:
   - setup;
   - per-scenario results;
   - family-level inference;
   - the negative findings (verifier harm, unused memory at 1.5B, S5 harm, 14B regressions).
   
   Label every eval2 number "validation set".
3. **When Slurm returns:**
   - run E0 (jobs 14–20);
   - freeze and seal eval3;
   - run the confirmatory grid on eval3: 5 models plus the second family, A–E, greedy plus 3 seeds;
   - run E3 and E4.
4. **Decide the venue by outcome:**
   - H1–H5 confirmed with a second family and an external benchmark → a main-conference empirical track or Findings;
   - confirmed only on memlab → an agents or memory workshop;
   - not confirmed → a short negative-results or reproducibility paper, still worth writing.
5. **Release.** Code, frozen splits (eval2 now; eval3 after the paper), raw runs and the analysis scripts. The previous `PROJECT_AUDIT.md` flagged leaked keys in git history: rotate them before making anything public.

## Paper A: steps (not audited here)

- The ANTIC package was outside this session's scope. Before submission, re-check it against `CORRECTIONS.md` item 8 (the 100% result is evaluation adaptation) and item 10 (the repository adapter is V2, not V1).
- If the package is to be confirmatory, the sealed 130-task benchmark-v2 test set is its confirmatory set. Move `.sealed/` out of the repository first.
