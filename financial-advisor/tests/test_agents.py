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

"""Asynchronous test cases for the refactored Financial Advisor (VACP/OTel)."""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock, ANY

# HACK: Add the project root to the python path to allow imports to work.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from financial_advisor.agent import VACPGovernedAgent
from google.adk.agents import InvocationContext, RunConfig, LlmAgent
from google.adk.events.event import Event
from google.genai import types

# Tell pytest this is an async test file
pytest_plugins = ("pytest_asyncio",)

@pytest.mark.asyncio
@patch('financial_advisor.agent.tracer')
@patch.object(LlmAgent, '_run_async_impl')
async def test_vacp_governed_agent_otel_tracing(mock_run_async_impl, mock_tracer):
    """
    Tests that VACPGovernedAgent correctly generates OpenTelemetry spans for reasoning.
    """
    # --- Arrange ---
    vetted_agent = VACPGovernedAgent(name="test_agent", model="gemini-1.5-pro")

    mock_ctx = MagicMock(spec=InvocationContext)
    mock_ctx.user_content = "Give me a stock plan."
    mock_ctx.invocation_id = "test_id"
    mock_ctx.agent = vetted_agent
    mock_ctx.run_config = RunConfig()
    mock_ctx.session = MagicMock()
    mock_ctx.session.events = []
    mock_ctx.branch = "test_branch"

    # Mock tracer context managers
    mock_root_span = MagicMock()
    mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_root_span

    mock_reasoning_span = MagicMock()
    mock_tracer.start_span.return_value = mock_reasoning_span

    # Mock generator yielding an event
    async def mock_run_async_impl_gen(*args, **kwargs):
        yield Event(
            author="test",
            content=types.Content(parts=[types.Part(text="Thinking about stocks...")]),
            id="test",
            invocation_id=mock_ctx.invocation_id,
            partial=False
        )
    mock_run_async_impl.side_effect = mock_run_async_impl_gen

    # --- Act ---
    async for event in vetted_agent._run_async_impl(ctx=mock_ctx):
        pass

    # --- Assert ---
    # 1. Verify Root Span
    mock_tracer.start_as_current_span.assert_called_with("agent.interaction.test_id")
    mock_root_span.set_attribute.assert_any_call("vacp.agent.id", "test_agent")

    # 2. Verify Reasoning Span creation
    mock_tracer.start_span.assert_called_with("gen_ai.reasoning")
    mock_reasoning_span.set_attribute.assert_any_call("gen_ai.span.type", "reasoning")

    # 3. Verify Reasoning Span cleanup (end)
    # It should be ended when loop finishes or tool is called. Here loop finishes.
    mock_reasoning_span.end.assert_called()
    mock_reasoning_span.set_attribute.assert_any_call("gen_ai.content.completion", "Thinking about stocks...")
