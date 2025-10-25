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

from financial_advisor.agent import MCSVettedFinancialAgent
from financial_advisor.utils.mcs_client import MCSClient
from google.adk.agents import InvocationContext, RunConfig, LlmAgent
from google.adk.events.event import Event
from google.genai import types

# Tell pytest this is an async test file
pytest_plugins = ("pytest_asyncio",)

@pytest.mark.asyncio
@patch.object(LlmAgent, '_run_async_impl')
async def test_mcs_vetted_agent_happy_path_async(mock_run_async_impl):
    """
    Tests the MCSVettedFinancialAgent's happy path using mocks.
    """
    # --- Arrange ---
    mock_mcs_client = AsyncMock(spec=MCSClient)
    mock_mcs_client.is_server_ready_async.return_value = True
    mock_mcs_client.configure_constraints_async.return_value = True
    mock_mcs_client.deliberate_async.return_value = {
        "decision": "EXECUTE",
        "justification": "The proposed plan is within acceptable risk parameters."
    }

    vetted_agent = MCSVettedFinancialAgent(name="test_agent", mcs_client=mock_mcs_client, model="gemini-1.5-pro")

    mock_ctx = MagicMock(spec=InvocationContext)
    mock_ctx.user_content = "Give me a stock plan."
    mock_ctx.agent_states = {}
    mock_ctx.invocation_id = "test_id"
    mock_ctx.agent = vetted_agent
    mock_ctx.run_config = RunConfig()
    mock_ctx.session = MagicMock()
    mock_ctx.session.events = []
    mock_ctx.branch = "test_branch"
    mock_ctx.context_cache_config = None
    mock_ctx.end_invocation = False

    async def mock_run_async_impl_gen(*args, **kwargs):
        yield Event(
            author="test",
            content=types.Content(parts=[types.Part(text="1. Buy 100 shares of GOOG.\n2. Set a stop-loss order at -5%.")]),
            id="test",
            invocation_id=mock_ctx.invocation_id,
            partial=False
        )
    mock_run_async_impl.side_effect = mock_run_async_impl_gen

    # --- Act ---
    final_output = ""
    async for event in vetted_agent._run_async_impl(ctx=mock_ctx):
        if not event.partial:
            final_output = event.content.parts[0].text

    # --- Assert ---
    mock_mcs_client.deliberate_async.assert_awaited_once()
    assert "PLAN APPROVED BY SAFETY SUBSYSTEM" in final_output


@pytest.mark.asyncio
@patch.object(LlmAgent, '_run_async_impl')
async def test_mcs_vetted_agent_rejection_path_async(mock_run_async_impl):
    """
    Tests the MCSVettedFinancialAgent's rejection path asynchronously.
    """
    # --- Arrange ---
    mock_mcs_client = AsyncMock(spec=MCSClient)
    mock_mcs_client.is_server_ready_async.return_value = True
    mock_mcs_client.deliberate_async.return_value = {
        "decision": "VETO",
        "justification": "The plan involves highly volatile assets, exceeding risk budget."
    }

    vetted_agent = MCSVettedFinancialAgent(name="test_agent", mcs_client=mock_mcs_client, model="gemini-1.5-pro")

    mock_ctx = MagicMock(spec=InvocationContext)
    mock_ctx.user_content = "Give me a risky plan."
    mock_ctx.agent_states = {}
    mock_ctx.invocation_id = "test_id"
    mock_ctx.agent = vetted_agent
    mock_ctx.run_config = RunConfig()
    mock_ctx.session = MagicMock()
    mock_ctx.session.events = []
    mock_ctx.branch = "test_branch"
    mock_ctx.context_cache_config = None
    mock_ctx.end_invocation = False

    async def mock_run_async_impl_gen(*args, **kwargs):
        yield Event(
            author="test",
            content=types.Content(parts=[types.Part(text="A very risky plan.")]),
            id="test",
            invocation_id=mock_ctx.invocation_id,
            partial=False
        )
    mock_run_async_impl.side_effect = mock_run_async_impl_gen

    # --- Act ---
    final_output = ""
    async for event in vetted_agent._run_async_impl(ctx=mock_ctx):
        if not event.partial:
            final_output = event.content.parts[0].text

    # --- Assert ---
    assert "PLAN REJECTED BY SAFETY SUBSYSTEM" in final_output
    assert "exceeding risk budget" in final_output
