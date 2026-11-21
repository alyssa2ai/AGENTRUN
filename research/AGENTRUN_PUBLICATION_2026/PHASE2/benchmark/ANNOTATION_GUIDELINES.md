# Annotation and writing guidelines: p2val and eval3

**Version 1.1, 14 November 2026.** v1.0 was used for p2val; v1.1 (rule (c)–(e) and §4–§5) for p2val2 and eval3. These guidelines are given to the record writer and to the blind annotator. They are written so that a reader who has never seen AGENTRUN's code can follow them.

## 1. The setting

An assistant keeps a memory of short notes about fictional software projects. Each note (a *record*) states one fact about one project. Facts:
- the approved budget (USD);
- team size;
- staging server port;
- project lead;
- cloud region;
- delivery deadline.

Each record also has, outside its text:
- a `recorded_on` date: when the note was stored, which may be empty;
- a `source`: `meeting_notes`, `imported_doc`, `user_statement` or `system_of_record`.

## 2. Writer instructions

You receive, for each item, the project name, the fact, and for every record its value and a **brief**. Write the record **text** so that it does exactly what the brief says.

1. **Mention the project name and the record's own value** in every text, exactly as given: digits as digits; names, regions and dates spelled exactly.
2. **Follow the brief's meaning exactly. Do not add information it does not ask for:**
   - no extra dates;
   - no correction words when the brief says plain;
   - no hedging that changes the meaning.
3. **Vary the wording across items.** Write like real notes: meeting minutes, spreadsheet lines, chat summaries, document excerpts. Avoid repeating the same template sentence. For corrections, negations and reported claims, use your own natural phrasings.
4. **Keep each text short:** 1–3 sentences, at most 60 words.
5. **Questions.** When an item has a `question_brief`, write that one question in natural wording, as a user would ask it. Never put a value in the question.
6. **Output:** one JSON object per item:

```json
{"item_id": "...", "texts": {"1": "...", "2": "..."}, "question": "..." or null}
```

## 3. Annotator instructions (blind)

You receive, for each item:
- a question;
- the records about that project and fact: text, `recorded_on`, `source`.

You do **not** receive the intended answer. Decide what a careful assistant should answer, using only these records:

| Label | When |
|---|---|
| `answer:<value>` | The records establish one value as the answer to the question |
| `conflict` | The records give different values and do not establish which one is current |
| `abstain` | No record states the asked fact for this project |

**Rules of evidence:**
- **(a) Later dates win.** A later `recorded_on` makes a record newer, unless the texts state when the values took effect; stated effective dates take precedence.
- **(b) Explicit corrections and replacements win.** A record that explicitly corrects, replaces or dismisses another value supersedes it.
- **(c) These do not establish a change, so the established value stands and is the answer:**
  - a record saying it does *not* replace, correct or override another value;
  - a change that is proposed, pending, unconfirmed or conditional;
  - a change that is only reported or claimed by someone.
- **(d) A record that says the earlier value remains valid keeps that value current.**
- **(e) `conflict` applies only when:**
  - two records both state their values as facts and nothing establishes which is current (same date, nothing settling it); or
  - a record says the values disagree, or that both stand until they are reconciled.

  A missing `recorded_on` with no stated dates also gives `conflict`.
- **(f) The source type alone does not settle a disagreement.**
- **(g) Questions about an earlier time** ("before the change", "as of <date>") ask for the value valid at that time.

**Output:** one JSON object per item:

```json
{"item_id": "...", "label": "answer:<value>" | "conflict" | "abstain", "confidence": "high" | "low"}
```

## 4. Adjudication (pre-registered; `PREREGISTRATION.md` §6)

- The gold label of an item is the skeleton's label, fixed **before** any text is written.
- **Gating annotator (v1.1):** a Claude Opus instance with access only to §1, §3 and the annotator input file.
- **Secondary annotator:** Llama-3.1-8B-Instruct, reported but not gating.

  On p2val the open 8B/14B annotators reached κ 0.49 / 0.52 against gold and answered `conflict` even on plain later-dated updates. Opus reached κ 0.73 (87% exact). Its disagreements exposed an inconsistency in the v1.0 rules, which v1.1 fixes.
- An item whose **gating** annotation disagrees with the gold, or that the gating annotator marks low-confidence, is **flagged**.
- Flagged items stay in the sealed file, but are excluded from the **primary** confirmatory analysis and analysed separately.
- No one connected to the mechanism reads or edits eval3 items to resolve disagreements. Agreement statistics (Cohen's κ over answer / conflict / abstain, plus exact-value agreement) are computed by script and reported.

## 5. Limitations of this protocol

- The writer (Qwen2.5-14B-Instruct, open weights, run locally) and the annotators (Claude Opus gating; Llama-3.1-8B secondary) are **language models**, not independent human authors.
- The gating annotator is the same model family as the assistant that built the mechanism. It ran as a separate instance without access to the mechanism, the development data, the gold, or this conversation.
- They had no access to the mechanism's code, cue lists or development data. They did share the guidelines above, which were written by the mechanism's author.
- The categories and their semantics were chosen by the mechanism's author. The skeleton (values, dates, sources, gold) is generated by the author's script.
- What is independent is the **wording** of every record and of the historical questions, and the **check** that the wording carries the intended meaning.
