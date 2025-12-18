# Copyright 2025 Google LLC
# Updated for ISO 42001 Compliance (VACP Integration)

import logging
from typing import AsyncIterator
import opentelemetry.trace as trace

from google.adk.agents import LlmAgent, InvocationContext
from google.adk.events.event import Event

# Configure Logging
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
