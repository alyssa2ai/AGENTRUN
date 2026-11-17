# Decision on the eval3 primary item set (16 November 2026, 10:14 UTC)

Taken after the p2val2 annotations (Slurm job 4199) and BEFORE opening any evarb, TEA, legacy or LLM-arbiter output on p2val2, and before any eval3 output exists. Only annotator-vs-gold agreement per category was looked at.

Per-category agreement with the skeleton gold on the 90 valid p2val2 items (Llama-3.1-8B / Qwen2.5-14B, of 4 unless stated):
update_record_time 0 / 2; valid_time_same_import 0 / 2; three_value_chain 0 / 2; hypothetical_change 0 / 4; quoted_claim 0 / 1; as_of_question 1 / 0; unconfirmed_change 1 / 4; conflict_same_validity 1/3 / 3/3; missing_timestamp 3 / 1; negated_both_stand 4 / 2; all other categories 3-4 / 3-4.
Double-agreement primary set: 51 / 90; six categories have 0 primary items.

Decision: eval3's PRIMARY set = all mechanically valid items. Double-agreement and Qwen-agreement subsets are secondary sensitivity analyses. p2val2 analyses report all three, plus the author-audit sensitivity subset (primary minus `p2val2_AUDIT_FLAGGED_IDS.json`).
