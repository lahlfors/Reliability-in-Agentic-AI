import unittest
from unittest.mock import MagicMock
from vacp.system4 import FinancialState
from vacp.ecbf import ECBFGovernor
from vacp.schemas import AgentAction

class TestAutonomousHedgeFund(unittest.TestCase):
    """
    Simulates the "Autonomous Hedge Fund" case study (Section 8 of the report).
    Scenario: Market Dip. Agent wants to "Buy the dip".
    Risk Limit: $1,000,000
    """

    def setUp(self):
        self.governor = ECBFGovernor()
        self.risk_limit = 1_000_000.0

    def test_standard_governance_failure(self):
        """
        Demonstrate that a standard "Relative Degree 1" check would FAIL to stop the agent.
        Standard check: Is current_exposure + trade < limit?
        """
        # Initial State: High exposure ($900k), High volatility
        state = FinancialState(
            portfolio_value=10_000_000.0,
            risk_exposure=900_000.0,
            market_volatility=0.5, # High volatility
            liquidity_score=1.0
        )

        # Action: Buy $50k worth of assets
        # Standard check: 900k + 50k = 950k < 1M. SAFE.
        trade_amount = 50_000.0
        projected_exposure = state.risk_exposure + trade_amount

        self.assertLess(projected_exposure, self.risk_limit,
                        "Standard governance should incorrectly deem this safe (Limit not hit yet)")

    def test_ecbf_intervention(self):
        """
        Demonstrate that ECBF correctly blocks the action due to semantic inertia / momentum.
        """
        # Initial State: Same as above. High exposure close to limit.
        state = FinancialState(
            portfolio_value=10_000_000.0,
            risk_exposure=900_000.0,
            market_volatility=0.8, # Very High volatility implies high drift/momentum
            liquidity_score=0.8    # Slightly lower liquidity increases effective risk
        )

        action = AgentAction(
            tool_name="place_order",
            parameters={"context": "Buying the dip to maximize returns."},
        )

        # Run ECBF Check
        is_safe, reason, metrics = self.governor.check_safety(state, action)

        # Assertions
        print(f"\nECBF Metrics: {metrics}")
        print(f"Reason: {reason}")

        # The logic in HeuristicFinancialWorldModel:
        # t=1: Exposure increases by trade (100k*slip) + drift.
        # Drift = 900k * 0.8 * 0.1 = 72k.
        # Trade = 100k * (1 + 0.2) = 120k.
        # New Exposure ~ 900 + 72 + 120 = 1092k. > 1M.
        # So h(t+1) will be negative.

        # Even if h(t=0) is positive (100k margin), the velocity is negative (risk increasing).
        # The ECBF should catch this.

        self.assertFalse(is_safe, "ECBF should block the action due to projected violation.")
        self.assertIn("ECBF Violation", reason)
        self.assertLess(metrics['ecbf_value'], 0)

    def test_safe_action(self):
        """
        Verify that a safe action (Hedging/Selling) is allowed.
        """
        state = FinancialState(
            portfolio_value=10_000_000.0,
            risk_exposure=900_000.0,
            market_volatility=0.5,
            liquidity_score=1.0
        )

        action = AgentAction(
            tool_name="place_order",
            parameters={"context": "Selling assets to hedge risk."}, # 'sell' implies reducing exposure
        )

        is_safe, reason, metrics = self.governor.check_safety(state, action)

        print(f"\nSafe Action Metrics: {metrics}")
        self.assertTrue(is_safe, "Hedging should be allowed.")

if __name__ == '__main__':
    unittest.main()
