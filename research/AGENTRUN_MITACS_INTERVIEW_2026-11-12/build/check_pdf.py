"""Automated layout checks for a built PDF, plus page images for visual inspection.

    py -3.11 build/check_pdf.py <pdf> [--sheets]

Reports, per page: text or images outside the printable area (clipping),
lines that run into the right margin, and pages that are nearly empty.
Also maps LaTeX overfull-box and missing-character warnings to pages.
With --sheets, writes contact sheets (6 pages each) to build/pages/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

pdf = Path(sys.argv[1])
doc = fitz.open(pdf)
problems = []
MARGIN_PT = 2.4 * 72 / 2.54 if "QUICK" not in pdf.name else 1.9 * 72 / 2.54
for i, page in enumerate(doc, 1):
    w, h = page.rect.width, page.rect.height
    words = page.get_text("words")
    right_limit = w - MARGIN_PT + 6
    over = [wd for wd in words if wd[2] > right_limit and wd[1] > 40 and wd[3] < h - 40]
    outside = [wd for wd in words if wd[0] < 0 or wd[2] > w or wd[1] < 0 or wd[3] > h]
    imgs = [b for b in page.get_text("dict")["blocks"] if b["type"] == 1]
    img_out = [b for b in imgs if b["bbox"][2] > w - MARGIN_PT + 6 or b["bbox"][0] < MARGIN_PT - 6]
    chars = sum(len(wd[4]) for wd in words)
    if over:
        problems.append((i, f"{len(over)} words past the right margin, e.g. {over[0][4]!r}"))
    if outside:
        problems.append((i, f"{len(outside)} words outside the page"))
    if img_out:
        problems.append((i, f"{len(img_out)} images extend into a side margin"))
    if chars < 250 and i > 2 and not imgs:
        problems.append((i, f"nearly empty page ({chars} characters)"))
print(f"{pdf.name}: {len(doc)} pages")
for p in problems:
    print("  page", p[0], "-", p[1])
if not problems:
    print("  no layout problems detected")

log = pdf.parent / "build" / "tex" / (pdf.stem + ".log")
if log.exists():
    text = log.read_text(encoding="utf-8", errors="replace")
    print("  missing characters:", len(re.findall("Missing character", text)))
    print("  overfull boxes > 2pt:", [m for m in re.findall(r"Overfull \\[hv]box \(([\d.]+)pt", text) if float(m) > 2])

if "--sheets" in sys.argv:
    out = pdf.parent / "build" / "pages" / pdf.stem
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    per = 6
    for s in range(0, len(doc), per):
        pages = list(range(s, min(s + per, len(doc))))
        pix = [doc[p].get_pixmap(dpi=62) for p in pages]
        pw, ph = pix[0].width, pix[0].height
        sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, pw * 3 + 20, ph * 2 + 10), False)
        sheet.clear_with(255)
        for k, px in enumerate(pix):
            x, y = (k % 3) * (pw + 10), (k // 3) * (ph + 10)
            px2 = fitz.Pixmap(fitz.csRGB, px) if px.n != 3 else px
            px2.set_origin(x, y)
            sheet.copy(px2, px2.irect)
        sheet.save(out / f"sheet_{s // per + 1:02d}_p{pages[0] + 1}-{pages[-1] + 1}.png")
    print("  contact sheets:", out)
