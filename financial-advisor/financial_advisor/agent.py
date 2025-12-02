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
from observability.observability.telemetry import setup_telemetry
from metacognitive_control_subsystem.mcs.guardrails.actuators import GuardrailController, SecurityException

setup_logging()
logger = get_logger(__name__)
tracer = setup_telemetry()

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
        with tracer.start_as_current_span("gen_ai.agent.run") as root_span:
            root_span.set_attribute("gen_ai.agent.id", self.name)
            try:
                await self._setup_mcs_connection_async()
            except Exception as e:
                root_span.record_exception(e)
                yield self._create_error_event(f"Error setting up safety system: {e}", ctx)
                return

            user_query = str(ctx.user_content)
            root_span.set_attribute("gen_ai.user.query", user_query)

            # This loop represents the agent's internal monologue and action proposal cycle.
            try:
                # 1. Generate a proposed plan/action from the core LLM
                proposed_event = None
                with tracer.start_as_current_span("gen_ai.thought") as thought_span:
                    thought_span.set_attribute("gen_ai.thought.type", "planning")
                    async for event in super()._run_async_impl(ctx):
                        if not event.partial:
                            proposed_event = event
                            break

                if not proposed_event:
                    yield self._create_error_event("Could not generate an initial financial plan.", ctx)
                    return

                # Assuming the event content might have tool calls.
                # Ideally, we should inspect event.tool_calls if they exist.
                # However, the current logic assumes text output for the plan.

                # We need to intercept tool calls if they happen inside super()._run_async_impl
                # But since we are inheriting, we might need to override _execute_tool (if it exists)
                # or rely on the fact that we are manually constructing the "proposed action" here.

                # Check if the proposed event actually contains a tool call that we need to vet.
                # For the demo, we assume the text itself is the plan, OR we parse tool calls.

                # IMPORTANT: The current implementation extracts text.
                # If we want to guard `place_order`, we need to see if the LLM *called* it.
                # Standard LlmAgent handles tool calls automatically.
                # To intercept, we would need to hook into the tool execution.

                # Since we cannot easily hook into `super()`'s internal tool loop without overriding it entirely,
                # we will rely on the fact that we are adding `place_order` to the tool list.
                # AND we will implement a wrapper around the tool function itself?
                # No, we already implemented the tools as functions.
                # We should wrap them *before* passing them to the agent constructor?
                # Or better, we can invoke the guardrail check INSIDE the tool function?
                # Actually, the STPA requirement says "Actuators... independent of decision making".
                # Calling it inside the tool is "at the point of actuation", which is correct.

                # However, to be cleaner, let's look at how we constructed `agent_state`.
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
                with tracer.start_as_current_span("gen_ai.safety.deliberation") as safety_span:
                    deliberation_result = await self.mcs_client.deliberate_async(agent_state)
                    safety_span.set_attribute("gen_ai.safety.decision", str(deliberation_result.get("decision")))

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
                root_span.record_exception(e)
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
    from .tools.risk_tools import place_order, execute_python_code

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
            place_order,
            execute_python_code
        ],
        mcs_client=MCSClient()
    )
    logger.info("root_agent instance created successfully.")
except Exception as e:
    logger.critical(f"FATAL ERROR during root_agent instantiation: {e}", exc_info=True)
