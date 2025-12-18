from google.adk.agents import Agent
from finguard.tools.search import SearchTool

def create_researcher_agent(model_client=None):
    """
    Creates the Researcher Agent.
    """
    search = SearchTool()

    return Agent(
        name="researcher_agent",
        model="gemini-1.5-pro",
        instruction="You are a Market Researcher. You find latest news and data using search tools.",
        tools=[search.search_market_news],
        description="Researcher Agent: Fetches market news and data."
    )
