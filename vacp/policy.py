from typing import Dict, Any, List
from .interfaces import PolicyEngine, PolicyResult, RiskLevel
import time

class MockOPAPolicyEngine(PolicyEngine):
    """
    Simulates an Open Policy Agent (OPA) sidecar.
    In production, this would make an HTTP POST to localhost:8181/v1/data/...
    """

    def __init__(self):
        # Stateful storage for Loophole/Velocity detection
        self.trade_history: List[Dict[str, Any]] = []

    def evaluate(self, context: Dict[str, Any]) -> PolicyResult:
        # Simulate Rego Logic
        action = context.get("action")
        params = context.get("parameters", {})

        # --- Capstone Rules ---

        if action == "execute_trade" or action == "place_order":
            try:
                # 1. Clean parameters (simulated Rego input processing)
                symbol = params.get("symbol", "").upper()
                amount = float(params.get("amount", 0))
                current_time = time.time()

                # Rule 3: Blacklist (LUNA)
                if symbol == "LUNA":
                    return PolicyResult(
                        allowed=False,
                        risk_level=RiskLevel.CRITICAL,
                        reasons=["Trading of asset 'LUNA' is blacklisted."],
                        requirements=[]
                    )

                # Rule 2: Exposure Limit (> $50,000)
                # Check single trade limit
                if amount > 50_000:
                    return PolicyResult(
                        allowed=False, # Capstone says "Blacklist" / "Forbidden", implied blocking
                        risk_level=RiskLevel.HIGH,
                        reasons=[f"Single trade amount ${amount} exceeds limit of $50,000"],
                        requirements=["consensus_required"] # In previous logic allowed with consensus, but Capstone implies forbidden.
                                                            # Requirement: "The governance layer must return a 403 Forbidden"
                                                            # So we set allowed=False
                    )

                # Rule 1 & 5: Velocity Limit & Loophole (Stateful)
                # Filter trades in last 60 seconds
                recent_trades = [
                    t for t in self.trade_history
                    if t['timestamp'] > current_time - 60
                ]

                # Velocity: Max 3 trades per minute
                if len(recent_trades) >= 3:
                     return PolicyResult(
                        allowed=False,
                        risk_level=RiskLevel.HIGH,
                        reasons=["Velocity Limit Exceeded: Max 3 trades per minute."],
                        requirements=[]
                    )

                # Loophole: Aggregate Exposure in last window > $50k?
                # "Agent splits a $100k trade into two $49k trades"
                # If sum of recent trades + current > 50k?
                # The requirement explicitly says "No single trade > $50,000 USD" for Rule 2.
                # But Test Case 5 "The Loophole" implies we must catch splitting.
                # Let's enforce an aggregate limit per minute or similar?
                # Or just detect the pattern.
                # Assuming "Exposure Limit" implies *exposure*, so aggregate.
                total_recent_volume = sum(t['amount'] for t in recent_trades)
                if total_recent_volume + amount > 50_000: # Strict aggregate limit? Or loose?
                    # The test case says "Splits $100k into two $49k".
                    # If limit is strictly $50k single trade, then 49+49=98 is valid under Rule 2.
                    # But "Stateful Governance" (Distinction) requires catching this.
                    # So we enforce an *Aggregate* limit of $50k/min (or similar heuristic).
                    return PolicyResult(
                        allowed=False,
                        risk_level=RiskLevel.HIGH,
                        reasons=[f"Aggregate exposure limit ($50k/min) exceeded. Current: {total_recent_volume + amount}"],
                        requirements=[]
                    )

                # If allowed, record trade
                self.trade_history.append({
                    "timestamp": current_time,
                    "amount": amount,
                    "symbol": symbol
                })

            except (ValueError, TypeError) as e:
                # Let Layer 1 handle strict type errors, but if it gets here, maybe block?
                pass

        # Policy: High Value Transactions (Legacy)
        # Kept for compatibility with verify_refactor.py if needed, but overridden by above for trades
        if action == "execute_trade" and params.get("amount", 0) > 1_000_000:
             return PolicyResult(
                    allowed=True,
                    risk_level=RiskLevel.CRITICAL,
                    reasons=["High value trade detected"],
                    requirements=["consensus_required", "human_approval"]
                )

        # Policy: External Data Exfiltration
        if action == "export_data" and params.get("destination") == "external_email":
             return PolicyResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                reasons=["Data exfiltration to external email prohibited"],
                requirements=[]
            )

        # Default Allow
        return PolicyResult(allowed=True, risk_level=RiskLevel.LOW, reasons=[], requirements=[])
