"""Independent text writing and blind annotation with open-weight models (GPU, reproducible).

    python write_and_annotate.py write    --split eval3 --dir <dir> --model Qwen/Qwen2.5-14B-Instruct
    python write_and_annotate.py annotate --split eval3 --dir <dir> --model meta-llama/Llama-3.1-8B-Instruct --tag llama8b

write:    reads <split>_writer_input.jsonl (briefs only, no gold) and writes <split>_texts.jsonl.
          For each item one prompt with ANNOTATION_GUIDELINES.md §1-2 + the item's briefs; greedy decoding.
          Up to 4 attempts per item (greedy, then seeded T=0.7 twice, then greedy), each retry told
          exactly what failed (missing value / name / question), until the output parses and every
          text contains the project name and its own value verbatim (dates as YYYY-MM-DD).
          (v2, after p2val: the v1 writer reformatted date values; 11/88 p2val items failed validation.)
annotate: reads <split>_annotator_input.jsonl (question + records, NO gold) and writes
          <split>_annotations_<tag>.jsonl with {"item_id", "label", "confidence", "raw"}.
          The annotator prompt is ANNOTATION_GUIDELINES.md §1 + §3.
The models used here never see the mechanism's code, development data or gold labels.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from evarb.cues import mentions  # noqa: E402

GUIDE = (HERE / "ANNOTATION_GUIDELINES.md").read_text(encoding="utf-8")


def section(n_from: str, n_to: str | None) -> str:
    s = GUIDE.index(n_from)
    e = GUIDE.index(n_to) if n_to else len(GUIDE)
    return GUIDE[s:e]


SETTING = section("## 1.", "## 2.")
WRITER = section("## 2.", "## 3.")
ANNOT = section("## 3.", "## 4.")


def chat(client, prompt, temperature=None, seed=None):
    if temperature is not None:
        client.temperature = temperature
        if seed is not None:
            client.torch.manual_seed(seed)
    r = client.chat([{"role": "user", "content": prompt}])
    return (r.get("message") or {}).get("content") or r.get("raw_text") or ""


def first_json(raw):
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", raw or ""):
        try:
            obj, _ = dec.raw_decode(raw, m.start())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def write(a, client):
    d = Path(a.dir)
    items = [json.loads(x) for x in (d / f"{a.split}_writer_input.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    dest = d / f"{a.split}_texts.jsonl"
    done = {json.loads(x)["item_id"] for x in dest.read_text(encoding="utf-8").splitlines() if x.strip()} if dest.exists() else set()
    with open(dest, "a", encoding="utf-8") as f:
        for it in items:
            if it["item_id"] in done:
                continue
            spec = {"item_id": it["item_id"], "project": it["entity"],
                    "records": [{"slot": r["slot"], "fact": r["attribute_fact"], "value": r["value"], "brief": r["brief"]}
                                for r in it["records"]], "question_brief": it["question_brief"]}
            exact = "; ".join(f"slot {r['slot']} must contain the exact string {json.dumps(str(r['value']))}"
                              for r in it["records"])
            prompt = (SETTING + "\n" + WRITER + "\nWrite the item below. Every record's own value must appear EXACTLY as "
                      "given (a value that is a date such as 2027-02-16 stays in YYYY-MM-DD form; numbers as plain digits "
                      f"without commas or currency symbols): {exact}. Return ONLY the JSON object, no other text.\n\n"
                      + json.dumps(spec, ensure_ascii=False))
            out, ok, feedback = None, False, ""
            for attempt in range(4):
                raw = chat(client, prompt + feedback, temperature=0.0 if attempt in (0, 3) else 0.7, seed=1000 + attempt)
                obj = first_json(raw)
                if not obj or not isinstance(obj.get("texts"), dict):
                    feedback = "\n\nYour previous answer was not a valid JSON object with a \"texts\" field. Try again."
                    continue
                texts = {str(k): v for k, v in obj["texts"].items()}
                errs = []
                for r in it["records"]:
                    t = texts.get(str(r["slot"]))
                    if not isinstance(t, str):
                        errs.append(f"slot {r['slot']} is missing")
                    else:
                        if it["entity"].lower() not in t.lower():
                            errs.append(f"slot {r['slot']} must name {it['entity']}")
                        if not mentions(t, r["value"]):
                            errs.append(f"slot {r['slot']} must contain exactly {json.dumps(str(r['value']))}")
                q = obj.get("question") if it["question_brief"] else None
                if it["question_brief"] and not (isinstance(q, str) and q.strip()):
                    errs.append("the question is missing")
                out = {"item_id": it["item_id"], "texts": texts, "question": q, "attempts": attempt + 1}
                if not errs:
                    ok = True
                    break
                feedback = "\n\nYour previous answer had problems: " + "; ".join(errs) + ". Fix them and return the full JSON."
            if out is None:
                out = {"item_id": it["item_id"], "texts": {}, "question": None, "attempts": 3}
            out["writer_ok"] = ok
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
            f.flush()
    client.temperature = 0.0


def annotate(a, client):
    d = Path(a.dir)
    items = [json.loads(x) for x in (d / f"{a.split}_annotator_input.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    dest = d / f"{a.split}_annotations_{a.tag}.jsonl"
    done = {json.loads(x)["item_id"] for x in dest.read_text(encoding="utf-8").splitlines() if x.strip()} if dest.exists() else set()
    with open(dest, "a", encoding="utf-8") as f:
        for it in items:
            if it["item_id"] in done:
                continue
            prompt = (SETTING + "\n" + ANNOT + "\nAnnotate the item below. Return ONLY the JSON object.\n\n"
                      + json.dumps(it, ensure_ascii=False))
            raw = chat(client, prompt)
            obj = first_json(raw) or {}
            f.write(json.dumps({"item_id": it["item_id"], "label": obj.get("label"), "confidence": obj.get("confidence"),
                                "raw": raw[:600]}, ensure_ascii=False) + "\n")
            f.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["write", "annotate"])
    ap.add_argument("--split", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", default="ann")
    a = ap.parse_args()
    from evarb.clients import FamilyClient
    client = FamilyClient(a.model, max_new_tokens=600)
    (write if a.mode == "write" else annotate)(a, client)
    print(json.dumps({"mode": a.mode, "split": a.split, "model": a.model, "client": client.describe()}, default=str))


if __name__ == "__main__":
    main()
