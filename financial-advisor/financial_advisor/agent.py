# Copyright 2025 Google LLC
# Updated for ISO 42001 Compliance (VACP Integration)

import logging
import uuid
import traceback
from typing import AsyncIterator, Any

from google.adk.agents import LlmAgent, InvocationContext
from google.adk.events.event import Event
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from pydantic import PrivateAttr

# Import VACP Components (Simulating the Sidecar Client)
from vacp.goa import GoverningOrchestratorAgent
from vacp.schemas import AgentAction

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VACPGovernedAgent(LlmAgent):
    """
    An agent that delegates control decisions to the Verifiable Agentic Control Plane.
    """
    _goa: GoverningOrchestratorAgent = PrivateAttr()

    def __init__(self, vacp_goa: GoverningOrchestratorAgent, **kwargs):
        super().__init__(**kwargs)
        self._goa = vacp_goa

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncIterator[Event]:
        """
        Intercepts the agent's run loop to enforce VACP governance.
        """
        logger.info(f"Agent {self.name} starting run under VACP governance.")

        # In a real implementation, we would hook into the tool selection step.
        # Here, we simulate the 'planning' -> 'governance' -> 'execution' flow.

        async for event in super()._run_async_impl(ctx):
            # If the event contains a proposed plan or tool call (simplified for demo)
            # We assume the model outputs a text plan first.

            if event.content and event.content.parts:
                text_content = event.content.parts[0].text

                # SIMULATION: Extract intent as if it were a tool call
                # In production, this would be an actual tool_use event interception
                proposed_tool = "place_order" if "buy" in text_content.lower() else "data_analyst"

                # Construct Action for VACP
                action = AgentAction(
                    tool_name=proposed_tool,
                    parameters={"context": text_content}
                )

                # CALL VACP (GOA)
                # The agent pauses while the Control Plane decides.
                decision_obj = self._goa.process_request(action, plan_context=text_content)

                if decision_obj.decision == "QUARANTINE":
                    # Block the response/action
                    rejection_msg = f"--- VACP SECURITY ALERT ---\nAction blocked by ISO 42001 Control Plane.\nReason: {decision_obj.justification}"
                    yield Event(
                        author="VACP_GOA",
                        content=types.Content(parts=[types.Part(text=rejection_msg)]),
                        id=str(uuid.uuid4()),
                        invocation_id=ctx.invocation_id
                    )
                    return # Stop execution

            yield event

# --- Initialization ---
try:
    from . import prompt
    from .sub_agents.data_analyst import data_analyst_agent
    from .sub_agents.execution_analyst import execution_analyst_agent
    from .sub_agents.trading_analyst import trading_analyst_agent
    from .tools.risk_tools import place_order, execute_python_code

    # Initialize the Control Plane Sidecar (GOA)
    # This represents the "Sidecar" container running alongside the agent
    goa_sidecar = GoverningOrchestratorAgent(agent_id="financial_coordinator")

    root_agent = VACPGovernedAgent(
        vacp_goa=goa_sidecar,
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
    logger.info("VACPGovernedAgent initialized successfully.")
except Exception as e:
    logger.critical(f"FATAL ERROR during agent instantiation: {e}", exc_info=True)
