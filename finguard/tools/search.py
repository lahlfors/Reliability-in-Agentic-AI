# Copyright 2025 Google LLC
# FinGuard Search Tool (ADK Wrapper)

import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 1. Legacy/Core Implementation
class SearchToolCore:
    def search_market_news(self, query: str) -> str:
        """
        Searches for real-time market news.
        """
        # Mock Search
        return f"[MOCK SEARCH RESULT] Found 3 articles for '{query}': 1. Apple announces earnings... 2. Tech sector rallies... 3. Analyst upgrades AAPL."

# 2. Pydantic Models for Validation
class SearchInput(BaseModel):
    query: str = Field(..., description="The market topic to search for, e.g., 'AAPL news'")

# 3. ADK Wrapper
_search_core = SearchToolCore()

def search_market_news(query: str) -> str:
    """
    Searches for real-time market news using the FinGuard Search Tool.

    Args:
        query: The search query (e.g., "AAPL news").
    """
    # Runtime Validation (Defensive)
    try:
        validated = SearchInput(query=query)
    except Exception as e:
        return f"Input Validation Error: {e}"

    logger.info(f"Executing SearchTool with query: {validated.query}")
    return _search_core.search_market_news(validated.query)
