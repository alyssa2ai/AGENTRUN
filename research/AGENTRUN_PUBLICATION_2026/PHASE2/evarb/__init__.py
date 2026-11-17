"""evarb: evidence-basis arbitration with basis-gated enforcement (AGENTRUN Phase 2).

Modules:
  cues      clause-level linguistic cues in record text (correction, supersession, validity dates,
            retention, unconfirmed, negation, quotation, hypothetical/conditional)
  arbiter   per-(entity, attribute) resolution: status + evidence basis + strength
  policy    basis-gated enforcement: enforce / advise / request evidence / no action;
            question temporal intent (current vs historical); safe submission
  render    tool-result labels shown to the agent
  loop      agent loop for the Phase 2 configurations (Phase 1 configs run through rcs/tea unchanged)
  llm_arbiter  LLM evidence arbiter baseline (same output schema)
  clients   model-family adapters around the frozen HFClient
"""
from . import paths  # noqa: F401

EVARB_VERSION = "evarb-0.2"
