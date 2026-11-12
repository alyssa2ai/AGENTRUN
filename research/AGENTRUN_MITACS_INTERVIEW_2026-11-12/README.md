# AGENTRUN MITACS interview dossier (12 November 2026)

| File | What it is |
|---|---|
| `AGENTRUN_MITACS_COMPLETE_RESEARCH_DOSSIER.pdf` | The full research dossier: 19 chapters, glossary, references, source map |
| `AGENTRUN_MITACS_COMPLETE_RESEARCH_DOSSIER.md` | The same content as Markdown (the single source the PDF is built from) |
| `AGENTRUN_MITACS_INTERVIEW_QUICK_REFERENCE.pdf` | Three-page companion: introductions, five findings, five limitations, ten questions, terms |
| `figures/` | Every chart and diagram in the dossier |
| `build/verify_numbers.py` | Recomputes every number from raw outputs, independently of the original analysis code; writes `build/verified_numbers.json` and checks all quoted figures (0 mismatches) |
| `build/make_figures.py` | Draws the diagrams and the charts from `verified_numbers.json` |
| `build/md2tex.py` | Converts the Markdown to LaTeX and compiles it with XeLaTeX (MiKTeX) |
| `build/check_pdf.py` | Automated layout checks (margins, clipping, missing glyphs, overfull boxes) and page contact sheets |
| `build/src/`, `build/src_quickref/` | Markdown sources |
| `build/references_check.txt` | arXiv API output used to verify every arXiv reference |

Rebuild (from this folder, Python 3.11, MiKTeX on PATH):

```bash
py -3.11 build/verify_numbers.py
```

```bash
py -3.11 build/make_figures.py
```

```bash
py -3.11 build/md2tex.py dossier
```

```bash
py -3.11 build/md2tex.py quickref
```

No experiment was run for this dossier, and no raw result was modified.
