"""
Unit tests for the TDD-aligned FastAPI server and its /deliberate endpoint.
"""
import unittest
from fastapi.testclient import TestClient

# Import the FastAPI app from the server module
from metacognitive_control_subsystem.mcs.api.server import app

# Import schemas for constructing test payloads
from metacognitive_control_subsystem.mcs.api.schemas import DeliberateRequest, AgentState, ProposedAction


class TestDeliberateAPI(unittest.TestCase):
    """
    Tests for the /deliberate endpoint and its integration with the
    DeliberationController.
    """

    def setUp(self):
        """Set up the test client."""
        self.client = TestClient(app)

    def test_deliberate_endpoint_approves_safe_action(self):
        """
        Test that a safe action is approved with an 'EXECUTE' decision.
        """
        # Construct a request with a safe tool
        request_payload = {
            "agent_state": {
                "goal": "Summarize the document.",
                "plan": ["Read the document", "Summarize it"],
                "proposed_action": {
                    "tool_name": "read_document",
                    "parameters": {"doc_id": "123"}
                }
            }
        }
        response = self.client.post("/deliberate", json=request_payload)

        # Assert the response is successful and the decision is EXECUTE
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["decision"], "EXECUTE")
        self.assertIn("approved by heuristic policy", response_json["justification"])

    def test_deliberate_endpoint_vetoes_dangerous_action(self):
        """
        Test that a dangerous action (execute_shell) is vetoed.
        """
        # Construct a request with a dangerous tool
        request_payload = {
            "agent_state": {
                "goal": "Delete temporary files.",
                "plan": ["Find temp files", "Delete them"],
                "proposed_action": {
                    "tool_name": "execute_shell",
                    "parameters": {"command": "rm -rf /tmp/*"}
                }
            }
        }
        response = self.client.post("/deliberate", json=request_payload)

        # Assert the response is successful and the decision is VETO
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["decision"], "VETO")
        self.assertIn("vetoed by default policy", response_json["justification"])

    def test_deliberate_endpoint_requests_revision_for_empty_plan(self):
        """
        Test that an empty plan triggers a 'REVISE' decision.
        """
        # Construct a request with an empty plan
        request_payload = {
            "agent_state": {
                "goal": "Figure out what to do.",
                "plan": [], # Empty plan
                "proposed_action": {
                    "tool_name": "think",
                    "parameters": {}
                }
            }
        }
        response = self.client.post("/deliberate", json=request_payload)

        # Assert the response is successful and the decision is REVISE
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["decision"], "REVISE")
        self.assertIn("plan is empty", response_json["justification"])

    def test_deliberate_endpoint_handles_invalid_payload(self):
        """
        Test that the endpoint returns a 422 Unprocessable Entity for a bad request.
        """
        # Construct a request with a missing required field ('proposed_action')
        invalid_payload = {
            "agent_state": {
                "goal": "This is a test."
                # Missing 'proposed_action'
            }
        }
        response = self.client.post("/deliberate", json=invalid_payload)

        # Assert that the status code is 422
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()