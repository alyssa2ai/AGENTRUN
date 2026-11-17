# STALE: integration assessment

**14 November 2026.**

**Decision.** STALE is **ruled out as an evaluation benchmark for the evarb mechanism**. No STALE tasks were run and no STALE result is claimed. The reasons below come from the paper's full text and the official dataset card.

## 1. Source, version, access, licence (verified)

| Item | Value |
|---|---|
| Paper | Chao et al., "STALE: Can LLM Agents Know When Their Memories Are No Longer Valid?", arXiv 2605.06527 (7 May 2026), CC BY 4.0 |
| Code | `github.com/icedreamc/STALE`, linked from the paper's full text ("benchmark construction and evaluation code, and the implementation of CUPMem in anonymized form") |
| Data | `huggingface.co/datasets/STALEproj/STALE`: one `train` split, 400 rows, JSON, **CC BY 4.0**, ungated |
| Version | No release tag was visible on the dataset card. Any use must pin the dataset commit hash |

## 2. Task structure (dataset viewer and paper §3)

**Each row:**
- `uid`, `type` (T1 / T2);
- `M_old`, an earlier user utterance, for example "I've been based in Seattle for the last few years.";
- `M_new`, a later one, for example "…settling into my new place in Austin…";
- `explanation` (the latent state change);
- `probing_queries` (dim1 State Resolution, dim2 Premise Resistance, dim3 Implicit Policy Adaptation);
- `relevant_session_index`;
- 50 `timestamps`;
- a 50-session `haystack_session` dialogue (contexts up to 150K tokens).

**Scoring** is by an LLM judge (Gemini-3.1-flash-lite) against the latent-state logic, not against reference strings.

## 3. Does STALE test this mechanism? No.

1. **No explicit evidence by construction.** STALE's Axiom 2 (§3.2) requires that no utterance "explicitly negates, corrects, or marks the obsolescence" of the old value. evarb's contribution is precisely the reading of explicit evidence: corrections, negated corrections, retention, reported or hypothetical changes, validity dates. On STALE, evarb's text rules can only stay silent, which is the correct behaviour there.
2. **Metadata is never insufficient.** `M_new` always has a later session timestamp than `M_old`. Record-time ordering is already correct, so the legacy gate, TEA and evarb would all give the same order. The STALE difficulty is *recognising that `M_new` updates the same latent attribute* (implicit co-reference), which is an extraction problem.
3. **No structured records.** STALE is dialogue. Running any of our arbiters needs an `(entity, attribute, value)` extractor in front of it, and that extractor, not the arbiter, would determine the result.
4. **Scoring needs an external API judge** (Gemini). That is a dependency and a cost outside this project's infrastructure, and the judge's own error rate would need validating.

## 4. What STALE could still contribute (not done; requires approval)

- **A false-trigger test.** Run `evarb.cues.analyse` on the 800 `M_old` / `M_new` sentences, which were written independently of this project. Count how often a correction, supersession, dismissal or negation cue fires on natural user language that, by Axiom 2, contains none.
  - This is cheap (CPU only, seconds) and is a real test of the cue lexicon's precision on independent text.
  - It needs the 400 rows to be fetched from Hugging Face (CC BY 4.0, under 1K rows). That is a download, so it was not done without the user's go-ahead.
- **An exploratory Phase 3 add-on, not part of the confirmatory plan:**
  - an oracle-extraction STALE subset, mapping `M_old` / `M_new` to two records of one attribute with their session timestamps;
  - checking that EBG does not falsely resolve or falsely enforce on implicit conflicts;
  - this measures safety, not benefit.

## 5. What would change this decision

A STALE-like benchmark whose memories carry explicit corrections, retractions and validity statements with imperfect metadata, in other words the setting eval3 constructs, would be a fair external test. None was found in the Phase 1 literature review (`PHASE1/RELATED_WORK_DEEP_DIVE.md`). That review's limitation remains: only arXiv was searched.
