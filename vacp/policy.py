from typing import Dict, Any
from .interfaces import PolicyEngine, PolicyResult, RiskLevel

class MockOPAPolicyEngine(PolicyEngine):
    """
    Simulates an Open Policy Agent (OPA) sidecar.
    In production, this would make an HTTP POST to localhost:8181/v1/data/...
    """

    def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        # Simulate Rego Logic
        action = context.get("action")
        params = context.get("parameters", {})

        # Policy 1: High Value Transactions require Consensus
        if action == "execute_trade" or action == "place_order": # Added place_order for compatibility
            amount = params.get("amount", 0)
            # Handle string amounts if necessary, though type hint says Dict[str, Any]
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                pass

            if amount > 1_000_000:
                return PolicyResult(
                    allowed=True, # Conditional allow
                    risk_level=RiskLevel.CRITICAL,
                    reasons=["High value trade detected"],
                    requirements=["consensus_required", "human_approval"]
                )
            elif amount > 50_000:
                return PolicyResult(
                    allowed=True,
                    risk_level=RiskLevel.HIGH,
                    reasons=["Significant trade volume"],
                    requirements=["consensus_required"]
                )

        # Policy 2: External Data Exfiltration
        if action == "export_data" and params.get("destination") == "external_email":
             return PolicyResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                reasons=["Data exfiltration to external email prohibited"],
                requirements=[]
            )

        # Default Allow
        return PolicyResult(allowed=True, risk_level=RiskLevel.LOW, reasons=[], requirements=[])
