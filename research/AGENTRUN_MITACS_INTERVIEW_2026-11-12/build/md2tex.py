"""Convert the dossier's Markdown subset to LaTeX (XeLaTeX) and build the PDF.

    py -3.11 build/md2tex.py dossier      -> AGENTRUN_MITACS_COMPLETE_RESEARCH_DOSSIER.{md,pdf}
    py -3.11 build/md2tex.py quickref     -> AGENTRUN_MITACS_INTERVIEW_QUICK_REFERENCE.pdf

Supported Markdown: '#' to '###' headings (a leading "12." or "12.3" number is
stripped; LaTeX numbers them), paragraphs, '-' and '1.' lists (one nesting
level), pipe tables with an optional preceding 'Table: caption' line, images
on their own line ('![caption](path)'), '>' callouts, fenced code, fenced
'math' blocks (display LaTeX), inline **bold**, *italic*, `code`, [links](url),
and '<!-- pagebreak -->'.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BUILD = HERE / "build"

SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def esc(s: str) -> str:
    return "".join(SPECIAL.get(c, c) for c in s)


def esc_code(s: str) -> str:
    out = esc(s)
    # allow line breaks after path separators and underscores in long identifiers
    return out.replace("/", r"/\allowbreak{}").replace(r"\_", r"\_\allowbreak{}").replace(".", r".\allowbreak{}")


def inline(s: str) -> str:
    tokens = []

    def keep(tex):
        tokens.append(tex)
        return f"\x00{len(tokens) - 1}\x00"

    s = re.sub(r"`([^`]+)`", lambda m: keep(r"\texttt{" + esc_code(m.group(1)) + "}"), s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: keep(r"\href{" + m.group(2).replace("%", r"\%").replace("#", r"\#")
                                                          + "}{" + esc(m.group(1)) + "}"), s)
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", s)
    s = s.replace("→", r"$\rightarrow$").replace("≥", r"$\geq$").replace("≤", r"$\leq$")
    s = s.replace("arXiv:", r"arXiv:\allowbreak{}").replace("modelcontextprotocol.io", r"modelcontext\-protocol.io")
    s = re.sub("[฀-๿][฀-๿ ]*[฀-๿]", lambda m: r"{\thaifont " + m.group(0) + "}", s)
    s = re.sub("\x00(\\d+)\x00", lambda m: tokens[int(m.group(1))], s)
    return s


def is_num(cell: str) -> bool:
    c = cell.strip().replace("%", "").replace(",", "").replace("−", "-").replace("*", "")
    return bool(re.fullmatch(r"[-+]?\d+(\.\d+)?( / [-+]?\d+(\.\d+)?)?(\s*\(.*\))?", c)) or c in ("—", "-", "")


def table(rows: list[list[str]], caption: str | None) -> str:
    header, body = rows[0], rows[1:]
    n = len(header)
    plain = lambda c: re.sub(r"[*`]", "", c)  # noqa: E731
    # body text sets the proportional share; the longest single word sets a floor (headers may wrap)
    lens = [min(max(max((len(plain(r[i])) for r in body if i < len(r)), default=0),
                    max(len(w) for w in plain(header[i]).split() or [""]), 3), 70) for i in range(n)]
    longest_word = [max(len(w) for r in rows if i < len(r) for w in (plain(r[i]).split() or [""])) for i in range(n)]
    avail = 1.0 - 0.020 * n
    floor = [min(0.0118 * (lw + 1), 0.30) for lw in longest_word]
    rest = max(avail - sum(floor), 0.0)
    extra = [max(l - lw, 0) for l, lw in zip(lens, longest_word)]
    tot = sum(extra) or 1
    widths = [f + rest * e / tot for f, e in zip(floor, extra)]
    scale = avail / sum(widths)
    widths = [w * scale for w in widths]
    numeric = [all(is_num(r[i]) for r in body if i < len(r)) and i > 0 for i in range(n)]
    spec = "".join((r">{\raggedleft\arraybackslash}" if numeric[i] else r">{\raggedright\arraybackslash}")
                   + f"p{{{widths[i]:.3f}\\linewidth}}" for i in range(n))
    out = [r"\begingroup\small\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.18}",
           r"\begin{longtable}{" + spec + "}"]
    if caption:
        out.append(r"\caption{" + inline(caption) + r"}\\")
    head = " & ".join(r"\textbf{" + inline(c) + "}" for c in header) + r" \\"
    out += [r"\toprule", head, r"\midrule", r"\endfirsthead", r"\toprule", head, r"\midrule", r"\endhead",
            r"\bottomrule", r"\endlastfoot"]
    for r in body:
        r = r + [""] * (n - len(r))
        out.append(" & ".join(inline(c) for c in r[:n]) + r" \\")
    out += [r"\end{longtable}", r"\endgroup", ""]
    return "\n".join(out)


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def convert(md: str, chapters: bool = True) -> str:
    lines = md.splitlines()
    out, i, caption = [], 0, None
    para: list[str] = []
    list_stack: list[str] = []

    def flush_para():
        if para:
            out.append(inline(" ".join(para)) + "\n")
            para.clear()

    def close_lists(level=0):
        while len(list_stack) > level:
            out.append(r"\end{" + list_stack.pop() + "}")

    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if st == "<!-- pagebreak -->":
            flush_para(); close_lists(); out.append(r"\clearpage"); i += 1; continue
        if st.startswith("```"):
            flush_para(); close_lists()
            kind = st[3:].strip()
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i]); i += 1
            i += 1
            if kind == "math":
                out.append(r"\begin{equation*}" + " ".join(b.strip() for b in block) + r"\end{equation*}")
            else:
                out.append(r"\begin{small}\begin{verbatim}" + "\n" + "\n".join(block) + "\n" + r"\end{verbatim}\end{small}")
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", st)
        if m:
            flush_para(); close_lists()
            level, title = len(m.group(1)), m.group(2)
            title = re.sub(r"^\d+(\.\d+)*\.?\s+", "", title)
            numbered = re.match(r"^\d+(\.\d+)*\.?\s", m.group(2)) is not None
            cmd = (["chapter", "section", "subsection"] if chapters else ["section", "subsection", "subsubsection"])[level - 1]
            star = "" if numbered else "*"
            out.append(f"\\{cmd}{star}{{{inline(title)}}}")
            if not numbered and level == 1:
                out.append(f"\\addcontentsline{{toc}}{{{cmd}}}{{{inline(title)}}}")
                out.append(r"\markboth{" + inline(title) + "}{" + inline(title) + "}")
            i += 1
            continue
        if st.startswith("Table:"):
            flush_para(); close_lists()
            caption = st[len("Table:"):].strip()
            i += 1
            continue
        if st.startswith("|"):
            flush_para(); close_lists()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                r = split_row(lines[i])
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in r):
                    rows.append(r)
                i += 1
            out.append(table(rows, caption))
            caption = None
            continue
        m = re.match(r"^!\[(.*)\]\((.*?)\)(\{width=([\d.]+)\})?$", st)
        if m:
            flush_para(); close_lists()
            w = m.group(4) or "1.0"
            # placed in the text flow (not floated) so every figure stays next to the text that discusses it
            out.append(r"\par\begin{minipage}{\linewidth}\centering\vspace{4pt}\includegraphics[width=" + w
                       + r"\linewidth,keepaspectratio,height=0.40\textheight]{" + (HERE / m.group(2)).as_posix()
                       + r"}\captionof{figure}{" + inline(m.group(1)) + r"}\vspace{6pt}\end{minipage}\par")
            i += 1
            continue
        if st.startswith(">"):
            flush_para(); close_lists()
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(lines[i].strip()[1:].strip()); i += 1
            out.append(r"\begin{callout}" + inline(" ".join(block)) + r"\end{callout}")
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            flush_para()
            indent = len(m.group(1).replace("\t", "    "))
            level = 1 if indent < 2 else 2
            kind = "itemize" if m.group(2) in "-*" else "enumerate"
            close_lists(level)
            if len(list_stack) < level:
                out.append(r"\begin{" + kind + "}")
                list_stack.append(kind)
            elif list_stack[-1] != kind:
                close_lists(level - 1)
                out.append(r"\begin{" + kind + "}")
                list_stack.append(kind)
            text = [m.group(3)]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) \
                    and lines[i].startswith("  ") and not lines[i].strip().startswith(("|", "```", "!", ">")):
                text.append(lines[i].strip()); i += 1
            out.append(r"\item " + inline(" ".join(text)))
            continue
        if not st:
            flush_para()
            if list_stack and not (i + 1 < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i + 1])):
                close_lists()
            i += 1
            continue
        if list_stack and line.startswith("  "):
            out.append(inline(st)); i += 1; continue
        close_lists()
        para.append(st)
        i += 1
    flush_para(); close_lists()
    return "\n".join(out)


PREAMBLE = r"""
\usepackage{fontspec}
\setmainfont{Cambria}
\setsansfont{Calibri}
\setmonofont{Consolas}[Scale=0.88]
\newfontfamily\thaifont{Leelawadee UI}[Scale=0.95]
\usepackage[a4paper,top=2.4cm,bottom=2.4cm,left=2.4cm,right=2.4cm,headheight=15pt]{geometry}
\usepackage{xcolor,graphicx,booktabs,longtable,array,caption,enumitem,amsmath,amssymb,fancyhdr,titlesec,etoolbox}
\usepackage[hidelinks]{hyperref}
\definecolor{ink}{HTML}{1F2A37}\definecolor{accent}{HTML}{1F4E79}\definecolor{muted}{HTML}{5B6676}
\definecolor{calloutbg}{HTML}{EEF3F9}\definecolor{calloutrule}{HTML}{1F4E79}
\hypersetup{colorlinks=true,linkcolor=accent,urlcolor=accent}
\setlength{\parindent}{0pt}\setlength{\parskip}{0.55em}
\linespread{1.06}
\setlist{itemsep=0.2em,topsep=0.3em,leftmargin=1.4em}
\captionsetup{font={small,color=muted},labelfont={bf,color=ink},justification=raggedright,singlelinecheck=false,skip=6pt}
\captionsetup[longtable]{position=top}
\newenvironment{callout}{\par\smallskip\noindent\begin{lrbox}{0}\begin{minipage}{\dimexpr\linewidth-1.6em\relax}}%
  {\end{minipage}\end{lrbox}\colorbox{calloutbg}{\hspace{0.3em}\usebox{0}\hspace{0.3em}}\par\smallskip}
