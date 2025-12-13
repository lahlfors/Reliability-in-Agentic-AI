import unittest
from unittest.mock import patch, MagicMock
import os
import json
import tempfile
from vacp.gateway import gateway as global_gateway
from vacp.goa import GoverningOrchestratorAgent

class TestGatewayIntegration(unittest.TestCase):
    def setUp(self):
        # Reset GOA Singleton
        GoverningOrchestratorAgent._instance = None

        # Mock MIMService to avoid GCP credential errors in ToolGateway init
        self.mim_patcher = patch('vacp.gateway.MIMService')
        self.MockMIM = self.mim_patcher.start()

        # Create a temp agent card
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.card_path = os.path.join(self.tmp_dir.name, "agent.json")
        self.card_data = {
             "card_version": "1.0",
             "agent_name": "TestAgent",
             "agent_version": "1.0",
             "provider": { "name": "Test", "address": "Test", "contact_email": "test@test.com" },
             "regulatory": { "intended_purpose": "Test", "high_risk_category": "none" },
             "constraints": {
                "max_autonomy_level": 1,
                "tools_allowed": ["allowed_tool"],
                "tools_denied": ["denied_tool"],
                "risk_limits": {}
             }
        }

        with open(self.card_path, "w") as f:
            json.dump(self.card_data, f)

        # Patch signature verification to pass
        self.signer_patcher = patch('vacp.c2pa.C2PASigner.verify_file')
        self.MockVerify = self.signer_patcher.start()
        self.MockVerify.return_value = True

    def tearDown(self):
        self.mim_patcher.stop()
        self.signer_patcher.stop()
        self.tmp_dir.cleanup()
        GoverningOrchestratorAgent._instance = None

    def test_fail_safe_blocking(self):
        """
        Verify that a denied tool is strictly blocked by the Gateway
        when the policy is loaded.
        """
        # Load the card into GOA
        self.goa = GoverningOrchestratorAgent(agent_card_path=self.card_path)

        # Ensure policy is propagated to global gateway
        # (This happens in GOA init via import, but we need to ensure the global instance is updated)
        # In vacp.goa we removed the circular import update.
        # In vacp.gateway.ToolGateway.__init__, it pulls from GOA.
        # But global_gateway is already instantiated at module level.
        # So we must manually update it or rely on a mechanism.
        # Ah, ToolGateway has:
        # if self.goa.agent_card: self.set_policy(self.goa.agent_card)
        # But global_gateway was instantiated BEFORE test setUp, so it has the OLD GOA instance (which is None/Empty).
        # We need to refresh the global gateway's policy or re-init it.

        global_gateway.goa = self.goa # Update to new GOA instance
        if self.goa.agent_card:
            global_gateway.set_policy(self.goa.agent_card)

        # Test Denied Tool
        with self.assertRaises(PermissionError) as cm:
            global_gateway.verify_access("denied_tool", {})
        self.assertIn("blocked by Agent Card policy", str(cm.exception))

        # Test Allowed Tool
        try:
            global_gateway.verify_access("allowed_tool", {})
        except PermissionError:
            self.fail("allowed_tool raised PermissionError unexpectedly!")

    def test_kill_switch_enforcement(self):
        """
        Verify that if GOA activates kill switch, Gateway blocks everything.
        """
        self.goa = GoverningOrchestratorAgent(agent_card_path=self.card_path)
        global_gateway.goa = self.goa

        self.goa.activate_kill_switch("Test Kill Switch")

        with self.assertRaises(PermissionError) as cm:
            global_gateway.verify_access("allowed_tool", {})
        self.assertIn("Kill-switch is active", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
