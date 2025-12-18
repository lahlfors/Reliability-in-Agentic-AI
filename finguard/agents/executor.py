from google.adk.agents import Agent
from finguard.tools.execution import BrokerageTool

def create_executor_agent(model_client=None):
    """
    Creates the Executor Agent (The Arm).
    This is the ONLY agent with 'authorized=True' for the BrokerageTool.
    """
    # ZSP: Injecting authorization here.
    brokerage = BrokerageTool(authorized=True)

    return Agent(
        name="executor_agent",
        model="gemini-1.5-pro",
        instruction="You are the Trade Executor. You execute approved trades. You must NOT execute if the trade has not been approved by Compliance.",
        tools=[brokerage.execute_order, brokerage.get_portfolio],
        description="Executor Agent: Executes trades on the brokerage."
    )
