from typing import Dict, Any
from finguard.governance.policy_engine import OPAEngine

class ComplianceTool:
    def __init__(self):
        self.opa = OPAEngine()

    def validate_proposed_trade(self, action: str, ticker: str, amount: float, esg_score: int = 100) -> Dict[str, Any]:
        """
        Validates a proposed trade action against the corporate risk policy (OPA).

        Args:
            action: The action to take (buy/sell).
            ticker: The stock ticker symbol.
            amount: The dollar amount of the trade.
            esg_score: The ESG score of the asset (default 100).

        Returns:
            A dictionary containing 'allowed' (bool) and 'violations' (list of strings).
        """
        result = self.opa.validate_trade(action, ticker, amount, esg_score)
        return {
            "allowed": result.allowed,
            "violations": result.violations,
            "status": "APPROVED" if result.allowed else "DENIED"
        }
