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
        self.assertIn("Decision made based on rule", response_json["justification"])

    def test_deliberate_endpoint_vetoes_dangerous_action(self):
        """
        Test that a dangerous action (delete_file) is vetoed.
        """
        # Configure the constraints to include NO_FILE_DELETION
        self.client.post("/configure/constraints", json=[{"name": "NO_FILE_DELETION", "description": "Prevent file deletion.", "budget": 0.0}])
        # Construct a request with a dangerous tool
        request_payload = {
            "agent_state": {
                "goal": "Delete temporary files.",
                "plan": ["Find temp files", "Delete them"],
                "proposed_action": {
                    "tool_name": "delete_file",
                    "parameters": {"file_path": "/tmp/test.txt"}
                }
            }
        }
        response = self.client.post("/deliberate", json=request_payload)

        # Assert the response is successful and the decision is VETO
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["decision"], "VETO")
        self.assertIn("Decision made based on rule", response_json["justification"])

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
