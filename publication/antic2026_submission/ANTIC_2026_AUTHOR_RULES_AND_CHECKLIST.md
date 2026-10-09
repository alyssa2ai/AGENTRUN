# ANTIC 2026 — Author Rules and Compliance Checklist

Prepared on 9–10 October 2026 from the official sources listed below. Each
requirement is labelled as one of:

- **Mandatory**: stated as required by ANTIC or Springer.
- **Recommended**: encouraged by the source but not required.
- **Administrative**: process or fee information.

Each requirement also has a compliance status for this package:

- ✅ complies
- ❌ does not comply
- ⚠️ needs the author's input or is uncertain
- ⛔ unresolved; the public sources do not settle it

Nothing here was obtained by logging in to Meteor. Portal-only fields are
marked as unknown.

## Sources consulted

| # | Source | URL | Retrieved |
|---|---|---|---|
| S1 | ANTIC 2026 website: call for papers, author guidelines, dates, fees | https://antic.co.in/ | 2026-10-09 |
| S2 | ANTIC footer: address for correspondence | https://antic.co.in/footer.html | 2026-10-10 |
| S3 | ANTIC-hosted LaTeX template (`llncs.cls` v2.24 2024/01/29, `splncs04.bst`, `samplepaper.tex`, `llncsdoc.pdf`); ZIP SHA-256 `7cc8efaa…dcaf5de` | https://antic.co.in/static/files/LaTeX2e-Template.zip | 2026-10-09 |
| S4 | Springer "Information for authors and editors" (applies to LNCS, LNAI, LNBI, LNBIP, **CCIS**, LNICST, IFIP AICT) | https://link.springer.com/series/558/information-for-authors-and-editors (ANTIC's link redirects here) | 2026-10-09 |
| S5 | Springer "Instructions for Authors of Papers to be Published in Springer Computer Science Proceedings" (PDF, 10 pp.), linked from S4 | linked as "Instructions for Authors (PDF)" on S4 | 2026-10-09 |
| S6 | Springer's current LaTeX2e proceedings template (`llncs.cls` **v2.25, 2026/09/03**, with `llncsdoc.pdf` including a submission checklist), linked from S4 | linked as "LaTeX2e Proceedings Template (ZIP)" on S4 | 2026-10-09 |
| S7 | Springer Nature Book Authors' Code of Conduct | https://www.springernature.com/gp/authors/book-authors-code-of-conduct | 2026-10-09 |
| S8 | Springer Nature Book Publishing Policies (AI, authorship, competing interests) | https://www.springernature.com/gp/policies/book-publishing-policies | 2026-10-09 |
| S9 | Meteor landing page for ANTIC 2026 (public part only) | https://meteor.springer.com/ANTIC2026 | 2026-10-09 |
| S10 | Springer "CCIS Forthcoming Proceedings" list, dated 19 Aug 2026, linked from S4 | linked from S4 | 2026-10-09 |
| S11 | Springer License-to-Publish form (default, Word), linked from S4 | linked from S4 | 2026-10-09 |

The ANTIC brochure link on the website (`/static/files/ANTIC2026brochure.pdf`) returned a "page not found" page, so it could not be consulted.

---

## Part A — Initial submission (due 15 October 2026)

### A1. Scope, dates and eligibility

| Rule | Type | Source | Status |
|---|---|---|---|
| Submission deadline: **15 October 2026**. Acceptance notification by 20 Nov 2026. Registration fee payment by 30 Nov 2026. Conference 21–23 Dec 2026 at IIIT Lucknow, offline; online presentation only for foreign authors. | Administrative | S1, S9 | ⚠️ not yet submitted |
| Topics: "Advanced Network Technologies and Intelligent Computing", including AI, deep learning, machine learning, and NLP ("Video, Speech & Text Processing using AI"). | Mandatory (scope) | S1 | ✅ in scope (ML/AI) |
| Papers must report "original and unpublished results". | Mandatory | S1 | ⛔ An earlier version of this work is a non-peer-reviewed Zenodo preprint. See `PREPRINT_OVERLAP_REVIEW.md` and the draft inquiry to the organisers. |
| Proceedings intended for Springer CCIS. | Administrative | S1, S9 | ⚠️ ANTIC 2026 does not appear in Springer's CCIS forthcoming list dated 19 Aug 2026 (S10); ANTIC 2021–2025 were published in CCIS (S1). Informational only. |

### A2. Submission system and files

| Rule | Type | Source | Status |
|---|---|---|---|
| Submit through Meteor at https://meteor.springer.com/ANTIC2026. Submissions by e-mail are not accepted. | Mandatory | S1, S9 | ⚠️ author action |
| Required Meteor fields, accepted file types, and whether source files are needed at first submission. | — | not public (login required) | ⛔ unknown. A PDF (`AGENTRUN_ANTIC2026_Submission.pdf`) and the full source ZIP are both ready. |
| Whether review is double-blind. | — | not stated on S1 | ⛔ unknown. The manuscript is **not anonymised**: it names the author, cites the author's preprint and gives the repository URL. |
| Fee payment is due at registration after acceptance (by 30 Nov). The public site does not make payment a condition of initial upload. | Administrative | S1 | ✅ (nothing to do now) |

