# Venue selection

**Date of verification: 21 November 2026.** Every fact below was read from the official page named beside it,
using a browser in this session. Anything that could not be read from an official page is marked
**UNVERIFIED** and is not used to support a recommendation.

> **Search limitation, stated up front.** Web *search* was unavailable in this session (the search back end
> returned a model-routing error), so candidate venues were chosen from knowledge and then verified by fetching
> their official pages directly. This is a weaker discovery process than a systematic search: a well-fitting venue
> that did not occur to me would not have been found. The five candidates below were each verified; the *set* of
> candidates was not exhaustively searched.

---

## Recommendation

**Primary: Transactions on Machine Learning Research (TMLR).**
**Second: ACL Rolling Review → ACL 2027.**
**Third: Journal of Artificial Intelligence Research (JAIR).**

TMLR is recommended on scientific fit, not on deadline convenience — it has no deadline at all, which is precisely
why the recommendation cannot be accused of being deadline-driven.

---

## 1. Transactions on Machine Learning Research (TMLR) — **recommended**

| Item | Finding | Source |
|---|---|---|
| Scope | "experimental and/or theoretical studies yielding new insight into the design and behavior of learning in intelligent systems"; "accounts of applications of existing techniques that shed light on the strengths and weaknesses of the methods"; "formalization of new learning tasks … and of methods for assessing performance on those tasks"; "reproducibility studies of previously published results or claims" | `jmlr.org/tmlr/editorial-policies.html` |
| Acceptance criteria | Two questions only: (1) "Are the claims made in the submission supported by accurate and convincing evidence?" — "the most important criterion"; (2) would some of the audience be interested, and is it communicated clearly. Explicitly: the second criterion "should not be used as a reason to reject work that isn't considered 'significant' or 'impactful' because it isn't achieving a new state-of-the-art on some benchmark. Nor should it form the basis for rejecting work on a method considered not 'novel enough', as novelty of the studied method is not a necessary criterion for acceptance in TMLR." | `jmlr.org/tmlr/acceptance-criteria.html` |
| Length | "Submissions may be any length, but a paper's length should be justified by its content and papers that are unusually long (not counting any Appendices) are likely to result in reviewing delays." | `jmlr.org/tmlr/author-guide.html` |
| Template | "Submissions must be PDF files generated using the TMLR LaTeX stylefile and template." Official files obtained from the JMLR organisation repository: `tmlr.sty`, `tmlr.bst`, `fancyhdr.sty`, `main.tex`, `math_commands.tex` | `jmlr.org/tmlr/author-guide.html`; `github.com/JmlrOrg/tmlr-style-file` |
| Anonymity | Double-blind; "submissions must be anonymized"; the example template warns "Non-anonymous submissions will be rejected without review" | `jmlr.org/tmlr/author-guide.html`, `main.tex` |
| Deadlines | Rolling submission, no deadlines. A holiday pause has been announced in past years (2 Dec – 5 Jan for the 2025/26 turn). **UNVERIFIED whether a 2026/27 pause is announced** — the news list read today shows the 2025 notice, not a 2026 one. | `jmlr.org/tmlr/` |
| Review process | OpenReview, public after assignment; ≥3 reviewers; open-ended rebuttal; decisions are accept as is / accept with minor revision / reject | `jmlr.org/tmlr/editorial-policies.html` |
| Supplementary | Up to 100 MB, PDF or ZIP, must be anonymized; code and data explicitly encouraged for reproducibility | `jmlr.org/tmlr/author-guide.html` |
| Licence and preprints | CC BY 4.0, authors retain copyright; arXiv posting allowed at any time, but the double-blind submission must not link to a version naming the authors | `jmlr.org/tmlr/author-guide.html` |
| Fees | **No publication or open-access charge is stated on any of the three pages read.** Not asserted as "free" — simply, no fee is mentioned. | — |
| Originality constraint | "TMLR only accepts original contributions that don't reuse the authors' own prior work … we do not accept submissions that are expanded versions of conference papers." Overlap with non-archival workshops and preprints is acceptable. | `jmlr.org/tmlr/editorial-policies.html` |

**Why it fits this paper.** The central result is a preregistered confirmatory comparison whose most interesting
finding — that ungated enforcement scores 9.7 pp *higher* than the gated mechanism we propose, at more than twice
the harm — cuts against the proposed design. At a venue that selects on novelty and impact, that honesty is a
liability. TMLR's stated criterion is evidence supporting claims, and it explicitly refuses to reject for lack of
novelty or state-of-the-art. The paper's other properties line up as well: variable length suits a paper with a
large methodological appendix; "methods for assessing performance on those tasks" covers the sealed benchmark; the
100 MB anonymised supplement accommodates the reproducibility package; CC BY 4.0 matches the intended artifact
release; and rolling submission means no scramble.

**Risks.** (i) The originality rule forbids reusing the authors' own prior published text — the earlier QLoRA
specialization study in this repository is separate work and must stay separate, which the manuscript already
enforces. (ii) TMLR is a journal, so there is no conference presentation; if a talk matters, note that TMLR has
joined a Journal-to-Conference track with NeurIPS/ICML/ICLR (announced 21 Oct 2025 on the TMLR news page) —
**the current terms of that track are UNVERIFIED here.** (iii) An unusually long paper risks reviewing delays, so
the main text is kept to a conference-like length with the detail in appendices and the supplement.

## 2. ACL Rolling Review → ACL 2027 — second choice

