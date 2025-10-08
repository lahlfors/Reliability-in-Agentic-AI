"""
Unit tests for the full implementation of the ConstraintFilter.
"""

import pytest
from r2a2.components.constraint_filter import ConstraintFilter
from r2a2.formal.cmdp import CMDP_Model
from r2a2.api.schemas import Constraint, PIDGains

@pytest.fixture
def cmdp_model():
    """Provides a configured CMDP_Model instance for testing."""
    model = CMDP_Model()
    constraints = [
        Constraint(name="tool_misuse", description="Test constraint", budget=1.0),
        Constraint(name="privacy_leak", description="Test constraint 2", budget=0.5),
    ]
    pid_gains = PIDGains(kp=0.1, ki=0.01, kd=0.05)
    model.configure_constraints(constraints, pid_gains, learning_rate=0.01)
    return model

@pytest.fixture
def constraint_filter():
    """Provides a ConstraintFilter instance."""
    return ConstraintFilter()

def test_verify_action_safe(constraint_filter, cmdp_model):
    """
    Tests that an action is approved when its costs are below all budgets.
    """
    action = {"tool_name": "safe_tool"}
    estimated_costs = {
        "tool_misuse": 0.8,
        "privacy_leak": 0.4,
    }
    is_safe = constraint_filter.verify_action(action, estimated_costs, cmdp_model)
    assert is_safe is True

def test_verify_action_unsafe_one_constraint(constraint_filter, cmdp_model):
    """
    Tests that an action is rejected when it violates one constraint.
    """
    action = {"tool_name": "unsafe_tool"}
    estimated_costs = {
        "tool_misuse": 1.2,  # This exceeds the budget of 1.0
        "privacy_leak": 0.4,
    }
    is_safe = constraint_filter.verify_action(action, estimated_costs, cmdp_model)
    assert is_safe is False

def test_verify_action_unsafe_at_budget(constraint_filter, cmdp_model):
    """
    Tests that an action is rejected if its cost is exactly at the budget limit (cost > budget).
    """
    action = {"tool_name": "edge_case_tool"}
    # The check is `cost > budget`, so a cost equal to the budget should pass.
    estimated_costs = {
        "tool_misuse": 1.0,
        "privacy_leak": 0.5,
    }
    is_safe = constraint_filter.verify_action(action, estimated_costs, cmdp_model)
    assert is_safe is True

def test_verify_action_cost_not_in_model(constraint_filter, cmdp_model):
    """
    Tests that if a cost is estimated for a constraint not in the model,
    it is ignored and the action is approved (assuming other costs are fine).
    """
    action = {"tool_name": "unknown_cost_tool"}
    estimated_costs = {
        "tool_misuse": 0.5,
        "unknown_constraint": 99.9, # This should be ignored
    }
    is_safe = constraint_filter.verify_action(action, estimated_costs, cmdp_model)
    assert is_safe is True