\pretocmd{\tableofcontents}{\begingroup\hypersetup{linkcolor=ink}}{}{}
\apptocmd{\tableofcontents}{\endgroup}{}{}
\setlength{\emergencystretch}{2.5em}
\makeatletter
\@ifundefined{l@chapter}{}{\renewcommand*\l@section{\@dottedtocline{1}{1.5em}{2.6em}}
  \renewcommand*\l@subsection{\@dottedtocline{2}{4.1em}{3.4em}}}
\makeatother
"""

DOSSIER_HEAD = r"""\documentclass[10.5pt,a4paper,oneside]{report}
""" + PREAMBLE + r"""
\titleformat{\chapter}[display]{\sffamily\color{accent}}{\large\bfseries Chapter \thechapter}{4pt}{\LARGE\bfseries}[\vspace{2pt}{\color{accent}\titlerule[0.8pt]}]
\titlespacing*{\chapter}{0pt}{0pt}{16pt}
\titleformat{\section}{\sffamily\Large\bfseries\color{accent}}{\thesection}{0.6em}{}
\titleformat{\subsection}{\sffamily\large\bfseries\color{ink}}{\thesubsection}{0.6em}{}
\pagestyle{fancy}\fancyhf{}
\renewcommand{\chaptermark}[1]{\markboth{\thechapter.\ #1}{}}
\fancyhead[L]{\sffamily\small\color{muted}AGENTRUN research dossier}
\fancyhead[R]{\sffamily\small\color{muted}\leftmark}
\fancyfoot[C]{\sffamily\small\color{muted}\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\sffamily\small\color{muted}\thepage}\renewcommand{\headrulewidth}{0pt}}
\begin{document}
\begin{titlepage}
\color{ink}
\vspace*{3.2cm}
{\sffamily\color{accent}\small\bfseries RESEARCH DOSSIER \quad|\quad MITACS INTERVIEW\par}
\vspace{0.6cm}
{\sffamily\fontsize{40}{44}\selectfont\bfseries AGENTRUN\par}
\vspace{0.5cm}
{\sffamily\Large Persistent memory, retrieval, provenance and verification\\ in multi-tool LLM agents\par}
\vspace{0.4cm}
{\color{accent}\rule{\linewidth}{1pt}\par}
\vspace{0.4cm}
{\large Architecture, experiments, evidence, failures and limitations\par}
\vfill
{\sffamily\large\bfseries Alyssa L.\par}
{\sffamily 12 November 2026\par}
\vspace{0.8cm}
{\small\color{muted} Every number in this document was recomputed from raw experiment outputs (\texttt{build/verify\_numbers.py}).\\
Research branch \texttt{research/memory-ablation-2026-11}; experiments on the SIT HPC (2\,$\times$\,NVIDIA L40).\par}
\end{titlepage}
\pagenumbering{roman}
\tableofcontents
\clearpage
\pagenumbering{arabic}
"""

QUICK_HEAD = r"""\documentclass[10pt,a4paper]{article}
""" + PREAMBLE.replace("top=2.4cm,bottom=2.4cm,left=2.4cm,right=2.4cm", "top=1.8cm,bottom=1.8cm,left=1.9cm,right=1.9cm") + r"""
\titleformat{\section}{\sffamily\large\bfseries\color{accent}}{\thesection}{0.6em}{}[{\color{accent}\titlerule[0.5pt]}]
\titleformat{\subsection}{\sffamily\normalsize\bfseries\color{ink}}{\thesubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{10pt}{6pt}
\setlength{\parskip}{0.4em}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\sffamily\small\color{muted}AGENTRUN \textbullet{} interview quick reference}
\fancyhead[R]{\sffamily\small\color{muted}Alyssa L. \textbullet{} 12 November 2026}
\fancyfoot[C]{\sffamily\small\color{muted}\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\begin{document}
"""


def build(kind: str) -> Path:
    if kind == "dossier":
        parts = sorted((BUILD / "src").glob("0*.md"))
        md = "\n\n".join(p.read_text(encoding="utf-8").strip() for p in parts) + "\n"
        name = "AGENTRUN_MITACS_COMPLETE_RESEARCH_DOSSIER"
        (HERE / f"{name}.md").write_text(md, encoding="utf-8")
        body_md = md.split("<!-- pagebreak -->", 1)[1]  # title block is rendered by the LaTeX title page
        intro = md.split("<!-- pagebreak -->", 1)[0].split("## How to read this document", 1)[1]
        body = (r"\chapter*{How to read this document}\addcontentsline{toc}{chapter}{How to read this document}"
                r"\markboth{How to read this document}{}" + "\n" + convert(intro) + "\n\\clearpage\n" + convert(body_md))
        tex = DOSSIER_HEAD + body + "\n\\end{document}\n"
    else:
        name = "AGENTRUN_MITACS_INTERVIEW_QUICK_REFERENCE"
        md = (BUILD / "src_quickref" / "quickref.md").read_text(encoding="utf-8")
        (BUILD / f"{name}.md").write_text(md, encoding="utf-8")
        title, rest = md.split("\n", 1)
        tex = QUICK_HEAD + r"{\sffamily\LARGE\bfseries\color{accent} " + inline(title.lstrip("# ")) + r"\par}\vspace{4pt}" \
            + convert(rest, chapters=False) + "\n\\end{document}\n"
    out = BUILD / "tex"
    out.mkdir(exist_ok=True)
    (out / f"{name}.tex").write_text(tex, encoding="utf-8")
    for _ in range(3):  # three passes for the table of contents and longtable widths
        r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"], cwd=out,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(r.stdout[-3000:])
            raise SystemExit(f"xelatex failed for {name}")
    pdf = HERE / f"{name}.pdf"
    pdf.write_bytes((out / f"{name}.pdf").read_bytes())
    print("built", pdf)
    return pdf


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "dossier")
