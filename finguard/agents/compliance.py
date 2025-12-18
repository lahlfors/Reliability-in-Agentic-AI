# Copyright 2025 Google LLC
# FinGuard Compliance Agent (Refactored for VACP)

from vacp.governed_agent import VACPGovernedAgent
from finguard.tools.compliance import validate_proposed_trade

compliance_agent = VACPGovernedAgent(
    name="compliance_agent",
    model="gemini-1.5-pro",
    instruction="""
    You are a Risk Officer and Compliance Auditor.
    You do not generate code.
    You only validate JSON payloads against the OPA policy.
    Use the `validate_proposed_trade` tool to check if a trade is allowed.
    """,
    tools=[validate_proposed_trade],
    description="Compliance Agent: Validates trades against risk policy."
)

def create_compliance_agent(model_client=None):
    return compliance_agent
