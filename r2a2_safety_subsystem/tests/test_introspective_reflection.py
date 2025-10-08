"""
Unit tests for the full implementation of the IntrospectiveReflection module.
"""

import pytest
from unittest.mock import patch
from r2a2.components.introspective_reflection import IntrospectiveReflection

@pytest.fixture
def reflection_module():
    """Provides an IntrospectiveReflection instance for testing."""
    return IntrospectiveReflection()

@pytest.fixture
def sample_trajectory():
    """Provides a sample trajectory for analysis."""
    return [
        {"state": {"task": "step 1"}, "action": "do_a"},
        {"state": {"task": "step 2"}, "action": "do_b", "outcome": "error"},
    ]

def test_analyze_trajectory_success(reflection_module, sample_trajectory):
    """
    Tests that a trajectory is successfully analyzed and a valid insight is returned.
    """
    insight = reflection_module.analyze_trajectory(sample_trajectory)

    assert isinstance(insight, dict)
    assert insight["type"] == "causal_discovery"
    assert "execute_code" in insight["hypothesis"]

def test_prompt_construction(reflection_module, sample_trajectory):
    """
    Tests that the analysis prompt is constructed correctly.
    """
    prompt = reflection_module._construct_analysis_prompt(sample_trajectory)

    assert "You are an AI agent's self-reflection and analysis core." in prompt
    assert '"task": "step 1"' in prompt
    assert '"outcome": "error"' in prompt
    assert "Example Output" in prompt

@patch("r2a2.components.introspective_reflection.IntrospectiveReflection._call_llm_simulation")
def test_analyze_trajectory_invalid_json(mock_llm_call, reflection_module, sample_trajectory, caplog):
    """
    Tests graceful failure when the LLM returns invalid JSON.
    """
    mock_llm_call.return_value = "not json"
    insight = reflection_module.analyze_trajectory(sample_trajectory)

    assert insight is None
    assert "Failed to decode LLM response as JSON" in caplog.text

@patch("r2a2.components.introspective_reflection.IntrospectiveReflection._call_llm_simulation")
def test_analyze_trajectory_malformed_insight(mock_llm_call, reflection_module, sample_trajectory, caplog):
    """
    Tests graceful failure when the insight object is not a dictionary.
    """
    mock_llm_call.return_value = '{"insight": "just a string"}'
    insight = reflection_module.analyze_trajectory(sample_trajectory)

    assert insight is None
    assert "LLM response for 'insight' was not a dictionary" in caplog.text

def test_analyze_empty_trajectory(reflection_module):
    """
    Tests that an empty trajectory results in no analysis and no insight.
    """
    insight = reflection_module.analyze_trajectory([])
    assert insight is None