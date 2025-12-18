# Copyright 2025 Google LLC
# FinGuard Executor Agent (Refactored for VACP)

from vacp.governed_agent import VACPGovernedAgent
from finguard.tools.execution import execute_order, get_portfolio

executor_agent = VACPGovernedAgent(
    name="executor_agent",
    model="gemini-1.5-pro",
    instruction="""
    You are the Trade Executor.
    You execute approved trades using the `execute_order` tool.
    You must NOT execute if the trade has not been approved by Compliance.
    You can check holdings with `get_portfolio`.
    """,
    tools=[execute_order, get_portfolio],
    description="Executor Agent: Executes trades on the brokerage."
)

def create_executor_agent(model_client=None):
    return executor_agent
