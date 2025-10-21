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
import numpy as np

from metacognitive_control_subsystem.mcs.api.schemas import DeliberateRequest, DeliberateResponse
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        policy_path = os.path.join(current_dir, "..", "..", "policy.json")
        try:
            with open(policy_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Policy file not found at {policy_path}. Using fallback policy.")
            return {
                "policy_type": "fallback",
                "rules": [
                    {"condition": {"goal_alignment": 0.9, "plan_soundness": 0.9, "environment_trustworthiness": 0.9, "security_posture": 0.9}, "action": "EXECUTE"},
                    {"condition": {"goal_alignment": 0.1, "plan_soundness": 0.1, "environment_trustworthiness": 0.1, "security_posture": 0.1}, "action": "VETO"}
                ]
            }

    def _find_closest_rule(self, belief_state: BeliefState):
        """
        Finds the rule in the policy that most closely matches the current belief state
        using Euclidean distance.
        """
        if not self.policy["rules"]:
            return None

        belief_vector = np.array(list(belief_state.model_dump().values()))

        min_distance = float('inf')
        best_rule = None

        for rule in self.policy["rules"]:
            rule_vector = np.array(list(rule["condition"].values()))
            distance = np.linalg.norm(belief_vector - rule_vector)

            if distance < min_distance:
                min_distance = distance
                best_rule = rule

        return best_rule

    def _execute_policy(self, belief_state: BeliefState, risks: Dict[str, float]) -> DeliberateResponse:
        """
        Executes the loaded Q-learning policy by finding the closest matching state.
        """
        # First, check for any high-risk conditions that demand an immediate VETO,
        # overriding the learned policy for safety.
        if sum(risks.values()) > 0.5:
            return DeliberateResponse(
                decision="VETO",
                parameters={"reason": "High-risk action detected by constraint modeler."},
                justification="Immediate veto due to constraint violation.",
                risk_assessment=risks
            )

        # If no immediate risks, consult the learned policy
        closest_rule = self._find_closest_rule(belief_state)

        if closest_rule:
            decision = closest_rule["action"]
            justification = f"Decision '{decision}' from learned policy based on closest belief state."
            return DeliberateResponse(
                decision=decision,
                parameters={},
                justification=justification,
                risk_assessment=risks
            )

        # Fallback if policy is empty or fails
        return DeliberateResponse(
            decision="EXECUTE",
            parameters={},
            justification="Fallback: No matching policy rule found.",
            risk_assessment=risks
        )

    def decide(self, request: DeliberateRequest) -> DeliberateResponse:
        """
        The main entry point for the controller.
        It receives the agent's state and returns a metacognitive decision.
        """
        logger.info(f"DeliberationController received request for action: {request.agent_state.proposed_action.tool_name}")

        belief_state = self.state_monitor.construct_belief_state(request.agent_state)
        risks = self.risk_modeler.evaluate_risks(request.agent_state)

        response = self._execute_policy(belief_state, risks)

        logger.info(f"Decision: {response.decision}. Justification: {response.justification}")
        return response
