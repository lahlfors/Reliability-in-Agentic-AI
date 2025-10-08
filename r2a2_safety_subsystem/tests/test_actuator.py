"""
Unit tests for the full implementation of the Actuator module.
"""

import pytest
from r2a2.components.actuator import Actuator

@pytest.fixture
def actuator():
    """Provides an Actuator instance for testing."""
    return Actuator()

def test_format_action_valid(actuator):
    """
    Tests that a valid action dictionary is formatted correctly.
    """
    action = {
        "tool_name": "execute_shell",
        "parameters": {"command": "ls -l"},
        "explanation": "List files in the current directory."
    }

    formatted = actuator.format_action(action)

    expected = {
        "tool_name": "execute_shell",
        "parameters": {"command": "ls -l"},
        "explanation": "List files in the current directory."
    }
    assert formatted == expected

def test_format_action_no_explanation(actuator):
    """
    Tests that an action without an explanation is also handled correctly.
    """
    action = {
        "tool_name": "read_file",
        "parameters": {"path": "/tmp/test.txt"},
    }

    formatted = actuator.format_action(action)

    expected = {
        "tool_name": "read_file",
        "parameters": {"path": "/tmp/test.txt"},
    }
    assert formatted == expected

def test_format_action_invalid_missing_tool_name(actuator):
    """
    Tests that an action missing the 'tool_name' key raises a ValueError.
    """
    action = {"parameters": {}}
    with pytest.raises(ValueError, match="Invalid action format. Must be a dict with 'tool_name' and 'parameters'."):
        actuator.format_action(action)

def test_format_action_invalid_missing_parameters(actuator):
    """
    Tests that an action missing the 'parameters' key raises a ValueError.
    """
    action = {"tool_name": "some_tool"}
    with pytest.raises(ValueError, match="Invalid action format. Must be a dict with 'tool_name' and 'parameters'."):
        actuator.format_action(action)

def test_format_action_invalid_parameters_type(actuator):
    """
    Tests that an action where 'parameters' is not a dict raises a ValueError.
    """
    action = {"tool_name": "some_tool", "parameters": "not_a_dict"}
    with pytest.raises(ValueError, match="Action 'parameters' must be a dictionary."):
        actuator.format_action(action)

def test_format_action_non_dict_action(actuator):
    """
    Tests that passing a non-dictionary as the action raises a ValueError.
    """
    with pytest.raises(ValueError, match="Invalid action format."):
        actuator.format_action("this is not a dict")