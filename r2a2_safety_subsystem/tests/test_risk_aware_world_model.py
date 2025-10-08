"""
Unit tests for the full implementation of the RiskAwareWorldModel.
"""

import pytest
from r2a2.components.risk_aware_world_model import RiskAwareWorldModel

@pytest.fixture
def world_model():
    """Provides a RiskAwareWorldModel instance for testing."""
    return RiskAwareWorldModel()

@pytest.fixture
def current_state():
    """Provides a sample current_state dictionary."""
    return {
        "tick": 10,
        "task_instruction": "Evaluate market conditions.",
    }

def test_evaluate_plan_web_search(world_model, current_state):
    """
    Tests that a plan involving a web search is assigned the correct
    reward and cost profile.
    """
    plan = [{"tool_name": "search_web", "parameters": {"query": "tech stocks"}}]

    reward, costs = world_model.evaluate_plan(plan, current_state)

    assert reward == 1.0
    assert costs["resource_usage"] == 0.1
    assert costs["tool_misuse"] == 0.0
    assert costs["privacy_leak"] == 0.0

def test_evaluate_plan_execute_code(world_model, current_state):
    """
    Tests that a plan involving code execution is assigned a high
    'tool_misuse' cost.
    """
    plan = [{"tool_name": "execute_code", "parameters": {"code": "print(1)"}}]

    reward, costs = world_model.evaluate_plan(plan, current_state)

    assert reward == 1.0
    assert costs["tool_misuse"] == 0.5
    assert costs["resource_usage"] == 0.0

def test_evaluate_plan_internal_docs(world_model, current_state):
    """
    Tests that a plan involving internal docs is assigned a 'privacy_leak' cost.
    """
    plan = [{"tool_name": "read_internal_docs", "parameters": {"topic": "security"}}]

    reward, costs = world_model.evaluate_plan(plan, current_state)

    assert reward == 1.0
    assert costs["privacy_leak"] == 0.2
    assert costs["tool_misuse"] == 0.0

def test_evaluate_empty_plan(world_model, current_state):
    """
    Tests that an empty plan results in zero reward and costs.
    """
    plan = []
    reward, costs = world_model.evaluate_plan(plan, current_state)

    assert reward == 0.0
    assert costs == {}

def test_transition_prediction_structure(world_model, current_state):
    """
    Tests that the _predict_transition method returns a correctly
    structured next state.
    """
    action = {"tool_name": "any_tool", "parameters": {}}
    next_state = world_model._predict_transition(current_state, action)

    assert "last_action_outcome" in next_state
    assert next_state["last_action_outcome"]["status"] == "success"
    assert "The tool 'any_tool' was executed successfully" in next_state["last_action_outcome"]["description"]
    # Ensure original state is preserved
    assert next_state["tick"] == 10