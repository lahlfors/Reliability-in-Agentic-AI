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
# This is necessary because the test environment has an inconsistent CWD.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# The new root agent is an instance of R2A2VettedFinancialAgent
from financial_advisor.agent import R2A2VettedFinancialAgent

# We still need the original LlmAgent class for type hinting in mocks
from google.adk.agents import LlmAgent


@patch("financial_advisor.agent.R2A2Client")
def test_r2a2_vetted_agent_happy_path(MockR2A2Client):
    """
    Tests the R2A2VettedFinancialAgent's happy path using mocks.

    This test ensures that:
    1. The R2A2 client is initialized and configured.
    2. The inner coordinator agent is called to get a plan.
    3. The plan is sent to the R2A2 client for vetting.
    4. The final output includes the approval message and the plan.
    """
    # --- Arrange ---

    # 1. Mock the R2A2Client instance and its methods
    mock_r2a2_instance = MockR2A2Client.return_value
    mock_r2a2_instance.is_server_ready.return_value = True
    mock_r2a2_instance.configure_constraints.return_value = True

    # Simulate a successful "ACTION_APPROVED" response from the R2A2 subsystem
    mock_r2a2_instance.vet_action.return_value = {
        "status": "ACTION_APPROVED",
        "action": {}, # Not used in this logic, but part of the real response
        "explanation": "The proposed plan is within acceptable risk parameters."
    }

    # 2. Mock the inner financial_coordinator agent
    # We remove `spec=LlmAgent` because the real LlmAgent does not have a .run() method.
    # The test is focused on the wrapper's logic, so this is an acceptable simplification.
    mock_coordinator_agent = MagicMock()

    # Define the mock output of the financial coordinator
    mock_plan = (
        "1. Buy 100 shares of GOOG.\n"
        "2. Set a stop-loss order at -5%."
    )
    mock_coordinator_agent.run.return_value = mock_plan

    # 3. Instantiate the agent-under-test with the mocked components
    # The R2A2VettedFinancialAgent will receive the mocked client instance
    vetted_agent = R2A2VettedFinancialAgent(
        coordinator_agent=mock_coordinator_agent,
        r2a2_client=mock_r2a2_instance
    )

    # --- Act ---

    # Run the agent with a sample input
    final_output = vetted_agent.run(inputs={"query": "Give me a stock plan."})

    # --- Assert ---

    # Verify that the inner coordinator was called correctly
    mock_coordinator_agent.run.assert_called_once_with({"query": "Give me a stock plan."})

    # Verify that the R2A2 client was called to vet the plan
    mock_r2a2_instance.vet_action.assert_called_once()
    # Check that the plan from the coordinator was passed to the vet_action method
    call_args, _ = mock_r2a2_instance.vet_action.call_args
    assert call_args[1]["proposed_plan"] == mock_plan

    # Verify the final output is correctly formatted
    assert "PLAN APPROVED BY SAFETY SUBSYSTEM" in final_output
    assert "The proposed plan is within acceptable risk parameters." in final_output
    assert mock_plan in final_output


@patch("financial_advisor.agent.R2A2Client")
def test_r2a2_vetted_agent_rejection_path(MockR2A2Client):
    """
    Tests the R2A2VettedFinancialAgent's rejection path.
    """
    # --- Arrange ---
    mock_r2a2_instance = MockR2A2Client.return_value
    mock_r2a2_instance.is_server_ready.return_value = True

    # Simulate a "DEFER_TO_HUMAN" response
    mock_r2a2_instance.vet_action.return_value = {
        "status": "DEFER_TO_HUMAN",
        "action": None,
        "explanation": "The plan involves highly volatile assets, exceeding risk budget."
    }

    mock_coordinator_agent = MagicMock()
    mock_coordinator_agent.run.return_value = "A very risky plan."

    vetted_agent = R2A2VettedFinancialAgent(
        coordinator_agent=mock_coordinator_agent,
        r2a2_client=mock_r2a2_instance
    )

    # --- Act ---
    final_output = vetted_agent.run(inputs={"query": "Give me a risky plan."})

    # --- Assert ---
    assert "PLAN REJECTED BY SAFETY SUBSYSTEM" in final_output
    assert "exceeding risk budget" in final_output
    assert "A very risky plan." not in final_output # The original plan should not be shown