import logging
import sys
import unittest
from unittest.mock import MagicMock, patch

# Configure logging to see output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyRefactor")

# We need to mock dependencies that might fail during import if not in a full environment
# especially google.adk.agents.LlmAgent if it tries to validate models or creds
# However, VACPGovernedAgent inherits from it.

# Let's try to import the agent class.
# We might need to set PYTHONPATH in the run command.

try:
    from financial_advisor.agent import VACPGovernedAgent
except ImportError as e:
    # If import fails, we might need to mock LlmAgent first?
    # Or just rely on the environment being set up correctly.
    # The sandbox should have the files.
    logger.error(f"Failed to import VACPGovernedAgent. Ensure PYTHONPATH includes financial-advisor/. Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class TestCyberneticGovernance(unittest.TestCase):

    def setUp(self):
        # Patch LlmAgent.__init__ to avoid needing real API keys or model names
        self.patcher = patch('google.adk.agents.LlmAgent.__init__', return_value=None)
        self.mock_super_init = self.patcher.start()

        # Instantiate agent
        self.agent = VACPGovernedAgent()

    def tearDown(self):
        self.patcher.stop()

    def test_safe_trade(self):
        logger.info("\n--- Test: Safe Trade (Low Risk) ---")
        payload = {"action": "execute_trade", "parameters": {"amount": 1000}}
        result = self.agent.execute_governance_check(payload)
        self.assertIsNone(result, "Safe trade should be allowed")

    def test_high_value_trade_consensus(self):
        logger.info("\n--- Test: High Value Trade (Policy Block) ---")
        # Capstone Rule: > 50,000 is STRICTLY FORBIDDEN.
        payload = {"action": "execute_trade", "parameters": {"amount": 60000}}
        result = self.agent.execute_governance_check(payload)
        self.assertIsNotNone(result)
        self.assertIn("exceeds limit of $50,000", result)

    def test_critical_trade_human(self):
        logger.info("\n--- Test: Critical Trade (Policy Block) ---")
        # Capstone Rule: > 50,000 is STRICTLY FORBIDDEN, so > 2M is also blocked.
        payload = {"action": "execute_trade", "parameters": {"amount": 2000000}}
        result = self.agent.execute_governance_check(payload)
        self.assertIsNotNone(result)
        self.assertIn("exceeds limit of $50,000", result)

    def test_policy_violation(self):
        logger.info("\n--- Test: Policy Violation (Data Exfiltration) ---")
        payload = {"action": "export_data", "parameters": {"destination": "external_email"}}
        result = self.agent.execute_governance_check(payload)
        self.assertIsNotNone(result)
        self.assertIn("BLOCK: Policy Violation", result)

    def test_semantic_verifier_violation(self):
        logger.info("\n--- Test: Semantic Verifier (ShieldGemma) ---")
        # "drop table" is in the blacklist
        payload = {"action": "execute_python_code", "parameters": {"code": "cursor.execute('DROP TABLE users')"}}
        result = self.agent.execute_governance_check(payload)
        self.assertIsNotNone(result)
        self.assertIn("BLOCK: Semantic Verifier", result)

if __name__ == "__main__":
    unittest.main()
