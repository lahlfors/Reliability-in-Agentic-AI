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

from google.adk.agents import LlmAgent, InvocationContext
from google.adk.events.event import Event
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from observability.observability.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

logger.info("MCSVettedFinancialAgent module loading...")

class MCSVettedFinancialAgent(LlmAgent):
    """
    A financial agent that extends LlmAgent to incorporate a safety-vetting
    step before producing a final response. It is designed to be robust
    and handle potential failures gracefully.
    """
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
            {"name": "Fiduciary Duty Constraint", "description": "Ensures recommendations are suitable.", "budget": 0.01},
            {"name": "Compliance Constraint", "description": "Ensures adherence to legal requirements.", "budget": 0.0}
        ]
        await self.mcs_client.configure_constraints_async(constraints)
        logger.info("MCS constraints configured successfully.")
        self._mcs_is_setup = True

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncIterator[Event]:
        """
        The core execution method, now fully aligned with the TDD's host agent
        integration logic.
        """
        try:
            await self._setup_mcs_connection_async()
        except Exception as e:
            yield self._create_error_event(f"Error setting up safety system: {e}", ctx)
            return

        user_query = str(ctx.user_content)

        # This loop represents the agent's internal monologue and action proposal cycle.
        # For simplicity, we run it once, but a real agent might loop multiple times.
        try:
            # 1. Generate a proposed plan/action from the core LLM
            proposed_event = None
            async for event in super()._run_async_impl(ctx):
                if not event.partial:
                    proposed_event = event
                    break

            if not proposed_event:
                yield self._create_error_event("Could not generate an initial financial plan.", ctx)
                return

            proposed_plan_str = proposed_event.content.parts[0].text

            # 2. Construct the payload for the MCS
            agent_state = {
                "goal": user_query,
                "plan": proposed_plan_str.split('\n'),
                "memory_buffer": f"User query: {user_query}",
                "proposed_action": {"tool_name": "present_financial_plan", "parameters": {"plan_details": proposed_plan_str}},
                "tool_schemas": [t._get_declaration().model_dump(exclude_unset=True) for t in self.tools] if hasattr(self, 'tools') else []
            }

            # 3. Call the MCS for a deliberation
            deliberation_result = await self.mcs_client.deliberate_async(agent_state)

            # 4. Implement conditional logic based on the MCS decision
            decision = deliberation_result.get("decision", "ERROR") if deliberation_result else "ERROR"
            justification = deliberation_result.get("justification", "An error occurred during safety deliberation.")

            if decision == "EXECUTE":
                final_response_text = (
                    "--- PLAN APPROVED BY SAFETY SUBSYSTEM ---\n"
                    f"Reasoning: {justification}\n\n"
                    f"--- Financial Plan ---\n{proposed_plan_str}"
                )
            elif decision in ["VETO", "REVISE"]:
                final_response_text = (
                    f"--- PLAN REJECTED BY SAFETY SUBSYSTEM (Decision: {decision}) ---\n"
                    f"Reason: {justification}\n\n"
                    "The proposed financial plan was blocked to ensure safety. "
                    "Please refine your request or consult a human expert."
                )
            elif decision == "ESCALATE":
                final_response_text = "This request requires review by a human advisor. Please stand by."
            else: # TERMINATE or other errors
                final_response_text = "The session has been terminated for safety reasons."

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            yield self._create_error_event(f"An unexpected error occurred during processing.", ctx)
            return

        yield self._create_final_event(final_response_text, ctx)

    def _create_error_event(self, message: str, ctx: InvocationContext) -> Event:
        logger.error(message, exc_info=True)
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=message)]),
            id=str(uuid.uuid4()),
            invocation_id=ctx.invocation_id,
            partial=False
        )

    def _create_final_event(self, text: str, ctx: InvocationContext) -> Event:
        return Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=text)]),
            id=str(uuid.uuid4()),
            invocation_id=ctx.invocation_id,
            partial=False
        )


# Initialize root_agent to None to handle potential instantiation errors.
root_agent = None
try:
    from . import prompt
    from .sub_agents.data_analyst import data_analyst_agent
    from .sub_agents.execution_analyst import execution_analyst_agent
    from .sub_agents.trading_analyst import trading_analyst_agent
    from .utils.mcs_client import MCSClient

    MCSVettedFinancialAgent.model_rebuild()

    root_agent = MCSVettedFinancialAgent(
        name="financial_coordinator",
        model="gemini-2.5-pro",
        description="A financial agent designed to provide vetted financial advice.",
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
