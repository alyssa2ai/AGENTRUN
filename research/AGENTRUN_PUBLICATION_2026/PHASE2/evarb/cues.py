"""Clause-level linguistic cues in a memory record's text.

The Phase 1 arbiter (TEA) matched a correction lexicon anywhere in the text. It therefore read
"This does not replace the 298600" as a correction (p1hold N3: 0/6). Here every cue is found
inside a clause and qualified by what scopes over it in that clause:

  negated       a negator within the 4 tokens before the cue ("does not replace", "is not a correction")
  quoted        the cue is inside quotation marks, or the clause is reported speech
                ("X wrote that ...", "according to ...")
  hypothetical  the clause is conditional or hypothetical ("if ...", "would", "might", "were to")

Cue kinds (each a Clause):
  correction     correct(ion|ed), erratum, typo, "was a mistake / wrong / incorrect"
  supersession   replace(s|d), supersede(s|d), "instead of", "no longer", revised, amended, update(d|s), overrides
  dismissal      disregard, ignore, discard, withdrawn, retracted, obsolete, outdated
  retention      "remains valid", "still stands", "is unchanged", "continues to apply"
  unconfirmed    "not (yet) confirmed/approved/final/adopted", pending, proposed, draft, tentative,
                 provisional, "under review", "awaiting", "subject to approval"
  contradiction  "both figures stand", "until reconciled", discrepancy, disagree, "conflicts with"
  hypothetical_value  the record's own value is stated inside a conditional / hypothetical clause
Only correction and dismissal cues (not "update" / "revised", which are often incidental) may
break a same-time tie without referring to the rival value.

A clause *refers to the rival* if it mentions the rival's value (token-bounded; numbers compared
numerically) or uses an anaphor for an earlier value ("the earlier figure", "the previous value",
"this morning's figure"). Validity dates: a date after "as of / as at / effective / valid from /
since / dated / updated on / starting" (valid_from) or after "until / through / valid to"
(valid_to); a date equal to the record's own value (a deadline) is ignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from . import paths  # noqa: F401
import memlab  # noqa: E402

_MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                       "september", "october", "november", "december"], 1)}
_MON = r"(?:january|february|march|april|may|june|july|august|september|october|november|december)"
_ORD = r"(?:st|nd|rd|th)?"
DATE = (r"(?:(?P<iso>\d{4}-\d{2}-\d{2})|(?P<dmy>\d{1,2}" + _ORD + r" (?:of )?" + _MON + r",? \d{4})|(?P<mdy>" + _MON
        + r" \d{1,2}" + _ORD + r",? \d{4}))")
VALID_FROM_RE = re.compile(r"\b(?:as of|as at|effective(?: from| on| as of)?|valid (?:from|since|as of)|since|dated|"
                           r"updated on|starting(?: from| on)?|beginning(?: from| on)?|from|with effect from|"
                           r"takes? effect(?: on| from)?|appl(?:ies|y|ied) from|applicable from)\b[\s:,]*" + DATE, re.I)
# evarb-0.2: words that signal deliberation or doubt about a record's value. A record that wins only by
# time order (record_time / valid_time) and contains one of them is advised, never enforced.
DOUBT_RE = re.compile(r"\b(?:suggest\w*|discuss\w*|consider\w*|floated|propos\w*|remain\w*|still|confirm\w*|approv\w*|"
                      r"plan(?:s|ned)?|expect\w*|tentative\w*|likely|possibl\w*|perhaps|maybe|claim\w*|rumou?r\w*|"
                      r"reportedly|unclear|uncertain\w*|tbc|tbd)\b", re.I)
VALID_TO_RE = re.compile(r"\b(?:until|till|through|valid (?:to|until|through)|up to)\b[\s:,]*" + DATE, re.I)

KINDS = {
    "correction": r"correct(?:ion|ions|ed|s)?|erratum|errata|typo|was (?:a |an )?(?:mistake|wrong|incorrect|error|typo)|"
                  r"(?:is|was) (?:wrong|incorrect|in error)|mistaken(?:ly)?|amended|amends|amendment",
    "supersession": r"replace[sd]?|replacing|replacement|supersede[sd]?|superseding|instead of|no longer|revised|"
                    r"revises|revision|update[sd]?|updating|overrides?|overridden|"
                    r"changed (?:from|to)",
    "dismissal": r"disregard(?:ed)?|ignore[sd]?|discard(?:ed)?|withdrawn|withdraws?|retracted|retracts?|obsolete|"
                 r"outdated|out of date|void(?:ed)?|cancel(?:l?ed|s)?",
    "retention": r"remains? (?:the )?(?:valid|current|in effect|in force|unchanged|the same|correct|confirmed|official|"
                 r"agreed|approved|binding|authoritative)|"
                 r"still (?:stands|valid|applies|holds|in effect|current|correct|the (?:official|confirmed|agreed))|"
                 r"is unchanged|unchanged|continues to apply|stays (?:valid|in effect|the same)|stands as",
    "unconfirmed": r"not (?:yet )?(?:been )?(?:confirmed|approved|final(?:i[sz]ed)?|adopted|signed off|agreed|ratified)|"
                   r"unconfirmed|unapproved|pending|proposed|proposal|draft|tentative|provisional|"
                   r"under (?:review|discussion|consideration)|awaiting|subject to (?:approval|confirmation)|"
                   r"to be confirmed",
    "contradiction": r"both (?:figures|values|numbers|entries|records)? ?(?:stand|remain|apply|are valid)|"
                     r"until (?:they are |it is )?reconciled|discrepanc(?:y|ies)|disagree(?:s|ment)?|"
                     r"conflicts? with|inconsistent with|do not match|does not match",
}
CUE_RE = {k: re.compile(r"\b(?:" + v + r")\b", re.I) for k, v in KINDS.items()}
NEGATOR = re.compile(r"\b(?:not|no|never|neither|nor|without|nobody|none|nothing|isn't|wasn't|doesn't|don't|didn't|won't|cannot|"
                     r"can't|hasn't|haven't|aren't|n't)\b", re.I)
REPORTED = re.compile(r"\b(?:said|says|wrote|writes|claimed|claims|reported|reports|mentioned|forwarded|"
                      r"according to|quoted|quotes|suggested|suggests|rumou?red|asked whether|alleged(?:ly)?)\b", re.I)
HYPOTHETICAL = re.compile(r"\b(?:if|would|could|might|were to|suppose|supposing|hypothetical(?:ly)?|in case|unless|"
                          r"assuming|scenario|should (?:the|it|this)|may (?:be|replace|change|become|increase|decrease|"
                          r"move|rise|fall))\b", re.I)
ANAPHOR = re.compile(r"\b(?:the|this|that) (?:earlier|previous|prior|original|old|older|initial|first|morning'?s?|"
                     r"preceding|last)\b(?: \w+){0,2}? ?(?:figure|value|number|entry|amount|estimate|record|one|"
                     r"version|date|lead|region|port|size|budget)\b|\b(?:the|this) (?:figure|value|number|entry|amount)s? "
                     r"(?:given|noted|reported|recorded|stated|entered) (?:earlier|before|previously|this morning)\b", re.I)
QUOTES = re.compile(r"[\"“”]([^\"“”]{3,})[\"“”]|(?<!\w)'([^']{3,})'(?!\w)")
SPLIT = re.compile(r"(?<=[.;!?])\s+(?=[A-Z0-9\"“(])|;\s+|\s+—\s+|\s+-\s+(?=[A-Z])")


def parse_date(m: re.Match) -> str | None:
    try:
        if m.group("iso"):
            return date.fromisoformat(m.group("iso")).isoformat()
        s = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", (m.group("dmy") or m.group("mdy")).lower().replace(",", ""))
        s = [t for t in s.split() if t != "of"]
        if m.group("dmy"):
            return date(int(s[2]), _MONTHS[s[1]], int(s[0])).isoformat()
        return date(int(s[2]), _MONTHS[s[0]], int(s[1])).isoformat()
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def mentions(text: str, value) -> bool:
    """Token-bounded mention of a record value; numbers compared numerically."""
    if value is None or str(value).strip() == "":
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        nums = re.findall(r"(?<![\w.\-])-?\d[\d,]*(?:\.\d+)?(?![\w])", text)
        return any(abs(float(n.replace(",", "")) - float(value)) < 1e-9 for n in nums)
    v = memlab._norm(value)
    return bool(v) and re.search(r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])", memlab._norm(text)) is not None


@dataclass
class Clause:
    kind: str
    text: str
    negated: bool
    quoted: bool
    hypothetical: bool
    anaphoric: bool

    @property
    def asserted(self) -> bool:
        """The record itself asserts this cue (not negated, reported or hypothetical)."""
        return not (self.negated or self.quoted or self.hypothetical)


@dataclass
class RecordCues:
    record_id: str
    valid_from: str | None = None
    valid_to: str | None = None
    clauses: list[Clause] = field(default_factory=list)
    quoted_spans: list[str] = field(default_factory=list)
    own_value_asserted: bool = True   # evarb-0.2: own value stated in at least one plain (unqualified) clause
    doubt: bool = False               # evarb-0.2: DOUBT_RE matches anywhere in the text

    def of(self, *kinds, asserted=None) -> list[Clause]:
        return [c for c in self.clauses if c.kind in kinds and (asserted is None or c.asserted == asserted)]


def clauses_of(text: str) -> list[str]:
    parts = [p.strip() for p in SPLIT.split(text or "") if p and p.strip()]
    return parts or [text or ""]


def _negated(clause: str, start: int) -> bool:
    toks = re.findall(r"[A-Za-z']+", clause[:start])[-4:]
    return any(NEGATOR.fullmatch(t) for t in toks) or bool(re.search(r"n't\s*$", clause[:start]))


def analyse(rec: dict) -> RecordCues:
    text = rec.get("text") or ""
    own = str(rec.get("value"))
    out = RecordCues(rec.get("record_id", "?"))
    vf = {d for m in VALID_FROM_RE.finditer(text) if (d := parse_date(m)) and d != own}
    vt = {d for m in VALID_TO_RE.finditer(text) if (d := parse_date(m)) and d != own}
    out.valid_from = vf.pop() if len(vf) == 1 else None
    out.valid_to = vt.pop() if len(vt) == 1 else None
    quoted = [a or b for a, b in QUOTES.findall(text)]
    out.quoted_spans = quoted
    out.doubt = DOUBT_RE.search(text) is not None
    plain_value = False
    for cl in clauses_of(text):
        bare = QUOTES.sub(" ", cl)  # the clause without its quoted spans
        if mentions(bare, rec.get("value")) and not (REPORTED.search(cl) or HYPOTHETICAL.search(cl)):
            m = CUE_RE["supersession"].search(cl) or CUE_RE["correction"].search(cl)
            if not (m and _negated(cl, m.start())):
                plain_value = True
    out.own_value_asserted = plain_value
    for cl in clauses_of(text):
        reported = REPORTED.search(cl) is not None
        hypo = HYPOTHETICAL.search(cl) is not None
        anaph = ANAPHOR.search(cl) is not None
        for kind, rx in CUE_RE.items():
            for m in rx.finditer(cl):
                inq = any(m.group(0).lower() in q.lower() and q.lower() in cl.lower() for q in quoted)
                neg = _negated(cl, m.start())
                if kind == "unconfirmed" and m.group(0).lower().startswith("not"):
                    neg = False  # "not confirmed" is itself the cue
                out.clauses.append(Clause(kind, cl, neg, inq or reported, hypo, anaph))
        if hypo and mentions(cl, rec.get("value")):
            out.clauses.append(Clause("hypothetical_value", cl, False, reported, True, anaph))
    return out


def refers_to(clause: Clause, rival: dict, n_rival_values: int) -> bool:
    return mentions(clause.text, rival.get("value")) or (clause.anaphoric and n_rival_values == 1)
