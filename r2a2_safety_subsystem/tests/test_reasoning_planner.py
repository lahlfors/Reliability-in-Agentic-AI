"""
Unit tests for the full implementation of the ReasoningPlanner.
"""

import pytest
from unittest.mock import patch
from r2a2.components.reasoning_planner import ReasoningPlanner

@pytest.fixture
def planner():
    """Provides a ReasoningPlanner instance for testing."""
    return ReasoningPlanner()

def test_prompt_construction(planner):
    """
    Tests that the _construct_prompt method builds a correct and detailed prompt.
    """
    belief_state = {
        "task_instruction": "Analyze Q2 earnings.",
        "observations": {"report_status": "available"}
    }
    relevant_memories = [
        {"state": {"task_instruction": "Analyze Q1 earnings."}}
    ]

    prompt = planner._construct_prompt(belief_state, relevant_memories)

    assert "Analyze Q2 earnings" in prompt
    assert '"report_status": "available"' in prompt
    assert "Analyze Q1 earnings" in prompt
    assert "Example Output Format" in prompt

def test_generate_plans_successful_parsing(planner):
    """
    Tests that the planner can successfully call the simulated LLM and parse
    its valid JSON response.
    """
    belief_state = {"task_instruction": "Do something."}
    relevant_memories = []

    plans = planner.generate_plans(belief_state, relevant_memories)

    assert isinstance(plans, list)
    assert len(plans) == 2
    assert plans[0][0]["tool_name"] == "search_web"
    assert plans[1][0]["explanation"] == "Alternatively, start by reading internal documentation on market analysis."

@patch("r2a2.components.reasoning_planner.ReasoningPlanner._call_llm_simulation")
def test_generate_plans_invalid_json_response(mock_llm_call, planner, caplog):
    """
    Tests that the planner handles a non-JSON response from the LLM gracefully.
    """
    mock_llm_call.return_value = "This is not JSON."

    belief_state = {"task_instruction": "Do something."}
    relevant_memories = []

    plans = planner.generate_plans(belief_state, relevant_memories)

    assert plans == []
    assert "Failed to decode LLM response as JSON" in caplog.text

@patch("r2a2.components.reasoning_planner.ReasoningPlanner._call_llm_simulation")
def test_generate_plans_malformed_json_structure(mock_llm_call, planner, caplog):
    """
    Tests that the planner handles a JSON response with an incorrect structure.
    """
    mock_llm_call.return_value = '{"wrong_key": "some_value"}'

    belief_state = {"task_instruction": "Do something."}
    relevant_memories = []

    plans = planner.generate_plans(belief_state, relevant_memories)

    assert plans == []
    # No specific error for wrong key, but it should return an empty list.

    # Test case where candidate_plans is not a list
    mock_llm_call.return_value = '{"candidate_plans": "not-a-list"}'
    plans = planner.generate_plans(belief_state, relevant_memories)
    assert plans == []
    assert "LLM response for 'candidate_plans' was not a list" in caplog.text