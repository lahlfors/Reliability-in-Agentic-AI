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

"""
Main entry point for the Financial Advisor VACP System.
Registers all agents with the Runner to enable deterministic routing.
"""

import logging
import asyncio

# ADK Imports
from google.adk.runners import InMemoryRunner

# Agent Imports
from financial_advisor.agent import root_agent as coordinator
from financial_advisor.sub_agents.data_analyst import data_analyst_agent
from financial_advisor.sub_agents.trading_analyst import trading_analyst_agent
from financial_advisor.sub_agents.execution_analyst import execution_analyst_agent
from financial_advisor.sub_agents.safety import compliance_agent, human_escalation_agent, risk_evaluation_agent

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: The coordinator already has the "router" tool.
# In ADK 1.17, we simply run the root agent (coordinator).
# The coordinator will return "transfer_to_agent" events/actions,
# which the Runner (InMemoryRunner) should handle if the target agents are registered.
# But InMemoryRunner.__init__ only takes `agent` (singular).

# INVESTIGATION:
# The user prompted: "If you register sub-agents, the ADK automatically injects this tool".
# But we REMOVED sub_agents from the coordinator to be "explicit".
# If we run `coordinator`, and it calls `router` tool, which sets `transfer_to_agent="foo"`,
# the Runner needs to know how to load "foo".

# In `google-adk` 1.17, there isn't a "list of agents" in `InMemoryRunner`.
# However, usually there is a registry or the agent itself has `sub_agents`.
# The user explicitly asked to REMOVE `sub_agents` list from coordinator.

# This implies we need a way to make the runner aware of other agents.
# OR, we need to add them back as `sub_agents` but rely on OUR tool to do the routing,
# effectively overriding the stochastic choice.

# Wait, if we use `sub_agents`, ADK adds `transfer_to_agent` tool automatically.
# The user wants "Type B: The 'Router Tool' Approach (Explicit & Deterministic)".
# "We remove sub_agents from the Coordinator... The Coordinator is no longer 'aware' of the other agents".

# If the runner encounters a transfer to "data_analyst_agent", and it's not in `sub_agents`,
# how does it resolve it?
# The user said: "You do not need a manual dictionary if you use the ADK Runner correctly... runner = LocalRunner(agents=[...])".
# But `InMemoryRunner` (which seems to be the local runner in 1.17) does NOT accept a list.
# And `LocalRunner` class does not exist in 1.17 `google.adk.runtimes`.

# It's possible `LocalRunner` was renamed or I am looking at a different version than the user expected.
# But I am on 1.17.0.
# The user mentioned ">= 1.15.1 (or the latest stable 1.21.x)".

# Let's check `google.adk.apps.App`. Maybe `App` manages multiple agents?
# Or maybe we DO need to list them in `sub_agents` but use `tools=[route_request]` to FORCE the usage.
# If I list them in `sub_agents`, the framework knows them.
# The user said "CRITICAL: Remove this to disable stochastic routing".
# Maybe disabling stochastic routing means not giving the LLM the `transfer_to_agent` tool?
# But if we use `sub_agents`, ADK *automatically* adds it.

# Hypothesis: The user wants me to use `route_request` tool which explicitly returns a `Transfer` (or sets `transfer_to_agent`).
# BUT for the transfer to WORK, the destination agent must be known.
# If `InMemoryRunner` doesn't support a list, maybe we should use `sub_agents` but HIDE them from the prompt?
# Or maybe there is another Runner?

# Let's try to pass them as `sub_agents` to `coordinator` BUT maybe we can suppress the automatic tool?
# OR, we just follow the user's updated instruction: "Register ALL agents so the Runner can handle 'Transfer' signals".
# Since `InMemoryRunner` doesn't support list, I will try to use `App` wrapper if it exists and supports it.

from google.adk.apps import App

def main():
    """
    Sets up the Runner with the full roster of agents.
    """
    logger.info("Initializing VACP Financial Advisor System...")

    # We need to construct a runner that knows about all agents.
    # Since InMemoryRunner only takes one agent, we might need to rely on the Coordinator
    # having them as sub_agents to resolving them, but we want to force the router tool.

    # Workaround: Add them as sub_agents so the runtime works,
    # but use system instructions to IGNORE the built-in tool and use `route_request`.
    # AND/OR: Can we modify the coordinator to HAVE sub_agents but not expose them?

    # Re-importing coordinator to modify it at runtime if needed,
    # but better to do it in `agent.py` if that's the only way.

    # However, let's try to verify if `App` allows multiple agents.
    # `App` usually wraps an agent.

    # Let's stick to the user's "Router Tool" pattern.
    # If the runtime fails to find "data_analyst_agent", then we MUST register it.
    # If `InMemoryRunner` is the only runner and takes 1 agent,
    # then that agent (Coordinator) MUST be the parent.

    # I will modify `financial_advisor/agent.py` to include sub_agents
    # BUT I will try to ensure `route_request` is the primary method.
    # The user said "remove sub_agents... to disable stochastic routing".
    # If I add them back, I risk stochastic behavior.

    # Alternative: The "Transfer" object (or `actions.transfer_to_agent`) might work
    # if the Runner is smart enough or if we implement a custom loop.
    # But we are using standard `InMemoryRunner`.

    # Let's try to add sub_agents back to `coordinator` in `agent.py` but potentially
    # we can remove the *automatically added* transfer tool if ADK allows,
    # or just strongly prompt against it.

    # For now, I will modify `run_agent.py` to just run `coordinator`.
    # I will assume that `coordinator` needs to be updated to include sub_agents
    # so that the runtime can resolve them.
    # I will update `agent.py` in the next step if this fails or if I decide to do it now.

    # Let's update `run_agent.py` to be correct for `InMemoryRunner` first (single agent).

    runner = InMemoryRunner(agent=coordinator)

    # Note: If `coordinator` doesn't have sub_agents, transfer will likely fail
    # with "Agent not found" or similar.
    # I'll update `agent.py` to include them but maybe I can hide them?

    logger.info("System Ready. Entering interactive loop.")

    # CLI loop: reading from stdin
    # InMemoryRunner.run() is a generator yielding events.
    # We need to feed it.

    print("VACP Financial Advisor (type 'quit' to exit)")

    # We need to simulate a session.
    user_id = "test_user"
    session_id = "test_session"

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ("quit", "exit"):
                break

            print("Agent: ... processing ...")

            # Run the agent
            events = runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=user_input
            )

            for event in events:
                # We can inspect events here
                # print(event)
                if event.content and event.content.parts:
                    print(f"Agent: {event.content.parts[0].text}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
