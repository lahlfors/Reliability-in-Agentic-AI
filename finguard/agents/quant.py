# Copyright 2025 Google LLC
# FinGuard Quant Agent (Refactored for VACP)

from vacp.governed_agent import VACPGovernedAgent
from finguard.tools.quant import run_python_analysis

quant_agent = VACPGovernedAgent(
    name="quant_agent",
    model="gemini-1.5-pro",
    instruction="""
    You are a Quantitative Analyst.
    You write Python code to analyze financial data.
    You do not have internet access.
    Use the `run_python_analysis` tool for calculations.
    """,
    tools=[run_python_analysis],
    description="Quant Agent: Performs numerical analysis using Python."
)

def create_quant_agent(model_client=None):
    return quant_agent
