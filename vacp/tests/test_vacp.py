import unittest
from unittest.mock import MagicMock
from vacp.goa import GoverningOrchestratorAgent
from vacp.gateway import gateway, vacp_enforce
from vacp.schemas import AgentAction
from vacp.processor import VACPSpanProcessor
from opentelemetry.sdk.trace import ReadableSpan
import opentelemetry.trace as trace

class TestVACP(unittest.TestCase):
    def setUp(self):
        self.goa = GoverningOrchestratorAgent()
        self.goa.reset()
        self.processor = VACPSpanProcessor()

    def test_ans_registry(self):
        # Access ANS via Gateway singleton
        identity = gateway.ans.resolve_agent("financial_coordinator")
        self.assertIsNotNone(identity)
        self.assertEqual(identity.risk_tier, "High")

    def test_goa_activation(self):
        # Test direct activation
        self.goa.activate_kill_switch("Test Reason")
        active, reason = self.goa.is_quarantined()
        self.assertTrue(active)
        self.assertEqual(reason, "Test Reason")

    def test_processor_safe_reasoning(self):
        # Simulate a safe reasoning span
        mock_span = MagicMock(spec=ReadableSpan)
        mock_span.name = "gen_ai.reasoning"
        mock_span.attributes = {
            "gen_ai.span.type": "reasoning",
            "gen_ai.content.completion": "I will analyze the data using python to calculate fibonacci."
        }

        self.processor.on_end(mock_span)

        # Verify GOA is NOT quarantined
        active, _ = self.goa.is_quarantined()
        self.assertFalse(active)

    def test_processor_unsafe_reasoning(self):
        # Simulate unsafe reasoning span
        mock_span = MagicMock(spec=ReadableSpan)
        mock_span.name = "gen_ai.reasoning"
        mock_span.attributes = {
            "gen_ai.span.type": "reasoning",
            "gen_ai.content.completion": "I will buy AAPL immediately without any analysis."
        }

        self.processor.on_end(mock_span)

        # Verify GOA IS quarantined
        active, reason = self.goa.is_quarantined()
        self.assertTrue(active)
        self.assertIn("P(fail)", reason)

    def test_gateway_enforcement(self):
        # 1. Safe State
        self.goa.reset()

        # Mock ANS to allow test tool
        with unittest.mock.patch('vacp.gateway.AgentNameService') as MockANS:
            instance = MockANS.return_value
            instance.resolve_agent.return_value.authorized_tools = ["test_tool"]
            instance.resolve_agent.return_value.risk_tier = "High"

            # Temporarily replace ANS
            original_ans = gateway.ans
            gateway.ans = instance

            # Temporarily override Agent Card on Gateway to allow test_tool
            original_card = gateway.card
            # Create a mock card or just set constraints
            mock_card = MagicMock()
            mock_card.constraints.tools_allowed = ["test_tool"]
            mock_card.constraints.tools_denied = []
            gateway.card = mock_card
            # Update internal sets
            gateway.allowed_tools = {"test_tool"}
            gateway.denied_tools = set()

            try:
                @vacp_enforce
                def test_tool():
                    return "OK"

                self.assertEqual(test_tool(), "OK")

                # 2. Quarantine State
                self.goa.activate_kill_switch("Violation")
                result = test_tool()
                self.assertIn("Kill-switch is active", result)

            finally:
                gateway.ans = original_ans
                gateway.card = original_card
                if original_card:
                    gateway.allowed_tools = set(original_card.constraints.tools_allowed)
                    gateway.denied_tools = set(original_card.constraints.tools_denied)
                else:
                    gateway.allowed_tools = set()
                    gateway.denied_tools = set()

if __name__ == '__main__':
    unittest.main()
