import os
from typing import Dict, Any

class BrokerageTool:
    def __init__(self, authorized: bool = False):
        # In a real ZSP architecture, we would check if the current process/identity
        # has the required IAM role. Here we simulate it with an environment variable
        # that only the ExecutorAgent should have.
        self.authorized = authorized or (os.getenv("HAS_BROKERAGE_ACCESS") == "true")

    def execute_order(self, action: str, ticker: str, amount: float) -> str:
        """
        Executes a trade order on the brokerage platform.
        This tool is strictly gated by Zero Standing Privileges (ZSP).

        Args:
            action: 'buy' or 'sell'.
            ticker: Stock symbol.
            amount: Amount in USD.
        """
        if not self.authorized:
            return "PERMISSION DENIED: Identity lacks 'roles/brokerage.trader' permission. execution_order failed."

        # Mock Execution
        return f"SUCCESS: Order executed. {action.upper()} {ticker} for ${amount}."

    def get_portfolio(self) -> Dict[str, Any]:
        """Retrieves current portfolio holdings."""
        if not self.authorized:
             return {"error": "PERMISSION DENIED"}

        return {
            "cash": 100000.0,
            "holdings": {"AAPL": 50, "GOOGL": 20}
        }
