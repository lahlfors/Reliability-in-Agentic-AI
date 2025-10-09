"""
Unit tests for the online Reflective Engine.
"""
import unittest
from unittest.mock import patch

# Import the new component
from metacognitive_control_subsystem.mcs.components.reflective_engine import ReflectiveEngine
# Import schemas needed for creating a mock agent state
from metacognitive_control_subsystem.mcs.api.schemas import AgentState, ProposedAction


class TestReflectiveEngine(unittest.TestCase):
    """
    Tests for the ReflectiveEngine component.
    """

    def setUp(self):
        """Set up the test case."""
        self.reflective_engine = ReflectiveEngine()
        self.mock_agent_state = AgentState(
            goal="Test goal",
            plan=["Step 1", "Step 2"],
            proposed_action=ProposedAction(
                tool_name="test_tool",
                parameters={"param1": "value1"}
            )
        )

    def test_run_reflection_self_critique_mode(self):
        """
        Test the run_reflection method in 'self-critique' mode.
        """
        mode = "self-critique"
        result = self.reflective_engine.run_reflection(mode, self.mock_agent_state)

        # Assert that the feedback is a dictionary and contains the expected key
        self.assertIsInstance(result, dict)
        self.assertIn("reflective_feedback", result)
        # Check if the mock response for this mode is present
        self.assertIn("inefficient", result["reflective_feedback"])

    def test_run_reflection_adversarial_simulation_mode(self):
        """
        Test the run_reflection method in 'adversarial-simulation' mode.
        """
        mode = "adversarial-simulation"
        result = self.reflective_engine.run_reflection(mode, self.mock_agent_state)

        # Assert that the feedback is a dictionary and contains the expected key
        self.assertIsInstance(result, dict)
        self.assertIn("reflective_feedback", result)
        # Check if the mock response for this mode is present
        self.assertIn("Vulnerability identified", result["reflective_feedback"])

    def test_run_reflection_unsupported_mode_raises_error(self):
        """
        Test that an unsupported reflection mode raises a ValueError.
        """
        with self.assertRaises(ValueError):
            self.reflective_engine.run_reflection("unsupported_mode", self.mock_agent_state)


if __name__ == '__main__':
    unittest.main()