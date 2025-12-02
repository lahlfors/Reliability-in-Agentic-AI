"""
Actuators (Guardrails) for the Metacognitive Control Subsystem.
These components act as Reference Monitors, enforcing safety constraints
independently of the agent's logic.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class GuardrailActuator:
    """Base class for all guardrail actuators."""
    def verify(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Verifies if the action is safe.
        Raises a SecurityException if unsafe.
        """
        raise NotImplementedError

class SecurityException(Exception):
    """Raised when a guardrail is violated."""
    pass


class NetworkSandbox(GuardrailActuator):
    """
    Enforces that network requests are only made to whitelisted domains.
    Corresponds to Constraint 3 (STPA).
    """
    def __init__(self, whitelist: List[str] = None):
        self.whitelist = whitelist or ["google.com", "finance.yahoo.com", "api.market-data.com"]

    def verify(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        # Check if the tool is network-capable
        if action_name not in ["google_search", "fetch_url"]:
            return True

        url = parameters.get("query") if action_name == "google_search" else parameters.get("url")

        # If the tool is google_search, the underlying mechanism calls Google.
        # This is implicitly whitelisted.
        if action_name == "google_search":
             # We assume google_search only hits google.com.
             # If the query itself contained a URL to fetch, we'd check it.
             # But standard google_search tool usage is just a query string.
             return True

        # For explicit URL fetching tools:
        if url and isinstance(url, str) and (url.startswith("http") or "://" in url):
            try:
                domain = urlparse(url).netloc.lower()
                # Strict Suffix Matching to prevent subdomain bypasses
                is_allowed = False
                for allowed in self.whitelist:
                    allowed = allowed.lower()
                    if domain == allowed or domain.endswith("." + allowed):
                        is_allowed = True
                        break

                if not is_allowed:
                    raise SecurityException(f"Network Access Violation: Domain '{domain}' is not whitelisted.")
            except Exception as e:
                # Fail closed on parsing errors
                 raise SecurityException(f"Network Access Violation: Malformed URL or checking error: {e}")

        return True


class FinancialCircuitBreaker(GuardrailActuator):
    """
    Enforces daily drawdown limits.
    Corresponds to Constraint 1 (STPA).
    """
    def __init__(self, max_drawdown_percent: float = 0.02, initial_portfolio_value: float = 100000.0):
        self.max_drawdown = max_drawdown_percent
        self.initial_value = initial_portfolio_value
        self.current_value = initial_portfolio_value
        # In a real system, current_value would be fetched from a DB.

    def verify(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        if action_name != "place_order":
            return True

        action = parameters.get("action", "").upper()
        quantity = parameters.get("quantity", 0)
        price = parameters.get("price", 0.0)

        if action == "BUY":
            cost = quantity * price
            # Simplified Check: Do not allow spending more than X% of portfolio in one go?
            # Or track simulated loss?
            # Let's implement: "Cannot Execute a trade that would risk > 2% of equity".
            # Assuming worst case 100% loss on this trade.
            risk_amount = cost
            allowed_risk = self.current_value * self.max_drawdown

            if risk_amount > allowed_risk:
                raise SecurityException(
                    f"Financial Circuit Breaker: Order risk (${risk_amount}) exceeds daily limit (${allowed_risk})."
                )

        return True

class ResourceLimiter(GuardrailActuator):
    """
    Prevents infinite loops and excessive resource usage.
    Corresponds to Constraint 2 (STPA).
    """
    def verify(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        if action_name != "execute_python_code":
            return True

        script = parameters.get("script", "")

        # Static Analysis (Simulated)
        if "while True" in script:
            raise SecurityException("Resource Violation: Infinite loop construct detected.")

        if "import socket" in script or "import requests" in script:
             raise SecurityException("Resource Violation: Unauthorized network library import.")

        if len(script) > 10000:
             raise SecurityException("Resource Violation: Script too large.")

        return True

# Master Guardrail Controller
class GuardrailController:
    def __init__(self):
        self.actuators = [
            NetworkSandbox(),
            FinancialCircuitBreaker(),
            ResourceLimiter()
        ]

    def validate_action(self, action_name: str, parameters: Dict[str, Any]):
        """
        Runs all actuators. If any fail, raises SecurityException.
        """
        for actuator in self.actuators:
            actuator.verify(action_name, parameters)
