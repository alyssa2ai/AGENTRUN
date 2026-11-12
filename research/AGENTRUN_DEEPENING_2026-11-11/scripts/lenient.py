"""POST HOC re-scoring aid. Not part of the frozen protocol.

The frozen scorer accepts a final answer only as a submit_answer tool call or
a JSON object. Small local models often wrote the same content as plain
"status: ... / value: ..." text. lenient_final() reads that form, so the
size of the format effect can be reported next to the strict score.
"""

import re

_STATUS = re.compile(r"status\W{0,4}(answer|abstain|conflict)", re.I)
_VALUE = re.compile(r"value\W{0,3}[:=]\s*\"?([^\n\"]*)", re.I)


def lenient_final(text):
    m = _STATUS.search(text or "")
    if not m:
        return None
    v = _VALUE.search(text)
    val = v.group(1).strip() if v else None
    return {"status": m.group(1).lower(), "value": val or None, "lenient": True}
