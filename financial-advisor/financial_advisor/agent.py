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

from google.adk.agents import BaseAgent, LlmAgent
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
    """
    name: str
    coordinator: LlmAgent
    r2a2_client: R2A2Client

    def __init__(self, name: str, coordinator: LlmAgent, r2a2_client: R2A2Client):
        """
        Initializes the Pydantic BaseModel by calling the parent constructor
        with the declared fields.
        """
        super().__init__(
            name=name,
            coordinator=coordinator,
            r2a2_client=r2a2_client
        )
        self._r2a2_is_setup = False  # Flag for lazy initialization

    def _setup_r2a2_connection(self):
        """
        Performs one-time setup and configuration of the R2A2 client.
        This is called lazily on the first run to allow for easier testing.
        """
        # For demonstration, configure R2A2 with some default constraints.
        # In a production system, this would come from a configuration file.
        constraints = [
            {"name": "tool_misuse", "description": "Limits risky tool use.", "budget": 0.8},
            {"name": "resource_usage", "description": "Limits API calls.", "budget": 1.0},
            {"name": "privacy_leak", "description": "Prevents PII leaks.", "budget": 0.5},
        ]
        if self.r2a2_client.is_server_ready():
            self.r2a2_client.configure_constraints(constraints)
            self._r2a2_is_setup = True
        else:
            # If the safety subsystem isn't available, we should not proceed.
            raise ConnectionError("R2A2 Safety Subsystem is not available.")

    def run(self, inputs: dict) -> str:
        """
        Runs the financial coordinator and vets its final output through R2A2.

        Args:
            inputs: A dictionary of inputs for the agent, typically containing
                    the user's query.

        Returns:
            A string containing the final, vetted financial advice or a
            rejection message.
        """
        # Lazy initialization: setup the connection on the first run.
        if not self._r2a2_is_setup:
            self._setup_r2a2_connection()

        # 1. Get the proposed plan from the coordinator agent.
        print("Getting financial plan from the coordinator agent...")
        proposed_plan_str = self.coordinator.run(inputs)

        # 2. Vet the proposed plan with the R2A2 subsystem.
        print("Vetting the financial plan with the R2A2 Safety Subsystem...")
        task_instruction = (
            "You are a safety firewall. A financial agent has proposed the "
            "following investment plan. Analyze it for risks such as tool "
            "misuse, resource consumption, and privacy violations."
        )
        observations = {
            "user_query": inputs.get("query"),
            "proposed_plan": proposed_plan_str
        }
        vetting_result = self.r2a2_client.vet_action(task_instruction, observations)

        # 3. Process the vetting result and formulate the final response.
        if vetting_result and vetting_result.get("status") == "ACTION_APPROVED":
            explanation = vetting_result.get("explanation", "Plan approved by R2A2.")
            final_response = (
                "--- PLAN APPROVED BY SAFETY SUBSYSTEM ---\n"
                f"Reasoning: {explanation}\n\n"
                f"--- Financial Plan ---\n{proposed_plan_str}"
            )
            return final_response
        elif vetting_result and vetting_result.get("status") == "DEFER_TO_HUMAN":
            explanation = vetting_result.get("explanation", "No explanation provided.")
            final_response = (
                "--- PLAN REJECTED BY SAFETY SUBSYSTEM ---\n"
                f"Reason: {explanation}\n\n"
                "The proposed financial plan was deemed too risky to proceed. "
                "Please revise the plan or consult a human expert."
            )
            return final_response
        else:
            return (
                "--- SAFETY SUBSYSTEM ERROR ---\n"
                "Could not get a safety assessment from the R2A2 subsystem. "
                "Aborting to ensure safety."
            )


MODEL = "gemini-2.5-pro"


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

# The root_agent is now the R2A2-vetted wrapper around the coordinator.
root_agent = R2A2VettedFinancialAgent(
    name="r2a2_vetted_financial_agent",
    coordinator=financial_coordinator,
    r2a2_client=R2A2Client()
)