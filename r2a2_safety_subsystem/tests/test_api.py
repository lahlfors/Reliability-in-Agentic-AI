"""
End-to-end tests for the R2A2 Subsystem API.

This test suite simulates a host agent interacting with the R2A2 FastAPI
server. It verifies that the core perception-action loop works correctly
with the new, fully implemented components.
"""

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app instance from the server module
from r2a2.api.server import app

# Create a TestClient instance
client = TestClient(app)

def test_full_decision_cycle_successful():
    """
    Tests a complete, successful perception-to-action cycle with the full components.
    1. Configure constraints.
    2. Call /perceive with a task.
    3. Call /getAction with the transaction ID.
    4. Verify the approved action is returned.
    """
    # 1. Configure the subsystem with all relevant constraints
    constraints_payload = [
        {"name": "tool_misuse", "description": "Prevents dangerous tool use.", "budget": 1.0},
        {"name": "resource_usage", "description": "Limits resource consumption.", "budget": 1.0},
        {"name": "privacy_leak", "description": "Prevents data leaks.", "budget": 1.0},
    ]
    response = client.post("/configure/constraints", json=constraints_payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    # 2. Call /perceive to initiate a decision cycle
    perceive_payload = {
        "task_instruction": "Analyze the latest market trends.",
        "observations": {"news_article": "Stocks are up today."},
    }
    response = client.post("/perceive", json=perceive_payload)
    assert response.status_code == 200
    perceive_data = response.json()
    assert "transaction_id" in perceive_data
    transaction_id = perceive_data["transaction_id"]

    # 3. Call /getAction to retrieve the vetted action
    response = client.get(f"/getAction?transaction_id={transaction_id}")
    assert response.status_code == 200
    action_data = response.json()

    # 4. Verify the response matches the new expected output from the full planner
    assert action_data["status"] == "ACTION_APPROVED"
    assert action_data["action"] is not None

    # This is the hardcoded action from the *full* ReasoningPlanner's LLM simulation
    expected_action = {
        "tool_name": "search_web",
        "parameters": {"query": "latest market trends"},
        "explanation": "First, search the web for current market trends to gather data."
    }
    assert action_data["action"] == expected_action

def test_get_action_with_invalid_transaction_id():
    """
    Tests that the /getAction endpoint returns a 404 for an unknown ID.
    """
    invalid_id = "this-id-does-not-exist"
    response = client.get(f"/getAction?transaction_id={invalid_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction ID not found."}

def test_unconfigured_system_still_runs():
    """
    Tests that the system can still process a request even if the
    /configure/constraints endpoint has not been called, using its defaults.
    """
    perceive_payload = {
        "task_instruction": "Perform a task on an unconfigured system.",
        "observations": {},
    }
    response = client.post("/perceive", json=perceive_payload)
    assert response.status_code == 200
    transaction_id = response.json()["transaction_id"]

    response = client.get(f"/getAction?transaction_id={transaction_id}")
    assert response.status_code == 200
    action_data = response.json()
    assert action_data["status"] == "ACTION_APPROVED"

def test_action_rejection_due_to_constraint_violation():
    """
    Tests that an action is correctly rejected if its estimated cost
    exceeds the configured budget.
    """
    # 1. Configure constraints with a low budget for 'tool_misuse'
    constraints_payload = [
        {"name": "tool_misuse", "description": "Test", "budget": 0.4}, # World model estimates 0.5 for execute_code
    ]
    response = client.post("/configure/constraints", json=constraints_payload)
    assert response.status_code == 200

    # 2. Call /perceive with a task that will generate a high-cost action.
    # We patch the planner to ensure it suggests the risky 'execute_code' action.
    from unittest.mock import patch
    risky_plan = [[{"tool_name": "execute_code", "parameters": {"code": "rm -rf /"}}]]

    with patch("r2a2.components.reasoning_planner.ReasoningPlanner.generate_plans", return_value=risky_plan):
        perceive_payload = {
            "task_instruction": "Delete all files.",
            "observations": {},
        }
        response = client.post("/perceive", json=perceive_payload)
        assert response.status_code == 200
        transaction_id = response.json()["transaction_id"]

    # 3. Call /getAction and verify the action was rejected.
    response = client.get(f"/getAction?transaction_id={transaction_id}")
    assert response.status_code == 200
    action_data = response.json()

    assert action_data["status"] == "DEFER_TO_HUMAN"
    assert action_data["action"] is None
    assert "rejected by the Constraint Filter" in action_data["explanation"]