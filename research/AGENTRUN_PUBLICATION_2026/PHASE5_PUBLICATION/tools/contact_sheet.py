"""Render a PDF to page images and tile them into contact sheets for visual inspection.

    python contact_sheet.py <pdf> <out_dir> [--cols 5] [--rows 2] [--dpi 60]

Used for the publication QA pass: every page of the compiled PDF is inspected, not only the first.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out_dir")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--dpi", type=int, default=60)
    a = ap.parse_args()

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["pdftoppm", "-png", "-r", str(a.dpi), a.pdf, str(tmp / "p")],
                       check=True, capture_output=True)
        pages = sorted(tmp.glob("p-*.png"))
        if not pages:
            raise SystemExit("no pages rendered")
        w, h = Image.open(pages[0]).size
        per = a.cols * a.rows
        pad, label = 6, 14
        made = []
        for s in range(0, len(pages), per):
            chunk = pages[s:s + per]
            sheet = Image.new("RGB", (a.cols * (w + pad) + pad, a.rows * (h + pad + label) + pad), "white")
            d = ImageDraw.Draw(sheet)
            for i, p in enumerate(chunk):
                r, c = divmod(i, a.cols)
                x = pad + c * (w + pad)
                y = pad + r * (h + pad + label)
                sheet.paste(Image.open(p).convert("RGB"), (x, y + label))
                d.text((x + 2, y + 1), f"page {s + i + 1}", fill="black")
                d.rectangle([x, y + label, x + w, y + label + h], outline="#999999")
            f = out / f"sheet_{s // per + 1:02d}.png"
            sheet.save(f)
            made.append(f)
        print(f"{len(pages)} pages -> {len(made)} sheet(s)")
        for f in made:
            print(" ", f)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
