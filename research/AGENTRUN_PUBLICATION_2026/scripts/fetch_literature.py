"""Fetch verified metadata (title, authors, dates, abstract, comment, journal ref, DOI) from the arXiv API.

    py -3.11 scripts/fetch_literature.py

Writes literature/arxiv_metadata.json. Used to build RELATED_WORK_AND_NOVELTY.md;
every entry there must match this file.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

IDS = {
    # six closest-overlap papers identified by the previous session (13 Nov 2026)
    "2610.05732": "close", "2611.15729": "close", "2610.31446": "close",
    "2610.34684": "close", "2611.01718": "close", "2610.41124": "close",
    # further candidates from the previous session's arXiv result lists
    "2611.07631": "candidate", "2610.41056": "candidate", "2609.38866": "candidate",
    "2610.17544": "candidate", "2611.09662": "candidate",
    # benchmarks and baselines already cited in the dossier
    "2605.06527": "benchmark", "2507.05257": "benchmark", "2610.09193": "benchmark",
    "2410.10813": "benchmark", "2402.17753": "benchmark",
    "2608.12476": "system", "2501.13956": "system", "2504.19413": "system", "2310.08560": "system",
    "2310.01798": "verification", "2406.01297": "verification", "2310.11511": "verification",
    "2401.15884": "verification",
}


def tag(e, name):
    m = re.search(rf"<{name}[^>]*>(.*?)</{name}>", e, re.S)
    return " ".join(m.group(1).split()) if m else None


def main():
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": ",".join(IDS), "max_results": 60})
    xml = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-script"}), timeout=90).read().decode("utf-8")
    out = {}
    for e in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        aid = tag(e, "id").split("/abs/")[-1]
        base = aid.split("v")[0]
        out[base] = {"arxiv_id": aid, "role": IDS.get(base), "title": tag(e, "title"),
                     "authors": re.findall(r"<name>(.*?)</name>", e), "published": tag(e, "published"),
                     "updated": tag(e, "updated"), "comment": tag(e, "arxiv:comment"),
                     "journal_ref": tag(e, "arxiv:journal_ref"), "doi": tag(e, "arxiv:doi"),
                     "primary_category": (re.search(r'arxiv:primary_category[^>]*term="([^"]+)"', e) or [None, None])[1],
                     "abstract": tag(e, "summary")}
    missing = sorted(set(IDS) - set(out))
    Path(__file__).resolve().parent.parent.joinpath("literature", "arxiv_metadata.json").write_text(
        json.dumps({"fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "missing": missing,
                    "papers": out}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(out), "fetched; missing:", missing)


if __name__ == "__main__":
    main()
