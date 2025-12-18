# Copyright 2025 Google LLC
# FinGuard Researcher Agent (Refactored for VACP)

from vacp.governed_agent import VACPGovernedAgent
from finguard.tools.search import search_market_news

# Use factory or singleton? Singleton is ADK pattern usually.
# But for 'finguard' let's define it as a module level instance to match financial-advisor pattern.

researcher_agent = VACPGovernedAgent(
    name="researcher_agent",
    model="gemini-1.5-pro",
    instruction="""
    You are a Market Researcher.
    Your goal is to find the latest news and data using the search tools provided.
    Provide concise summaries of your findings.
    """,
    tools=[search_market_news],
    description="Researcher Agent: Fetches market news and data."
)

def create_researcher_agent(model_client=None):
    """
    Legacy factory for backward compatibility if needed,
    but we prefer using the instance 'researcher_agent' directly.
    """
    return researcher_agent
