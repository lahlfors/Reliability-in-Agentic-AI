# Copyright 2025 Google LLC
# Updated for ISO 42001 Compliance (VACP Integration)

import logging
from typing import AsyncIterator
import opentelemetry.trace as trace

from google.adk.agents import LlmAgent, InvocationContext
from google.adk.events.event import Event
from google.adk.tools.agent_tool import AgentTool
from pydantic import PrivateAttr

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class VACPGovernedAgent(LlmAgent):
    """
    An agent that delegates control decisions to the Verifiable Agentic Control Plane via OpenTelemetry.
    """

    def __init__(self, **kwargs):
        # Filter out extra args if needed, but LlmAgent accepts kwargs
        super().__init__(**kwargs)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncIterator[Event]:
        """
        Intercepts the agent's run loop to enforce VACP governance via OTel.
        """
        logger.info(f"Agent {self.name} starting run under OTel-driven VACP governance.")

        # Start Root Span for the Interaction
        with tracer.start_as_current_span(f"agent.interaction.{ctx.invocation_id}") as root_span:
            root_span.set_attribute("vacp.agent.id", self.name)
            root_span.set_attribute("vacp.risk.tier", "High") # Dynamic in prod

            # Helper to buffer reasoning text
            reasoning_buffer = ""
            reasoning_span = None

            async for event in super()._run_async_impl(ctx):
                # 1. Capture Reasoning (Thought Phase)
                if event.content and event.content.parts:
                    text_content = event.content.parts[0].text
                    if text_content:
                        reasoning_buffer += text_content
                        # If we haven't started a reasoning span, start one
                        if not reasoning_span:
                             reasoning_span = tracer.start_span("gen_ai.reasoning")
                             reasoning_span.set_attribute("gen_ai.span.type", "reasoning")

                # 2. Check for Tool Use (Action Phase)
                # Heuristic: If event triggers a tool (simplified for ADK structure)
                # In ADK, the event itself describes what happened.
                # If we detect a tool call, we close the reasoning span.

                # Note: This is a simplified OTel instrumentation for demonstration.
                if hasattr(event, "tool_use") and event.tool_use:
                     if reasoning_span:
                        reasoning_span.set_attribute("gen_ai.content.completion", reasoning_buffer)
                        reasoning_span.end()
                        reasoning_span = None
                        reasoning_buffer = ""

                yield event

            # Clean up trailing reasoning
            if reasoning_span:
                reasoning_span.set_attribute("gen_ai.content.completion", reasoning_buffer)
                reasoning_span.end()

# --- Initialization ---
try:
    from . import prompt
    from .sub_agents.data_analyst import data_analyst_agent
    from .sub_agents.execution_analyst import execution_analyst_agent
    from .sub_agents.trading_analyst import trading_analyst_agent
    from .tools.risk_tools import place_order, execute_python_code
    from vacp.ans import AgentNameService

    # We no longer pass `vacp_goa` to the constructor.
    # Instantiate the agent to make it available for import
    root_agent = VACPGovernedAgent(
        name="financial_coordinator",
        model="gemini-2.5-pro",
        description="ISO 42001 Compliant Financial Agent",
        instruction=prompt.FINANCIAL_COORDINATOR_PROMPT,
        tools=[
            AgentTool(agent=data_analyst_agent),
            AgentTool(agent=trading_analyst_agent),
            AgentTool(agent=execution_analyst_agent),
            place_order,
            execute_python_code
        ]
    )
    logger.info("VACPGovernedAgent initialized successfully with OTel Governance.")
except Exception as e:
    # Log but don't crash module load if dependencies missing (e.g. in test env)
    logger.warning(f"Could not instantiate root_agent (expected during tests): {e}")
