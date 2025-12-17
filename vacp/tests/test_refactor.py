import unittest
import json
import os
from unittest.mock import MagicMock, patch
from vacp.state_manager import FileBasedStateManager
from vacp.goa import GoverningOrchestratorAgent
from vacp.ecbf import ECBFGovernor
from vacp.system4 import FinancialState, RealTimeMarketModel
from vacp.schemas import AgentAction, OperationalConstraints

class TestRefactor(unittest.TestCase):

    def setUp(self):
        self.test_state_file = "test_vacp_state.json"
        # Ensure clean state file
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)

    def tearDown(self):
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)

    def test_goa_state_persistence(self):
        """Verify GOA persists state to file."""
        manager = FileBasedStateManager(self.test_state_file)

        # 1. Initialize GOA with this manager
        # Reset singleton logic for test (hacky but needed for singleton testing)
        GoverningOrchestratorAgent._instance = None
        goa = GoverningOrchestratorAgent(agent_card_path="non_existent.json", state_manager=manager)

        # 2. Trigger Kill Switch
        goa.activate_kill_switch("Test Reason")

        # 3. Create NEW instance (simulating restart)
        GoverningOrchestratorAgent._instance = None
        new_manager = FileBasedStateManager(self.test_state_file)
        new_goa = GoverningOrchestratorAgent(agent_card_path="non_existent.json", state_manager=new_manager)

        active, reason = new_goa.is_quarantined()
        self.assertTrue(active)
        self.assertEqual(reason, "Test Reason")

    def test_ecbf_dynamic_limits(self):
        """Verify ECBF uses limits from constraints object."""
        governor = ECBFGovernor()
        state = FinancialState(10_000_000.0, 500_000.0, 0.2, 1.0)
        action = AgentAction(tool_name="place_order", parameters={})

        # Constraint with LOW limit ($400k) - Current exposure is 500k, so h is negative immediately
        constraints = OperationalConstraints(
            max_autonomy_level=1,
            risk_limits={"max_exposure": 400_000.0}
        )

        is_safe, reason, metrics = governor.check_safety(state, action, constraints)

        self.assertFalse(is_safe)
        self.assertEqual(metrics["limit_used"], 400_000.0)
        self.assertLess(metrics["h"], 0) # Already violated

    def test_real_time_model_fallback(self):
        """Verify RealTimeMarketModel works with mocked yfinance logic."""
        model = RealTimeMarketModel()

        # Directly mock the internal method that fetches data
        # This bypasses the need to patch the missing 'yf' module
        with patch.object(model, '_fetch_real_volatility', return_value=0.3):
             state = FinancialState(10_000_000.0, 500_000.0, 0.1, 1.0) # Internal vol low (0.1)
             action = AgentAction(tool_name="wait", parameters={})

             next_state = model.predict_next_state(state, action)

             # Drift should be higher due to VIX=0.3 override
             # Drift = 500k * 0.3 * 0.1 * 1.0 = 15k
             expected_drift = 500_000.0 * 0.3 * 0.1
             actual_drift = next_state.risk_exposure - state.risk_exposure

             self.assertAlmostEqual(actual_drift, expected_drift, delta=100.0)

if __name__ == '__main__':
    unittest.main()
