from google.adk.agents import Agent
from finguard.tools.compliance import ComplianceTool

def create_compliance_agent(model_client=None):
    """
    Creates the Compliance Agent (Internal Auditor).
    """
    compliance_tool = ComplianceTool()

    return Agent(
        name="compliance_agent",
        model="gemini-1.5-pro",
        instruction="You are a risk officer. You do not generate code. You only validate JSON payloads against the OPA policy. Use the 'validate_proposed_trade' tool.",
        tools=[compliance_tool.validate_proposed_trade],
        description="Compliance Agent: Validates trades against risk policy."
    )
