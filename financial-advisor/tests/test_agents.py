# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test cases for the refactored Financial Advisor with R2A2 vetting."""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# HACK: Add the project root to the python path to allow imports to work.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# The new root agent is an instance of R2A2VettedFinancialAgent
from financial_advisor.agent import R2A2VettedFinancialAgent, R2A2Client
from google.adk.agents import LlmAgent


@patch("financial_advisor.agent.R2A2Client")
def test_r2a2_vetted_agent_happy_path(MockR2A2Client):
    """
    Tests the R2A2VettedFinancialAgent's happy path using mocks.
    """
    # --- Arrange ---

    # 1. Mock the R2A2Client instance and its methods
    # Use spec=R2A2Client to satisfy Pydantic's type validation.
    mock_r2a2_instance = MagicMock(spec=R2A2Client)
    mock_r2a2_instance.is_server_ready.return_value = True
    mock_r2a2_instance.configure_constraints.return_value = True
    mock_r2a2_instance.vet_action.return_value = {
        "status": "ACTION_APPROVED",
        "action": {},
        "explanation": "The proposed plan is within acceptable risk parameters."
    }

    # 2. Mock the inner financial_coordinator agent
    mock_coordinator_agent = MagicMock(spec=LlmAgent)
    mock_plan = "1. Buy 100 shares of GOOG.\n2. Set a stop-loss order at -5%."
    # The LlmAgent itself doesn't have a .run() method, but the wrapper expects one.
    # We add it to the mock for the purpose of testing the wrapper's logic.
    mock_coordinator_agent.run = MagicMock(return_value=mock_plan)

    # 3. Instantiate the agent-under-test with the mocked components and correct keywords
    vetted_agent = R2A2VettedFinancialAgent(
        name="test_agent",
        coordinator=mock_coordinator_agent,
        r2a2_client=mock_r2a2_instance
    )

    # --- Act ---
    final_output = vetted_agent.run(inputs={"query": "Give me a stock plan."})

    # --- Assert ---
    mock_coordinator_agent.run.assert_called_once_with({"query": "Give me a stock plan."})
    mock_r2a2_instance.vet_action.assert_called_once()
    call_args, _ = mock_r2a2_instance.vet_action.call_args
    assert call_args[1]["proposed_plan"] == mock_plan
    assert "PLAN APPROVED BY SAFETY SUBSYSTEM" in final_output
    assert "The proposed plan is within acceptable risk parameters." in final_output
    assert mock_plan in final_output


@patch("financial_advisor.agent.R2A2Client")
def test_r2a2_vetted_agent_rejection_path(MockR2A2Client):
    """
    Tests the R2A2VettedFinancialAgent's rejection path.
    """
    # --- Arrange ---
    mock_r2a2_instance = MagicMock(spec=R2A2Client)
    mock_r2a2_instance.is_server_ready.return_value = True
    mock_r2a2_instance.vet_action.return_value = {
        "status": "DEFER_TO_HUMAN",
        "action": None,
        "explanation": "The plan involves highly volatile assets, exceeding risk budget."
    }

    mock_coordinator_agent = MagicMock(spec=LlmAgent)
    mock_coordinator_agent.run = MagicMock(return_value="A very risky plan.")

    vetted_agent = R2A2VettedFinancialAgent(
        name="test_agent",
        coordinator=mock_coordinator_agent,
        r2a2_client=mock_r2a2_instance
    )

    # --- Act ---
    final_output = vetted_agent.run(inputs={"query": "Give me a risky plan."})

    # --- Assert ---
    assert "PLAN REJECTED BY SAFETY SUBSYSTEM" in final_output
    assert "exceeding risk budget" in final_output
    assert "A very risky plan." not in final_output