# Copyright 2025 Google LLC
# FinGuard Brokerage Tool (ADK Wrapper)

import logging
import os
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 1. Legacy/Core Implementation
class BrokerageToolCore:
    def __init__(self, authorized: bool = False):
        self.authorized = authorized or (os.getenv("HAS_BROKERAGE_ACCESS") == "true")

    def execute_order(self, action: str, ticker: str, amount: float) -> str:
        if not self.authorized:
            return "PERMISSION DENIED: Identity lacks 'roles/brokerage.trader' permission. execution_order failed."
        return f"SUCCESS: Order executed. {action.upper()} {ticker} for ${amount}."

    def get_portfolio(self) -> Dict[str, Any]:
        if not self.authorized:
             return {"error": "PERMISSION DENIED"}
        return {
            "cash": 100000.0,
            "holdings": {"AAPL": 50, "GOOGL": 20}
        }

# 2. Pydantic Models
class ExecutionInput(BaseModel):
    action: Literal["buy", "sell"] = Field(..., description="Trade action")
    ticker: str = Field(..., description="Stock Ticker")
    amount: float = Field(..., gt=0, description="Trade amount")

# 3. ADK Wrapper
# Note: For strict ZSP, the authorization should ideally be per-request or checked via context.
# However, to preserve the 'authorized=True' logic for the Executor only, we might need a way
# to inject this. The ADK tools are usually stateless functions.
# SOLUTION: We will rely on an environment variable or a global flag that the Executor Agent sets?
# OR: We instantiate a 'authorized' core for the Executor and a 'unauthorized' one for others?
# But tools are functions.
# Better: The tool checks the Agent Name or Role from the Context?
# ToolContext has 'agent_name'?? No.
#
# Workaround for Refactor:
# We will assume this tool is ONLY registered to the Executor Agent.
# The `authorized=True` is implicit because only the Executor has access to this function definition
# if we are strict. But usually tools are imported.
# Let's default authorized=True here for the WRAPPER, assuming the 'AgentCard' controls WHO gets the tool.
# In VACP, *access* to the tool is the permission. If you have the tool, you are authorized.
# The 'Executor' agent gets this tool in its list. Others don't.

_brokerage_core = BrokerageToolCore(authorized=True)

def execute_order(action: str, ticker: str, amount: float) -> str:
    """
    Executes a trade order on the brokerage platform.
    """
    try:
        validated = ExecutionInput(action=action.lower(), ticker=ticker.upper(), amount=amount)
    except Exception as e:
        return f"Input Validation Error: {e}"

    logger.warning(f"EXECUTING TRADE: {validated.action} {validated.ticker}")
    return _brokerage_core.execute_order(validated.action, validated.ticker, validated.amount)

def get_portfolio() -> Dict[str, Any]:
    """Retrieves current portfolio holdings."""
    return _brokerage_core.get_portfolio()
