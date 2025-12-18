# Copyright 2025 Google LLC
# FinGuard Compliance Tool (ADK Wrapper)

import logging
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from finguard.governance.policy_engine import OPAEngine

logger = logging.getLogger(__name__)

# 1. Legacy/Core Implementation
class ComplianceToolCore:
    def __init__(self):
        # OPAEngine might require setup, we assume it works or mocks correctly.
        self.opa = OPAEngine()

    def validate_proposed_trade(self, action: str, ticker: str, amount: float, esg_score: int) -> Dict[str, Any]:
        result = self.opa.validate_trade(action, ticker, amount, esg_score)
        return {
            "allowed": result.allowed,
            "violations": result.violations,
            "status": "APPROVED" if result.allowed else "DENIED"
        }

# 2. Pydantic Models
class ComplianceInput(BaseModel):
    action: Literal["buy", "sell"] = Field(..., description="Trade action: 'buy' or 'sell'")
    ticker: str = Field(..., description="Stock Ticker, e.g. AAPL")
    amount: float = Field(..., gt=0, description="Trade amount in USD")
    esg_score: int = Field(default=100, ge=0, le=100, description="ESG Score (0-100)")

# 3. ADK Wrapper
_compliance_core = ComplianceToolCore()

def validate_proposed_trade(action: str, ticker: str, amount: float, esg_score: int = 100) -> Dict[str, Any]:
    """
    Validates a proposed trade action against the corporate risk policy (OPA).

    Args:
        action: The action to take (buy/sell).
        ticker: The stock ticker symbol.
        amount: The dollar amount of the trade.
        esg_score: The ESG score of the asset.
    """
    try:
        # Note: action comes in as string, pydantic validates enum
        validated = ComplianceInput(action=action.lower(), ticker=ticker.upper(), amount=amount, esg_score=esg_score)
    except Exception as e:
        return {"allowed": False, "violations": [f"Input Validation Error: {e}"], "status": "DENIED"}

    logger.info(f"Checking Compliance for {validated.ticker}...")
    return _compliance_core.validate_proposed_trade(
        validated.action, validated.ticker, validated.amount, validated.esg_score
    )
