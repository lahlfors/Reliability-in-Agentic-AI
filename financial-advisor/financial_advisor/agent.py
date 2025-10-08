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

from typing import AsyncIterator
from google.adk.agents import BaseAgent, InvocationContext, LlmAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .sub_agents.data_analyst import data_analyst_agent
from .sub_agents.execution_analyst import execution_analyst_agent
from .sub_agents.trading_analyst import trading_analyst_agent
from .utils.r2a2_client import R2A2Client


class R2A2VettedFinancialAgent(BaseAgent):
    """
    A wrapper agent that runs the financial coordinator and vets its final
    output through the R2A2 Modular Safety Subsystem.

    This class inherits from BaseAgent to be compatible with the ADK framework
    and uses a Pydantic model structure.
    """
    # Pydantic fields must be declared at the class level with type hints.
    name: str
    coordinator: LlmAgent
    r2a2_client: R2A2Client

    def __init__(self, name: str, coordinator: LlmAgent, r2a2_client: R2A2Client):
        """Initializes the vetted agent."""
        # Call the parent __init__ to satisfy the Pydantic model.
        super().__init__(
            name=name,
            coordinator=coordinator,
            r2a2_client=r2a2_client
        )
        self._r2a2_is_setup = False  # Flag for lazy initialization

    async def _setup_r2a2_connection_async(self):
        """
        Performs one-time setup and configuration of the R2A2 client.
        This is called lazily on the first run.
        """
        print("Waiting for R2A2 server to become ready...")
        if not await self.r2a2_client.is_server_ready_async():
            raise ConnectionError("R2A2 Safety Subsystem is not available.")
        print("R2A2 server is ready.")

        constraints = [
            {"name": "tool_misuse", "description": "Limits risky tool use.", "budget": 0.8},
            {"name": "resource_usage", "description": "Limits API calls.", "budget": 1.0},
            {"name": "privacy_leak", "description": "Prevents PII leaks.", "budget": 0.5},
        ]
        await self.r2a2_client.configure_constraints_async(constraints)
        print("R2A2 constraints configured successfully.")
        self._r2a2_is_setup = True

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncIterator[dict]:
        """
        Asynchronously runs the financial coordinator and vets its final output.
        This is the required implementation for a BaseAgent.
        """
        if not self._r2a2_is_setup:
            await self._setup_r2a2_connection_async()

        # 1. Get the user's query from the InvocationContext.
        user_query = str(ctx.user_content)
        coordinator_inputs = {"query": user_query}

        # 2. Get the proposed plan from the coordinator agent asynchronously.
        print("Getting financial plan from the coordinator agent...")
        final_event = {}
        async for event in self.coordinator.run_async(**coordinator_inputs):
            if event.get("is_final"):
                final_event = event
        proposed_plan_str = final_event.get("output", "")

        # 3. Vet the proposed plan with the R2A2 subsystem asynchronously.
        print("Vetting the financial plan with the R2A2 Safety Subsystem...")
        task_instruction = (
            "You are a safety firewall. A financial agent has proposed the "
            "following investment plan. Analyze it for risks such as tool "
            "misuse, resource consumption, and privacy violations."
        )
        observations = {
            "user_query": user_query,
            "proposed_plan": proposed_plan_str
        }
        vetting_result = await self.r2a2_client.vet_action_async(task_instruction, observations)

        # 4. Process the result and yield the final output.
        if vetting_result and vetting_result.get("status") == "ACTION_APPROVED":
            explanation = vetting_result.get("explanation", "Plan approved by R2A2.")
            final_response = (
                "--- PLAN APPROVED BY SAFETY SUBSYSTEM ---\n"
                f"Reasoning: {explanation}\n\n"
                f"--- Financial Plan ---\n{proposed_plan_str}"
            )
        elif vetting_result and vetting_result.get("status") == "DEFER_TO_HUMAN":
            explanation = vetting_result.get("explanation", "No explanation provided.")
            final_response = (
                "--- PLAN REJECTED BY SAFETY SUBSYSTEM ---\n"
                f"Reason: {explanation}\n\n"
                "The proposed financial plan was deemed too risky to proceed."
            )
        else:
            final_response = (
                "--- SAFETY SUBSYSTEM ERROR ---\n"
                "Could not get a safety assessment from the R2A2 subsystem. "
                "Aborting to ensure safety."
            )

        yield {"output": final_response, "is_final": True}


def create_agent() -> R2A2VettedFinancialAgent:
    """
    Factory function to create and configure the financial advisor agent.
    This avoids module-level instantiation, which can cause issues with testing
    and framework loading.
    """
    MODEL = "gemini-1.5-pro"

    # Define the coordinator agent without the risk_analyst tool.
    financial_coordinator = LlmAgent(
        name="financial_coordinator",
        model=MODEL,
        description=(
            "guide users through a structured process to receive financial "
            "advice by orchestrating a series of expert subagents. help them "
            "analyze a market ticker, develop trading strategies, and define "
            "execution plans."
        ),
        instruction=prompt.FINANCIAL_COORDINATOR_PROMPT,
        output_key="financial_coordinator_output",
        tools=[
            AgentTool(agent=data_analyst_agent),
            AgentTool(agent=trading_analyst_agent),
            AgentTool(agent=execution_analyst_agent),
        ],
    )

    # Create an instance of the custom vetted agent
    vetted_agent = R2A2VettedFinancialAgent(
        name="r2a2_vetted_financial_agent",
        coordinator=financial_coordinator,
        r2a2_client=R2A2Client()
    )
    return vetted_agent