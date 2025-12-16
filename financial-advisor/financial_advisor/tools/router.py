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

"""Router tool for deterministic agent transfer."""

import logging
from typing import Literal

# ADK Imports
# In ADK >= 1.15.1, 'Transfer' class might not exist or be needed if we use 'actions'.
# The user's prompt suggested 'google.adk.routing.Transfer', but my investigation showed
# 'google.adk.routing' does not exist in the installed version (1.17.0).
# However, 'google.adk.events.event_actions.EventActions' has a 'transfer_to_agent' field.
# And 'google.adk.tools.ToolContext.actions' returns 'EventActions'.

# To implement deterministic routing, we should use `tool_context.actions.transfer_to_agent`.
# This is the "System Tool" approach under the hood, but explicitly controlled.

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

def route_request(
    tool_context: ToolContext,
    intent: Literal[
        "MARKET_ANALYSIS",
        "STRATEGY_DEV",
        "EXECUTION_PLAN",
        "RISK_ASSESSMENT"
    ],
    rationale: str
):
    """
    Deterministically routes the session to the correct specialist agent based on intent.

    Args:
        tool_context: The tool context provided by the runtime.
        intent: The categorized intent of the user.
        rationale: The context or specific query to pass to the next agent.
    """

    # 1. Access Session State for Loop Prevention via ToolContext
    # ToolContext.state gives access to session state (delta-aware)
    session_state = tool_context.state

    # Initialize/Increment transfer count
    # Note: dictionary access on session_state might throw if key missing?
    # Usually it's a dict-like object.
    current_count = session_state.get("transfer_count", 0)
    session_state["transfer_count"] = current_count + 1

    logger.info(f"Router: Transfer count is {session_state['transfer_count']}")

    # --- Guardrail 1: Loop Prevention ---
    if session_state["transfer_count"] > 5:
        logger.warning("Router: Infinite loop detected. Escalin to human.")
        # Trigger transfer via actions
        tool_context.actions.transfer_to_agent = "human_escalation_agent"
        # We can also add metadata/context if supported, e.g. via custom_metadata or state
        session_state["error"] = "Infinite loop detected"
        return "Loop detected. Transferring to human."

    # --- Guardrail 2: Authorization (The "Gatekeeper") ---
    user_role = session_state.get("user_role", "analyst")

    # Check for EXECUTION_PLAN as it's the valid intent Literal. EXECUTE_TRADE was legacy.
    if intent == "EXECUTE_TRADE" or intent == "EXECUTION_PLAN":
        if user_role != "admin":
            logger.warning(f"Router: Unauthorized access attempt by {user_role}. Blocking.")
            tool_context.actions.transfer_to_agent = "compliance_agent"
            session_state["error"] = "Unauthorized: User lacks Admin privileges."
            return "Unauthorized. Transferring to compliance."

    # --- Standard Routing ---
    target_agent = "financial_coordinator"

    if intent == "MARKET_ANALYSIS":
        target_agent = "data_analyst_agent"
    elif intent == "STRATEGY_DEV":
        target_agent = "trading_analyst_agent"
    elif intent == "EXECUTION_PLAN":
        target_agent = "execution_analyst_agent"
    elif intent == "RISK_ASSESSMENT":
        target_agent = "risk_evaluation_agent"

    logger.info(f"Routing intent '{intent}' to '{target_agent}'")

    # The deterministic handoff:
    tool_context.actions.transfer_to_agent = target_agent

    # Pass context via session state or just return it (LLM will see return value)
    return f"Routing to {target_agent}. Rationale: {rationale}"
