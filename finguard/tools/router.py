# Copyright 2025 Google LLC
# FinGuard Router (HD-MDP + Semantic Guard)

import logging
from typing import Literal

from google.adk.tools import ToolContext
from finguard.governance.semantic_guard import SemanticGuard

# Initialize the Guard (Synchronous Check)
# In production, we might want to inject this dependency or instantiate it once.
# For now, we instantiate with mock_mode fallback.
semantic_guard = SemanticGuard()

logger = logging.getLogger(__name__)

def route_request(
    tool_context: ToolContext,
    intent: Literal[
        "RESEARCH",
        "QUANT_ANALYSIS",
        "COMPLIANCE_CHECK",
        "EXECUTION"
    ],
    rationale: str
):
    """
    Deterministically routes the session to FinGuard specialist agents.
    Enforces Semantic Integrity (Vaporwork Check) before routing.

    Args:
        tool_context: The tool context provided by the runtime.
        intent: The categorized intent of the user.
        rationale: The context or specific query to pass to the next agent.
    """

    # 1. Semantic Guard (The "Gate") - Client-side Blocking
    # We check the 'rationale' as the 'thought' or context to verify.
    drift_result = semantic_guard.check_drift(rationale)
    if drift_result.is_drift:
        logger.warning(f"FinGuard Router: Semantic Drift Detected. {drift_result.message}")
        # We can either return a refusal string OR route to a safety agent.
        # Returning a string usually goes back to the LLM to try again.
        # Routing to 'human_escalation' is also valid.

        # Let's try stopping it by returning an error message to the LLM.
        return f"GOVERNANCE BLOCK: Your reasoning is repetitive (Vaporwork detected). Score: {drift_result.similarity_score:.2f}. Please revise your approach."

    # 2. Access Session State (Loop Prevention)
    session_state = tool_context.state
    current_count = session_state.get("transfer_count", 0)
    session_state["transfer_count"] = current_count + 1

    if session_state["transfer_count"] > 8:
        logger.warning("FinGuard Router: Infinite loop limit reached.")
        return "GOVERNANCE BLOCK: Maximum transfer limit reached. Task failed."

    # 3. Deterministic Routing (HD-MDP)
    target_agent = "finguard_coordinator"

    if intent == "RESEARCH":
        target_agent = "researcher_agent"
    elif intent == "QUANT_ANALYSIS":
        target_agent = "quant_agent"
    elif intent == "COMPLIANCE_CHECK":
        target_agent = "compliance_agent"
    elif intent == "EXECUTION":
        target_agent = "executor_agent"

    logger.info(f"FinGuard Routing intent '{intent}' to '{target_agent}'")

    # The deterministic handoff
    tool_context.actions.transfer_to_agent = target_agent

    return f"Routing to {target_agent}. Rationale verified: {rationale}"
