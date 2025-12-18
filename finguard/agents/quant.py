from google.adk.agents import Agent
from finguard.tools.quant import PythonSandboxTool

def create_quant_agent(model_client=None):
    """
    Creates the Quant Agent (Analyst).
    Running in a simulated sandbox.
    """
    sandbox = PythonSandboxTool()

    return Agent(
        name="quant_agent",
        model="gemini-1.5-pro",
        instruction="You are a Quantitative Analyst. You write Python code to analyze financial data. You do not have internet access.",
        tools=[sandbox.run_python_analysis],
        description="Quant Agent: Performs numerical analysis using Python."
    )