| Item | Finding | Source |
|---|---|---|
| Process | ARR runs 10-week cycles, generally five per year; submission deadlines are set per cycle | `aclrollingreview.org/dates` |
| Cycles listed today | March 2026 (16 Mar), May 2026 (25 May), August 2026 (3 Aug), October 2026 (12 Oct). **All four have passed.** The October 2026 cycle ends 20 Dec 2026. No later cycle is listed on the page. | `aclrollingreview.org/dates` |
| Path to ACL 2027 | The participating-venue table lists **ACL 2027** with a final ARR submission date of "January, 2027" and **no commitment date yet published** | `aclrollingreview.org/dates` |
| Other open commitments | NAACL 2027 and COLING 2027 both show final ARR submission 12 Oct 2026 (passed) with commitment 23 Dec 2026 — i.e. open only to papers already in the October cycle, which this one is not | `aclrollingreview.org/dates` |
| Mandatory author actions | Designated service-contributor registration; a separate Responsible NLP Checklist due within 48 h of the deadline; from the October 2026 cycle **all** authors need OpenReview accounts including ORCID | `aclrollingreview.org/dates` |
| Page limit / template | **UNVERIFIED** — not stated on the dates page; the CFP and author pages were not read in this session | — |

**Why it fits.** The work is an agent-evaluation paper with a sealed benchmark, family-clustered inference and a
preregistration; ARR venues take exactly this kind of empirical NLP work, and the ACL community is the natural
audience for persistent-memory agents. **Why it is second.** The next actionable deadline is the January 2027
cycle whose exact date is not yet published, and ACL reviewing weighs novelty and significance more heavily than
TMLR's criteria do — which is a poorer match for a paper whose headline includes a result against its own design.

## 3. Journal of Artificial Intelligence Research (JAIR) — third choice

| Item | Finding | Source |
|---|---|---|
| Scope | "JAIR invites submissions in all areas of AI"; full-length original articles, research notes, survey articles, special tracks | `jair.org/index.php/jair/about/submissions` |
| Bar | "must meet the highest quality standards as measured by originality and significance of the contribution" | same |
| Fees | "we do not charge any publication fees to authors, nor do we charge readers for access" — and an explicit warning that predatory journals impersonate JAIR and do charge | same |
| Deadlines | Rolling | same |
| Conference overlap | Permitted: a JAIR submission may extend a conference paper if it adds substantial unpublished material, with notification at submission | same |
| Artifacts | Online appendices with data, code or instructions "strongly encouraged" | same |
| Template / length / anonymity | **UNVERIFIED** — the formatting sections were not read in this session | — |

**Why it fits.** Respected, genuinely free, open access, rolling, and it tolerates journal-length treatment of a
large empirical study. **Why it is third.** JAIR explicitly measures by "originality and significance", the two
criteria TMLR deliberately sets aside, which is the weaker match for this paper's honest framing.

## 4. COLM 2027 — possible, not yet announced

COLM is the Conference on Language Modeling. `colmweb.org` redirects to `colm.cc`, which today shows **COLM 2026**
(Hilton Union Square, San Francisco, 6–9 October 2026) as the current conference, with registration closed and
pre-proceedings published; past years listed are 2024 and 2025. `colm.cc/cfp` returns **404**. **No COLM 2027
dates, deadline, template, page limit or policy could be verified; all of that is UNVERIFIED.** Scientifically COLM
would be a strong fit — it is explicitly a venue for "understanding, improving, and critiquing" LM technology, and
"critiquing" is a fair description of this paper's ablation findings — so it is worth re-checking when the 2027
call appears. It cannot be recommended today on verified information.

Source: `colm.cc/`, `colm.cc/cfp`.

## 5. AAAI-27 — closed

AAAI-27 (41st AAAI, Montréal, 16–23 February 2027) has passed every author deadline: abstracts 21 July 2026, full
papers 28 July 2026, supplementary and code 31 July 2026, with final notification 30 November 2026 and camera-ready
14 December 2026. It is listed here only to record that it was checked and is not available. AAAI-28 dates are
**UNVERIFIED** (not announced on the page read).

Source: `aaai.org/conference/aaai/aaai-27/`.

---

## Comparison

| | TMLR | ARR → ACL 2027 | JAIR | COLM 2027 | AAAI-27 |
|---|---|---|---|---|---|
| Scientific fit | **Excellent** — criteria are evidence and interest, explicitly not novelty or SOTA | Good — right audience, novelty-weighted | Good — but graded on significance | Likely excellent (unverified) | Fair |
| Open now? | **Yes, rolling** | Next cycle Jan 2027, exact date unpublished | Yes, rolling | Unknown | **No, closed** |
| Length freedom | **Any length, justified by content** | Unverified | Journal length | Unverified | Fixed |
| Anonymity | Double-blind, required | Double-blind | Unverified | Unverified | Double-blind |
| Fees | None stated | Unverified | **None, explicitly** | Unverified | n/a |
| Artifact support | 100 MB anonymised supplement; code and data encouraged | Checklist required | Online appendices encouraged | Unverified | n/a |
| Reputation | Established ML journal, ISSN 2835-8856, OpenReview | Top-tier NLP | Long-established AI journal | New but prominent | Top-tier AI |

## Decision and what it means for the manuscript

The master manuscript is prepared against the **official TMLR template**, which is also venue-neutral enough to
re-target: the paper is written as section files included by `main.tex`, so switching to an ACL or JAIR template
means swapping the preamble and the bibliography style, not rewriting the paper.

Consequences already applied:

- the submission is **anonymous** — no author names, affiliations, acknowledgements or funding statements appear,
  and author information is kept in a separate file for you to complete;
- the main text is kept to a conference-like length with detail moved to appendices and a separate supplement,
  because TMLR warns that unusually long papers face reviewing delays;
- the artifact statement matches CC BY 4.0 and the "restricted until publication" policy for eval3;
- no claim of novelty is made for temporal ordering, deterministic arbitration or gating in isolation.

**Nothing has been submitted, and no submission account has been created.** The venue is yours to approve.
