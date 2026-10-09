# Reference Verification Report

Date of checks: 9–10 October 2026. Bibliography: `overleaf/references.bib`.
Style: `splncs04` (Springer, alphabetical numbering).

## Summary

- 29 entries. All 29 are cited in `main.tex`, and every citation key resolves (checked by script).
- BibTeX ran with 0 warnings. LaTeX reports no undefined citations.
- Every title, author list, year and venue was checked against at least one primary or authoritative source (table below). No DOI was typed from memory; each one came from Crossref or arXiv.
- For author lists longer than about 7 names, the first 6–7 authors are given, followed by "and others" (rendered "et al.").

## Sources used

- **arXiv abstract pages** (`arxiv.org/abs/<id>`): title, full author list, submission date, DataCite DOI and author comments. The arXiv API and the Semantic Scholar API were rate-limited (HTTP 429), so the abstract pages were read directly.
- **Crossref** (`api.crossref.org`): published versions with DOIs, including ACL Anthology, NeurIPS proceedings (DOI prefix 10.52202), ACM, PNAS and Science.
- **ICLR**: the official listings at `iclr.cc/virtual/2022|2023/papers.html` and `proceedings.iclr.cc/paper_files/paper/2024`. OpenReview requires an interactive browser check, which was not completed; no OpenReview page was used.
- **TMLR**: the accepted-papers listing at `jmlr.org/tmlr/papers/`, which shows month and year.
- **MLSys**: `proceedings.mlsys.org/paper_files/paper/2021`.
- **DBLP**: refused connections and was not used.

## Per-entry verification

| Key | Published venue verified via | Identifier |
|---|---|---|
| yao2023react | ICLR 2023 virtual listing; arXiv comment "ICLR camera ready" | arXiv:2210.03629 |
| schick2023toolformer | Crossref (NeurIPS 36, pp. 68539–68551) | 10.52202/075280-2997 |
| patil2024gorilla | Crossref (NeurIPS 37, pp. 126544–126565) | 10.52202/079017-4020 |
| qin2024toolllm | ICLR 2024 proceedings listing | arXiv:2307.16789 |
| li2023apibank | Crossref / ACL Anthology (EMNLP 2023, pp. 3102–3116) | 10.18653/v1/2023.emnlp-main.187 |
| mialon2023alm | TMLR listing (July 2023) | arXiv:2302.07842 |
| mcp2025spec | Specification page returned HTTP 200 with title "Specification - Model Context Protocol"; 2025-03-26 is the protocol version in the `mcp==1.9.4` package used by AGENTRUN | URL |
| liu2024agentbench | ICLR 2024 proceedings listing; abstract confirms "8 distinct environments" | arXiv:2308.03688 |
| zhou2024webarena | ICLR 2024 proceedings listing | arXiv:2307.13854 |
| yao2024taubench | arXiv only (not found in the ICLR 2025 listing) | 10.48550/arXiv.2406.12045 |
| kapoor2025agents | TMLR listing (June 2025) | arXiv:2407.01502 |
| hu2022lora | ICLR 2022 virtual listing | arXiv:2106.09685 |
| dettmers2023qlora | Crossref (NeurIPS 36, pp. 10088–10115) | 10.52202/075280-0441 |
| biderman2024loraforgets | TMLR listing (August 2024) | arXiv:2405.09673 |
| kirkpatrick2017ewc | Crossref (PNAS 114(13):3521–3526) | 10.1073/pnas.1611835114 |
| chen2023fireact | arXiv only (no published version found) | 10.48550/arXiv.2310.05915 |
| zeng2024agenttuning | Crossref / ACL Anthology (Findings ACL 2024, pp. 3053–3077) | 10.18653/v1/2024.findings-acl.181 |
| qwen2024qwen25 | arXiv (technical report) | 10.48550/arXiv.2412.15115 |
| liang2023helm | TMLR listing; arXiv journal-ref "TMLR, 2023" | arXiv:2211.09110 |
| biderman2024lessons | arXiv only | 10.48550/arXiv.2405.14782 |
| sclar2024formatting | ICLR 2024 proceedings listing | arXiv:2310.11324 |
| tam2024speakfreely | Crossref / ACL Anthology (EMNLP 2024 Industry, pp. 1218–1236) | 10.18653/v1/2024.emnlp-industry.91 |
| dodge2019showyourwork | Crossref / ACL Anthology (EMNLP-IJCNLP 2019, pp. 2185–2194) | 10.18653/v1/D19-1224 |
| bouthillier2021variance | MLSys 2021 proceedings listing | arXiv:2103.03098 |
| lipton2019troubling | Crossref (ACM Queue 17(1):45–77) | 10.1145/3317287.3328534 |
| dwork2015reusable | Crossref (Science 349(6248):636–638) | 10.1126/science.aaa9375 |
| zhou2023cheater | arXiv only | 10.48550/arXiv.2311.01964 |
| l2026agentrunpreprint | Zenodo API record 22346935 (preprint, 2026-09-05, CC BY 4.0) | 10.5281/zenodo.22346935 |
| l2026agentrunrepo | GitHub; commit a4a6976 is on `main` of alyssa2ai/AGENTRUN | URL |

## Corrections made relative to earlier drafts

- **Toolformer** now has nine authors. The published NeurIPS version adds Eric Hambro, who is not on the arXiv listing. The previous manuscript and the preprint followed arXiv.
- **"Let Me Speak Freely?"** now uses the published EMNLP Industry title ("…on Large Language Model Performance"), which differs from the arXiv title.
- **AgentBench** is described as evaluating **eight** environments, as its abstract states. The previous manuscript said 11.
- **Gorilla** is cited as NeurIPS 2024, its published venue (verified via Crossref), not as an arXiv preprint.
- **MLSys volume number** was removed from Bouthillier et al. because it could not be verified.
- **Paraphrase fixes.** Each claim about a cited work was compared with its abstract:
  - **Kapoor et al.:** the paraphrase now follows their four stated points.
  - **Dodge et al.:** the paraphrase now follows their actual claim, that test scores alone are insufficient.

## Unresolved or to-review items

- `yao2024taubench`, `chen2023fireact`, `biderman2024lessons` and `zhou2023cheater` are cited as arXiv preprints. A peer-reviewed version may exist, but none was found with the sources above. Check once more before the camera-ready.
- ICLR 2022/2023 venue facts rest on the iclr.cc virtual listings plus arXiv comments; no DOIs exist for these.
- `mcp2025spec` is a web specification with no DOI or archival identifier.
- Springer's instructions mention a bibliography style called "MathPhySci", but the ANTIC- and Springer-supplied templates both ship `splncs04.bst`, which is used here. See the rules checklist.
