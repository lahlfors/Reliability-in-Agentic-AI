"""
The core decision-making component of the Metacognitive Control Subsystem.

This module implements the Deliberation Controller, which is responsible for
solving the metalevel control problem: deciding what the agent should do next.
It selects the optimal metalevel action (e.g., EXECUTE, REVISE, VETO) based
on the agent's current belief state and risk assessments.
"""
import json
import logging
import os
from typing import Dict, Any

from metacognitive_control_subsystem.mcs.api.schemas import DeliberateRequest, DeliberateResponse, ProposedAction
from metacognitive_control_subsystem.mcs.components.state_monitor import StateMonitor, BeliefState
from metacognitive_control_subsystem.mcs.components.risk_modeler import RiskConstraintModeler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeliberationController:
    """
    The 'brain' of the MCS, implementing the metalevel policy.
    """

    def __init__(self, constraints):
        """Initializes the Deliberation Controller."""
        logger.info("Deliberation Controller Initialized.")
        self.state_monitor = StateMonitor()
        self.risk_modeler = RiskConstraintModeler(constraints)
        self.policy = self._load_policy()

    def _load_policy(self):
        """Loads the trained policy from a file."""
        # Get the absolute path to the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the policy file, which is in the parent directory of the current directory.
        policy_path = os.path.join(current_dir, "..", "policy.json")
        try:
            with open(policy_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback for tests running in different directory structures
            policy_path = os.path.join(os.path.dirname(__file__), "..", "..", "policy.json")
            with open(policy_path, "r") as f:
                return json.load(f)


    def _execute_policy(self, belief_state: BeliefState, risks: Dict[str, float]) -> DeliberateResponse:
        """
        Executes the loaded policy.
        """
        for rule in self.policy["rules"]:
            if eval(rule["condition"], {"risks": risks}):
                decision = rule["action"]
                justification = f"Decision made based on rule: {rule['condition']}"
                return DeliberateResponse(
                    decision=decision,
                    parameters={},
                    justification=justification,
                    risk_assessment=risks
                )
        return DeliberateResponse(
            decision="EXECUTE",
            parameters={},
            justification="No rules matched, executing by default.",
            risk_assessment=risks
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

        belief_state = self.state_monitor.construct_belief_state(request.agent_state)
        risks = self.risk_modeler.evaluate_risks(request.agent_state)

        response = self._execute_policy(belief_state, risks)

        logger.info(f"Decision: {response.decision}. Justification: {response.justification}")
        return response
