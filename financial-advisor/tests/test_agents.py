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

"""Asynchronous test cases for the refactored Financial Advisor."""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# HACK: Add the project root to the python path to allow imports to work.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Import the factory function and the classes needed for mocking.
from financial_advisor.agent import create_agent, R2A2Client, R2A2VettedFinancialAgent
from google.adk.agents import LlmAgent, InvocationContext

# Tell pytest this is an async test file
pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
@patch("financial_advisor.agent.R2A2Client", spec=R2A2Client)
@patch("financial_advisor.agent.LlmAgent", spec=LlmAgent)
async def test_r2a2_vetted_agent_happy_path_async(MockLlmAgent, MockR2A2Client):
    """
    Tests the R2A2VettedFinancialAgent's happy path using mocks.
    """
    # --- Arrange ---

    # 1. Configure the mocks that will be used when the agent is created.
    mock_r2a2_instance = MockR2A2Client.return_value
    mock_r2a2_instance.is_server_ready_async.return_value = True
    mock_r2a2_instance.configure_constraints_async.return_value = True
    mock_r2a2_instance.vet_action_async.return_value = {
        "status": "ACTION_APPROVED",
        "explanation": "The proposed plan is within acceptable risk parameters."
    }

    mock_coordinator_agent = MockLlmAgent.return_value
    mock_plan = "1. Buy 100 shares of GOOG.\n2. Set a stop-loss order at -5%."
    async def mock_run_async(*args, **kwargs):
        yield {"output": mock_plan, "is_final": True}
    mock_coordinator_agent.run_async = MagicMock(side_effect=mock_run_async)

    # 2. Call the factory function. It will create the agent using our mocks.
    vetted_agent = create_agent()

    # 3. Create a mock InvocationContext
    mock_ctx = MagicMock(spec=InvocationContext)
    mock_ctx.user_content = "Give me a stock plan."
    coordinator_inputs = {"query": mock_ctx.user_content}

    # --- Act ---
    final_output = ""
    async for event in vetted_agent._run_async_impl(ctx=mock_ctx):
        if event.get("is_final"):
            final_output = event.get("output")

    # --- Assert ---
    mock_coordinator_agent.run_async.assert_called_once_with(**coordinator_inputs)
    mock_r2a2_instance.vet_action_async.assert_awaited_once()
    assert "PLAN APPROVED BY SAFETY SUBSYSTEM" in final_output


@pytest.mark.asyncio
@patch("financial_advisor.agent.R2A2Client", spec=R2A2Client)
@patch("financial_advisor.agent.LlmAgent", spec=LlmAgent)
async def test_r2a2_vetted_agent_rejection_path_async(MockLlmAgent, MockR2A2Client):
    """
    Tests the R2A2VettedFinancialAgent's rejection path asynchronously.
    """
    # --- Arrange ---
    mock_r2a2_instance = MockR2A2Client.return_value
    mock_r2a2_instance.is_server_ready_async.return_value = True
    mock_r2a2_instance.vet_action_async.return_value = {
        "status": "DEFER_TO_HUMAN",
        "explanation": "The plan involves highly volatile assets, exceeding risk budget."
    }

    mock_coordinator_agent = MockLlmAgent.return_value
    async def mock_run_async(*args, **kwargs):
        yield {"output": "A very risky plan.", "is_final": True}
    mock_coordinator_agent.run_async = MagicMock(side_effect=mock_run_async)

    vetted_agent = create_agent()

    mock_ctx = MagicMock(spec=InvocationContext)
    mock_ctx.user_content = "Give me a risky plan."

    # --- Act ---
    final_output = ""
    async for event in vetted_agent._run_async_impl(ctx=mock_ctx):
        if event.get("is_final"):
            final_output = event.get("output")

    # --- Assert ---
    assert "PLAN REJECTED BY SAFETY SUBSYSTEM" in final_output
    assert "exceeding risk budget" in final_output