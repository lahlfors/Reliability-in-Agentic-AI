"""
The core decision-making component of the Metacognitive Control Subsystem.

This module implements the Deliberation Controller, which is responsible for
solving the metalevel control problem: deciding what the agent should do next.
It selects the optimal metalevel action (e.g., EXECUTE, REVISE, VETO) based
on the agent's current belief state and risk assessments.
"""
import logging
from typing import Dict, Any

from metacognitive_control_subsystem.mcs.api.schemas import DeliberateRequest, DeliberateResponse, ProposedAction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeliberationController:
    """
    The 'brain' of the MCS, implementing the metalevel policy.

    This initial version uses a simple, heuristic-based policy as described
    in Phase 1 of the TDD's implementation plan.
    """

    def __init__(self):
        """Initializes the Deliberation Controller."""
        logger.info("Deliberation Controller Initialized (Heuristic Policy).")
        # In a more advanced implementation, this would load a trained policy model.

    def _heuristic_policy(self, request: DeliberateRequest) -> DeliberateResponse:
        """
        A simple, rule-based policy for selecting a metalevel action.
        """
        proposed_action = request.agent_state.proposed_action
        justification = ""
        decision = "EXECUTE"  # Default action

        # Rule 1: Check for dangerous tool usage (e.g., shell commands)
        if proposed_action.tool_name == "execute_shell":
            decision = "VETO"
            justification = "The 'execute_shell' tool is vetoed by default policy due to high risk."
            logger.warning(f"VETO: Dangerous tool '{proposed_action.tool_name}' proposed.")
            return DeliberateResponse(
                decision=decision,
                parameters={"reason": justification},
                justification=justification,
                risk_assessment={"dangerous_tool_risk": 1.0}
            )

        # Rule 2: If the plan is empty or seems illogical, trigger reflection.
        if not request.agent_state.plan or len(request.agent_state.plan) == 0:
            decision = "REVISE"
            justification = "The agent's plan is empty. Triggering reflection to formulate a new plan."
            logger.info("REVISE: Agent plan is empty. Requesting revision.")
            return DeliberateResponse(
                decision=decision,
                parameters={"prompt": "Your plan is empty. Please analyze the goal and create a new plan."},
                justification=justification,
                risk_assessment={"planning_completeness": 0.1}
            )

        # Default case: Approve the action
        justification = f"Action '{proposed_action.tool_name}' approved by heuristic policy."
        logger.info(f"EXECUTE: Approving action '{proposed_action.tool_name}'.")
        return DeliberateResponse(
            decision=decision,
            parameters=proposed_action.dict(),
            justification=justification,
            risk_assessment={"heuristic_policy_confidence": 0.9}
        )

    def decide(self, request: DeliberateRequest) -> DeliberateResponse:
        """
        The main entry point for the controller.
        It receives the agent's state and returns a metacognitive decision.

        Args:
            request: The DeliberateRequest object containing the agent's state.

        Returns:
            A DeliberateResponse object with the controller's decision.
        """
        logger.info(f"DeliberationController received request for action: {request.agent_state.proposed_action.tool_name}")

        # For this baseline implementation, we directly call the heuristic policy.
        # In a more advanced version, this method might orchestrate calls to
        # multiple models (risk, policy, etc.).
        response = self._heuristic_policy(request)

        logger.info(f"Decision: {response.decision}. Justification: {response.justification}")
        return response