### A3. Template and formatting

| Rule | Type | Source | Status |
|---|---|---|---|
| Prepare the paper in LaTeX or Word using the Springer proceedings templates. | Mandatory | S1, S5 | ✅ `llncs` class; `llncs.cls` and `splncs04.bst` copied unmodified from the ANTIC-hosted ZIP (S3) and checked byte-identical |
| ANTIC hosts llncs v2.24 (2024). Springer's current template is v2.25 (2026/09/03), which adds `\Description` for figure alt text; the two `splncs04.bst` files are byte-identical. | Informational | S3, S6 | ✅ uses v2.24 as hosted by ANTIC; alt text supplied via `\Description` with a `\providecommand` fallback, so the source also compiles unchanged with v2.25 |
| Do not change layout settings (`\textheight`, `\vspace`, `\baselinestretch`, etc.); avoid `\enlargethispage` and `\pagebreak`. | Mandatory (class documentation) | S3/S6 `llncsdoc.pdf` §5–6 | ✅ none used |
| Fonts: templates are based on CMR; avoid Type 3 fonts; use T1 encoding. | Mandatory / Recommended | S5 §4.3, S6 `llncsdoc` §4 | ✅ CMR/EC fonts via `cm-super` (Type 1); figure fonts are embedded TrueType; `pdffonts` reports 0 Type 3 fonts |
| Avoid TikZ, xy and pstricks where possible. | Recommended | S6 `llncsdoc` §4 | ✅ figures are vector PDFs made with matplotlib |
| Do not load `amsmath` together with `newtxmath`. | Mandatory (if newtx used) | S6 | ✅ neither package is used |
| Paper length: full papers 12–15+ pages, short papers under 12 pages, "where a page constitutes 300–400 words"; papers under 6 pages are not allowed. Springer's guidance: full 12–15 or more, short 6–11. | Mandatory (ANTIC) | S1, S5 §4.2 | ✅ **full paper**: 14 pages in llncs; about 5,350 words including references (about 4,700 before references), i.e. 12–16 "pages" at 300–400 words per page |
| Headings capitalised; only the first two levels numbered; no "0" section. | Mandatory | S5 §4.1 | ✅ |
| Abstract of 150–250 words; no footnotes in the abstract. | Mandatory | S3 `samplepaper.tex`, S5 §4.7 | ✅ 218 words; no footnotes |
| Keywords via `\keywords`. | Template | S3 | ✅ 6 keywords |
| Table captions above tables, figure captions below figures; every figure and table referenced in the text; captions that are not full sentences have no final period. | Mandatory | S5 §4.5 | ✅ |
| Vector graphics; lettering of at least 6 pt; legible in black and white; line art ≥ 800 dpi if raster. | Mandatory | S5 §4.5 | ✅ all figures vector; smallest lettering 6 pt at final size; greyscale-safe (hatching, grey fill, text labels) |
| No colour in text, tables or equations. | Mandatory | S5 §4.5 | ✅ (`hyperref` with `hidelinks`) |
| Tables and equations editable, not images. | Mandatory | S5 §4.5 | ✅ |
| Equations numbered consecutively, without section counters. | Mandatory | S5 §4.6 | ✅ (one numbered equation) |
| Alternative text for figures. | Mandatory (EU Accessibility Act); may be requested by the PC chairs or done by typesetters | S5 §3, S6 `llncsdoc` §10 | ✅ `\Description` provided for all 3 figures |
| Program code in typewriter font. | Recommended | S5 §4.8 | ✅ |
| Numbered citations in square brackets, alphabetical order preferred; every reference cited and vice versa; DOIs strongly encouraged. | Mandatory / Recommended | S5 §4.9, S6 §12 | ✅ `splncs04` (alphabetical); 29/29 cited; DOIs wherever one exists |
| Bibliography style: the template uses `splncs04`. S5 also says LaTeX users should "use the bibliographic style MathPhySci". | Mandatory | S5 §4, S6 §12 | ⚠️ `splncs04` used, as both official templates and the class documentation direct. The "MathPhySci" wording appears to refer to the same Springer reference standard, but this is not confirmed. |
| Supply all source files and the `.bib`/`.bbl` with the final version. | Mandatory (final files) | S5 §4 | ✅ ZIP contains `.tex`, `.bib`, class, style and figures. The `.bbl` is generated on build; add it to the camera-ready upload if required. |
| Do not use long file names. | Recommended | S5 §4 | ⚠️ deliverable names such as `AGENTRUN_ANTIC2026_Submission.pdf` are fairly long; rename at upload if the portal objects. |
| Running heads and page numbers are added by Springer; a short title can be given. | Informational | S5 §4.4 | ✅ `\titlerunning` set |

### A4. Authors and metadata

