import unittest
from vacp.goa import GoverningOrchestratorAgent
from vacp.schemas import AgentAction, GOADecision

class TestVACP(unittest.TestCase):
    def setUp(self):
        self.goa = GoverningOrchestratorAgent(agent_id="financial_coordinator")

    def test_ans_registry(self):
        # Verify the agent exists in ANS
        identity = self.goa.gateway.ans.resolve_agent("financial_coordinator")
        self.assertIsNotNone(identity)
        self.assertEqual(identity.risk_tier, "High")

    def test_goa_track_decision(self):
        # Test a low risk action
        action = AgentAction(tool_name="data_analyst", parameters={})
        decision = self.goa.process_request(action, plan_context="analyze market data")
        self.assertEqual(decision.decision, "TRACK")

    def test_goa_monitor_decision(self):
        # Test a medium risk action
        action = AgentAction(tool_name="execute_python_code", parameters={})
        decision = self.goa.process_request(action, plan_context="run calc")
        # Python code might trigger MONITOR or QUARANTINE depending on Janus
        # In mock implementation:
        # AgentGuard returns 0.05 for execute_python_code
        # Janus returns "Vulnerability: Code injection..."
        # So it should be QUARANTINE
        self.assertEqual(decision.decision, "QUARANTINE")

    def test_goa_quarantine_decision(self):
        # Test a high risk action without context (Janus violation)
        action = AgentAction(tool_name="place_order", parameters={})
        decision = self.goa.process_request(action, plan_context="just buy it")
        # Janus checks for "analysis" in context. "just buy it" fails.
        self.assertEqual(decision.decision, "QUARANTINE")

    def test_goa_success_decision(self):
        # Test a high risk action WITH context
        action = AgentAction(tool_name="place_order", parameters={})
        decision = self.goa.process_request(action, plan_context="analysis completed, buy now")
        # Janus passes.
        # AgentGuard returns 0.15 for place_order + High Risk.
        # UCF Control 013: limit is 0.05 for High Risk. 0.15 > 0.05 -> Fail.
        # So it should be QUARANTINE anyway based on P_failure.
        self.assertEqual(decision.decision, "QUARANTINE")

    def test_kill_switch(self):
        self.goa.gateway.activate_kill_switch()
        with self.assertRaises(PermissionError):
            self.goa.gateway.intercept_and_validate("financial_coordinator", AgentAction(tool_name="data_analyst", parameters={}))

if __name__ == '__main__':
    unittest.main()
