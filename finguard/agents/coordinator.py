# Copyright 2025 Google LLC
# FinGuard Coordinator (Refactored to match Financial Advisor Architecture)

import logging
from vacp.governed_agent import VACPGovernedAgent
from finguard.tools.router import route_request

# Import Sub-Agents (Workers)
from finguard.agents.researcher import researcher_agent
from finguard.agents.quant import quant_agent
from finguard.agents.compliance import compliance_agent
from finguard.agents.executor import executor_agent

logger = logging.getLogger(__name__)

# The Root Coordinator
# This replaces the manual 'FinGuardCoordinator' loop.
finguard_coordinator = VACPGovernedAgent(
    name="finguard_coordinator",
    model="gemini-1.5-pro", # Using 1.5 Pro as standard for FinGuard
    description="FinGuard Supervisor: Manages risk and delegates tasks.",
    instruction="""
    You are the FinGuard Supervisor (Governance Layer).
    Do NOT answer questions directly. Do NOT execute trades directly.

    Your role is to route the session to the correct specialist based on the user's intent:
    1. RESEARCH: If the user needs market news or data.
    2. QUANT_ANALYSIS: If the user needs numerical analysis or Python code.
    3. COMPLIANCE_CHECK: If the user proposes a trade or needs a policy check.
    4. EXECUTION: If a trade is fully approved and ready to be placed.

    Call the `route_request` tool with the correct intent and rationale.
    """,
    tools=[route_request],
    sub_agents=[
        researcher_agent,
        quant_agent,
        compliance_agent,
        executor_agent
    ]
)

# For backward compatibility with existing tests/demos that might look for a class
class FinGuardCoordinator:
    """
    Legacy Wrapper to maintain interface if needed, or we just replace usage.
    For this refactor, we provide a way to 'run' which delegates to the agent runner?

    Actually, the 'main.py' or 'demo.py' usually instantiates this class.
    We should update the consumer.
    But to answer the user's requirement of "finguard becomes equivalent",
    we expose the 'root_agent' (finguard_coordinator) as the entry point.
    """
    def __init__(self, model_client=None, project_id=None):
        self.agent = finguard_coordinator
        # If model_client is passed (mocks), we might need to inject it?
        # ADK agents usually get their client from the runtime configuration or environment.
        pass

    async def run(self, user_query: str):
        # This emulates the old .run() method but uses the new ADK structure?
        # ADK agents don't have a simple .run(str) -> str method like the old loop.
        # They need a Runner.
        # We should encourage using 'run_agent.py' or similar.
        # But for drop-in replacement:
        raise NotImplementedError("Use the ADK Runner to execute this agent.")
