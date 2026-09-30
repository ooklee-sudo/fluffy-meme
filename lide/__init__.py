"""Harness for "When Delegated Agents Escalate: Loss-Induced Decision Escalation (LIDE)".

Modules
  taxonomy  ex ante action-risk taxonomy (Section 4.3)
  history   length-matched history builder (Sections 4.2, 4.5)
  envs      Environments A (coding) and B (operations) + governance artifacts
  agents    scripted honest / escalating agents (Section 4.5) and a simulated prospect-theory agent
  llm_agent Anthropic-API agent for the live Study 1 / Study 2 runs
  runner    factorial designs and episode runner
  analysis  LIDE classifier and tests for H1-H5 (Section 4.4)
"""