| Rule | Type | Source | Status |
|---|---|---|---|
| Author names final at submission; no additions, removals or reordering after delivery to Springer. | Mandatory | S1, S5 §4.1, §5.1 | ⚠️ single author "Alyssa L", taken from the existing manuscript and preprint. Confirm this is the complete author list. |
| Names written out in full; given name before surname. | Mandatory | S5 §5.2 | ⚠️ "L" looks like an initial. Springer asks for names in full; if you have a single main name, confirm how it should appear in the running head and author index. |
| Only real, accountable humans may be authors; AI tools cannot be authors. | Mandatory | S5 §5.2, S8 | ✅ |
| Corresponding author clearly marked in the header; e-mail address mandatory; only one corresponding author. | Mandatory | S5 §4.1 | ✅ e-mail included; sole author. Springer adds the envelope symbol in typesetting (S5 §6.2). |
| ORCID next to author names. | Recommended | S1, S5 §5.3, S8 | ⚠️ no ORCID in the repository; add `\orcidID{...}` if you have one |
| All authors' e-mail addresses (used for the free access link). | Recommended | S1, S5 §4.1 | ✅ |

### A5. Ethics and disclosures

| Rule | Type | Source | Status |
|---|---|---|---|
| Comply with Springer ethical standards and the Code of Conduct. | Mandatory | S1, S5 §2, S7 | ✅ see the items below |
| Originality / redundant publication: be transparent about overlap with prior work. | Mandatory | S7 | ⚠️ the preprint is cited and its corrected statements are identified; the inquiry to the organisers is pending |
| "Disclosure of Interests" section (competing interests) at the end of the paper, in the `credits` environment. | Mandatory (class documentation: "(mandatory) paragraph") | S3/S6 `llncsdoc` §11, S8 | ⚠️ included ("no competing interests"), taken from `publication/conflict_of_interest.md`. You must confirm it. |
| Disclose use of AI tools; authors remain accountable; AI may not fabricate data or citations. | Mandatory (disclosure) | S5 §2, S8 | ⚠️ draft statement included in the credits. You must confirm or correct the scope. |
| Acknowledge sources; no plagiarism (Springer may screen with software). | Mandatory | S7 | ✅ text written from scratch; 0.2% of 8-word sequences shared with the preprint |
| Funding statement or acknowledgments. | Optional (acknowledgments) | S6 §11 | ⚠️ none included; `publication/funding_statement.md` says "independent research", but this has not been confirmed |
| Ethics approval for human subjects. | Conditional | S7 | ✅ not applicable (no human participants) |
| Electronic supplementary material must be approved by the PC chairs. | Mandatory (if used) | S5 §5.4 | ✅ none; the repository is cited instead |

---

## Part B — After acceptance (do NOT confuse with submission)

| Rule | Type | Source | Status |
|---|---|---|---|
| Register and pay by **30 Nov 2026**: 10,000 INR for Indian authors, 250 USD for foreign authors. Payment details "Coming Soon" on the site. | Administrative | S1 | Pending acceptance |
| Only accepted, registered **and presented** papers are sent to Springer; Springer quality assurance may still withdraw a paper. | Mandatory | S1 | Pending |
| Presentation is in person at IIIT Lucknow; online presentation only for foreign authors. | Mandatory | S1 | ⚠️ an Indian author must plan to attend in person |
| Signed **License-to-Publish** form, sent as a scanned PDF after acceptance. Signed by the corresponding author on behalf of all authors; the name must match the corresponding author in the paper header; **digital signatures not acceptable**. | Mandatory | S1, S5 §5.1, S11 | Pending (form downloaded from S4 for reference) |
| No authorship changes once the paper is delivered to Springer. | Mandatory | S1, S5 §5.1 | Note |
| Proofs are checked by the corresponding author, usually within 72 hours; only typesetting errors are corrected. | Mandatory | S5 §6.2 | Note |
| Open Access / Open Choice requires a separate OA licence and Springer's fees; ask the conference contact. | Optional | S1, S5 §9 | Optional |
| Alt text may be requested by the PC chairs, or checked at the proof stage. | Mandatory | S5 §3 | ✅ already in source |
| Final camera-ready: all source files plus PDF; `.bib`/`.bbl`. | Mandatory | S5 §4 | Ready to regenerate |
| About one month after publication, authors whose e-mail is in the header receive a free download link. | Informational | S1, S5 §8 | — |

---

## Unresolved items (need your decision or an official answer)

1. ⛔ **Prior preprint versus "original and unpublished results".** Ask the organisers. A draft is in `PREPRINT_OVERLAP_REVIEW.md`. Not sent.
2. ⛔ **Single- or double-blind review.** Not stated publicly. If double-blind, the manuscript must be anonymised, and the preprint makes the author identifiable regardless.
3. ⛔ **Meteor submission fields and file requirements.** Visible only after logging in.
4. ⚠️ **Author name in full, ORCID, AI-use disclosure scope, competing-interest and funding statements.** All need your confirmation.
5. ⚠️ **"MathPhySci" versus `splncs04`.** `splncs04` follows both official templates.
6. ⚠️ **Page size.** The PDF is US Letter, the TeX default and the same as Springer's own compiled sample. Springer re-typesets, so this is informational.
