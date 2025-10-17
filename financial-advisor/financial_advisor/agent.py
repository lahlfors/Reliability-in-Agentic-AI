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

"""Financial coordinator: provide reasonable investment strategies"""
import logging
import uuid
import traceback
from typing import AsyncIterator

# Correct imports for the Google ADK framework
from google.adk.agents import LlmAgent, InvocationContext
from google.adk.events.event import Event
from google.adk.tools.agent_tool import AgentTool

# Correct, stable import pattern for Content/Part types
from google.genai import types

# --- Updated import from top-level observability package ---
from observability.observability.logging_config import setup_logging, get_logger

# Setup logging as early as possible
setup_logging()

# Get a logger for this module
logger = get_logger(__name__)

logger.info("MCSVettedFinancialAgent module loading...")

class MCSVettedFinancialAgent(LlmAgent):
    """
    A financial agent that extends LlmAgent to incorporate a safety-vetting
    step before producing a final response. It is designed to be robust
    and handle potential failures gracefully.
    """
    # Declare the custom mcs_client field using a string forward reference.
    mcs_client: "MCSClient"
    _mcs_is_setup: bool = False

    def __init__(self, mcs_client: "MCSClient", **kwargs):
        """Initializes the vetted agent."""
        super().__init__(mcs_client=mcs_client, **kwargs)
        self._mcs_is_setup = False

    async def _setup_mcs_connection_async(self):
        """Performs one-time setup and configuration of the MCS client."""
        if self._mcs_is_setup:
            return
        logger.info("Waiting for MCS server to become ready...")
        if not await self.mcs_client.is_server_ready_async():
            raise ConnectionError("Metacognitive Control Subsystem is not available.")
        logger.info("MCS server is ready.")

        constraints = [
            {"name": "tool_misuse", "description": "Limits risky tool use.", "budget": 0.8},
            {"name": "resource_usage", "description": "Limits API calls.", "budget": 1.0},
            {"name": "privacy_leak", "description": "Prevents PII leaks.", "budget": 0.5},
        ]
        await self.mcs_client.configure_constraints_async(constraints)
        logger.info("MCS constraints configured successfully.")
        self._mcs_is_setup = True

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncIterator[Event]:
        """
        The core execution method. It runs the parent LlmAgent's logic,
        intercepts the result, vets it, and then yields a final, safe response.
        """
        try:
            await self._setup_mcs_connection_async()
        except Exception as e:
            logger.error(f"Error setting up safety system: {e}", exc_info=True)
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"Error setting up safety system: {e}")]),
                id=str(uuid.uuid4()),
                invocation_id=ctx.invocation_id,
                partial=False
            )
            return

        user_query = str(ctx.user_content)
        logger.debug(f"User query: {user_query}")

        logger.info("Getting financial plan from the underlying LlmAgent...")
        final_event = None
        try:
            async for event in super()._run_async_impl(ctx):
                if not event.partial:
                    final_event = event
        except Exception as e:
            logger.error(f"Error during plan generation: {e}", exc_info=True)
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"Error during plan generation: {e}")]),
                id=str(uuid.uuid4()),
                invocation_id=ctx.invocation_id,
                partial=False
            )
            return

        proposed_plan_str = ""
        if final_event and final_event.content and final_event.content.parts:
            proposed_plan_str = final_event.content.parts[0].text
        else:
            logger.warning("Could not generate an initial financial plan.")
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text="Could not generate an initial financial plan.")]),
                id=str(uuid.uuid4()),
                invocation_id=ctx.invocation_id,
                partial=False
            )
            return
        logger.debug(f"Proposed plan: {proposed_plan_str}")

        logger.info("Vetting the financial plan with the TDD-aligned Metacognitive Control Subsystem...")

        # Construct the agent_state object for the /deliberate endpoint
        agent_state = {
            "goal": user_query,
            "plan": proposed_plan_str.split('\n'),  # Simple plan representation
            "memory_buffer": f"User query: {user_query}",  # Simple memory
            "proposed_action": {
                "tool_name": "present_financial_plan",
                "parameters": {
                    "plan_details": proposed_plan_str
                }
            },
            # Provide tool schemas if available, otherwise an empty list
            "tool_schemas": [t._get_declaration().model_dump(exclude_unset=True) for t in self.tools] if hasattr(self, 'tools') else []
        }

        try:
            # Call the new deliberate_async method
            deliberation_result = await self.mcs_client.deliberate_async(agent_state)
        except Exception as e:
            logger.error(f"Error during safety deliberation: {e}", exc_info=True)
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"Error during safety deliberation: {e}")]),
                id=str(uuid.uuid4()),
                invocation_id=ctx.invocation_id,
                partial=False
            )
            return
        logger.debug(f"Deliberation result: {deliberation_result}")

        if deliberation_result and deliberation_result.get("decision") == "EXECUTE":
            justification = deliberation_result.get("justification", "Plan approved by R2A2.")
            final_response_text = (
                "--- PLAN APPROVED BY SAFETY SUBSYSTEM ---\n"
                f"Reasoning: {justification}\n\n"
                f"--- Financial Plan ---\n{proposed_plan_str}"
            )
        else:
            decision = deliberation_result.get('decision', 'UNKNOWN') if deliberation_result else 'ERROR'
            justification = deliberation_result.get("justification", "An unspecified safety concern was raised.")
            final_response_text = (
                f"--- PLAN REJECTED BY SAFETY SUBSYYSTEM (Decision: {decision}) ---\n"
                f"Reason: {justification}\n\n"
                "The proposed financial plan was blocked to ensure safety. "
                "Please refine your request or consult a human expert."
            )
        logger.info("Yielding final response.")
        final_content = types.Content(parts=[types.Part(text=final_response_text)])
        yield Event(author=self.name, content=final_content, id=str(uuid.uuid4()), invocation_id=ctx.invocation_id, partial=False)

# Initialize root_agent to None to handle potential instantiation errors.
root_agent = None
try:
    # Defer local imports to prevent circular dependencies at load time.
    from . import prompt
    from .sub_agents.data_analyst import data_analyst_agent
    from .sub_agents.execution_analyst import execution_analyst_agent
    from .sub_agents.trading_analyst import trading_analyst_agent
    from .utils.mcs_client import MCSClient

    # After importing the necessary classes, tell Pydantic to resolve
    # the string-based forward references in our agent class.
    MCSVettedFinancialAgent.model_rebuild()

    logger.info("Attempting to create root_agent instance...")
    # The `adk web` command requires a module-level variable named `root_agent`.
    root_agent = MCSVettedFinancialAgent(
        name="financial_coordinator",
        model="gemini-2.5-pro",
        description=(
            "A financial agent designed to provide vetted financial advice."
        ),
        instruction=prompt.FINANCIAL_COORDINATOR_PROMPT,
        tools=[
            AgentTool(agent=data_analyst_agent),
            AgentTool(agent=trading_analyst_agent),
            AgentTool(agent=execution_analyst_agent),
        ],
        mcs_client=MCSClient()
    )
    logger.info("root_agent instance created successfully.")
except Exception as e:
    logger.critical(f"FATAL ERROR during root_agent instantiation: {e}", exc_info=True)
    # root_agent remains None if instantiation fails