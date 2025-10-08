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


# The new root agent is an instance of R2A2VettedFinancialAgent
from financial_advisor.agent import R2A2VettedFinancialAgent, R2A2Client
from google.adk.agents import LlmAgent

# Tell pytest this is an async test file
pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
@patch("financial_advisor.agent.R2A2Client", spec=R2A2Client)
async def test_r2a2_vetted_agent_happy_path_async(MockR2A2Client):
    """
    Tests the R2A2VettedFinancialAgent's happy path asynchronously.
    """
    # --- Arrange ---

    # 1. Mock the R2A2Client instance and its async methods
    mock_r2a2_instance = MockR2A2Client.return_value
    mock_r2a2_instance.is_server_ready = AsyncMock(return_value=True)
    mock_r2a2_instance.configure_constraints = AsyncMock(return_value=True)
    mock_r2a2_instance.vet_action = AsyncMock(return_value={
        "status": "ACTION_APPROVED",
        "explanation": "The proposed plan is within acceptable risk parameters."
    })

    # 2. Mock the inner financial_coordinator agent and its async generator
    mock_coordinator_agent = MagicMock(spec=LlmAgent)
    mock_plan = "1. Buy 100 shares of GOOG.\n2. Set a stop-loss order at -5%."

    # Mock the async generator `run_async`
    async def mock_run_async(*args, **kwargs):
        yield {"output": mock_plan, "is_final": True}

    mock_coordinator_agent.run_async = mock_run_async

    # 3. Instantiate the agent-under-test
    vetted_agent = R2A2VettedFinancialAgent(
        name="test_agent",
        coordinator=mock_coordinator_agent,
        r2a2_client=mock_r2a2_instance
    )

    # --- Act ---
    final_output = ""
    async for event in vetted_agent._run_async_impl(inputs={"query": "Give me a stock plan."}):
        if event.get("is_final"):
            final_output = event.get("output")

    # --- Assert ---
    mock_r2a2_instance.vet_action.assert_awaited_once()
    assert "PLAN APPROVED BY SAFETY SUBSYSTEM" in final_output
    assert "The proposed plan is within acceptable risk parameters." in final_output
    assert mock_plan in final_output


@pytest.mark.asyncio
@patch("financial_advisor.agent.R2A2Client", spec=R2A2Client)
async def test_r2a2_vetted_agent_rejection_path_async(MockR2A2Client):
    """
    Tests the R2A2VettedFinancialAgent's rejection path asynchronously.
    """
    # --- Arrange ---
    mock_r2a2_instance = MockR2A2Client.return_value
    mock_r2a2_instance.is_server_ready = AsyncMock(return_value=True)
    mock_r2a2_instance.vet_action = AsyncMock(return_value={
        "status": "DEFER_TO_HUMAN",
        "explanation": "The plan involves highly volatile assets, exceeding risk budget."
    })

    mock_coordinator_agent = MagicMock(spec=LlmAgent)
    async def mock_run_async(*args, **kwargs):
        yield {"output": "A very risky plan.", "is_final": True}
    mock_coordinator_agent.run_async = mock_run_async

    vetted_agent = R2A2VettedFinancialAgent(
        name="test_agent",
        coordinator=mock_coordinator_agent,
        r2a2_client=mock_r2a2_instance
    )

    # --- Act ---
    final_output = ""
    async for event in vetted_agent._run_async_impl(inputs={"query": "Give me a risky plan."}):
        if event.get("is_final"):
            final_output = event.get("output")

    # --- Assert ---
    assert "PLAN REJECTED BY SAFETY SUBSYSTEM" in final_output
    assert "exceeding risk budget" in final_output
    assert "A very risky plan." not in final_output