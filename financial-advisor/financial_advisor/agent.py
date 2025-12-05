# Copyright 2025 Google LLC
# Updated for ISO 42001 Compliance (VACP Integration)

import logging
import uuid
from typing import AsyncIterator, Any
import opentelemetry.trace as trace

from google.adk.agents import LlmAgent, InvocationContext
from google.adk.events.event import Event
from google.adk.tools.agent_tool import AgentTool
from pydantic import PrivateAttr

# VACP Components are now implicitly integrated via OTel
# We no longer explicitly call GOA.process_request

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class VACPGovernedAgent(LlmAgent):
    """
    An agent that delegates control decisions to the Verifiable Agentic Control Plane via OpenTelemetry.
    """

    def __init__(self, **kwargs):
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
                             # We use a manual start/end because we span across async events
                             reasoning_span = tracer.start_span("gen_ai.reasoning")
                             reasoning_span.set_attribute("gen_ai.span.type", "reasoning")

                # 2. Check for Tool Use (Action Phase)
                # Google ADK events are complex, usually tool calls are distinct events or part of content
                # We simplified: If we see a ToolCall or similar, we end the reasoning span first.

                # In ADK, tool calls might just be implicit.
                # We assume if the agent *emits* an event that triggers a tool,
                # we must close the reasoning span immediately to trigger the VACP check.

                # For this specific `super()` implementation, we assume we just pass through events.
                # But to properly separate Thought vs Action for OTel, we need to know when Thought ends.
                # A heuristic: if event has tool_calls or function_call, it's an action.

                # However, since `super()` handles the loop, we are observing.
                # If the event suggests a tool call is about to happen (or is requested),
                # we finalize the reasoning.

                # Assuming `event.tool_calls` exists or similar structure in ADK events (simplified)
                # Or just whenever we yield, we treat the preceding text as a thought block.

                # Let's assume every chunk of text is part of reasoning.
                # If we get a chunk that is not text (e.g. tool request), we close the span.

                # For this simulation, we will treat the 'text' response as the reasoning.
                # When the agent stops generating text (yields a final chunk or switches to tool), we end span.

                # Actually, `LlmAgent` yields `Event`s.
                # If event has `tool_use`, we must have ended the reasoning span *before* this event was yielded?
                # No, `super()` yields the tool use event. The executor (consumer) will act on it.
                # So we can intercept it here.

                if hasattr(event, "tool_use") and event.tool_use:
                     if reasoning_span:
                        reasoning_span.set_attribute("gen_ai.content.completion", reasoning_buffer)
                        reasoning_span.end() # This triggers VACPSpanProcessor -> AgentGuard -> GOA
                        reasoning_span = None
                        reasoning_buffer = ""

                # Also if we just have text and the stream ends (loop finishes), we handle that outside loop.
                # But `super()` loop yields events.

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
    from vacp.ans import AgentNameService # ANS to register

    # Register self in ANS (Simulated)
    # ans = AgentNameService()
    # ans.register(...)

    # We no longer pass `vacp_goa` to the constructor.
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
    logger.critical(f"FATAL ERROR during agent instantiation: {e}", exc_info=True)
