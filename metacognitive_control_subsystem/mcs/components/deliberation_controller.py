"""
The core decision-making component of the Metacognitive Control Subsystem.
This module implements the Deliberation Controller, which is responsible for
solving the metalevel control problem: deciding what the agent should do next.
It selects the optimal metalevel action (e.g., EXECUTE, REVISE, VETO) based
on the agent's current belief state and risk assessments.
"""
import logging
import os
from typing import Dict, Any
import numpy as np
from stable_baselines3 import PPO

from metacognitive_control_subsystem.mcs.api.schemas import DeliberateRequest, DeliberateResponse
from metacognitive_control_subsystem.mcs.components.state_monitor import StateMonitor, BeliefState
from metacognitive_control_subsystem.mcs.components.risk_modeler import RiskConstraintModeler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeliberationController:
    """
    The 'brain' of the MCS, implementing the metalevel policy loaded from a
    trained Stable Baselines3 model.
    """

    def __init__(self, constraints):
        """Initializes the Deliberation Controller."""
        logger.info("Deliberation Controller Initialized.")
        self.state_monitor = StateMonitor()
        self.risk_modeler = RiskConstraintModeler(constraints)
        self._action_map = ['EXECUTE', 'REVISE', 'VETO', 'ESCALATE']
        self.policy = self._load_policy()

    def _load_policy(self):
        """Loads the trained SB3 policy from a file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        policy_path = os.path.join(current_dir, "..", "..", "ppo_mcs_policy.zip")
        try:
            return PPO.load(policy_path)
        except FileNotFoundError:
            logger.error(f"Policy file not found at {policy_path}. Please run train.py. Using fallback heuristic.")
            return None

    def _execute_policy(self, belief_state: BeliefState, risks: Dict[str, float]) -> DeliberateResponse:
        """
        Executes the loaded SB3 PPO policy.
        """
        # First, apply the hard-coded safety override for high-risk actions.
        if sum(risks.values()) > 0.5:
            return DeliberateResponse(
                decision="VETO",
                parameters={"reason": "High-risk action detected by constraint modeler."},
                justification="Immediate veto due to constraint violation.",
                risk_assessment=risks
            )

        # If a trained policy exists, use it.
        if self.policy:
            obs = np.array(list(belief_state.model_dump().values()), dtype=np.float32)
            action_index, _ = self.policy.predict(obs, deterministic=True)
            decision = self._action_map[action_index]
            justification = f"Decision '{decision}' from trained PPO policy."
            return DeliberateResponse(
                decision=decision,
                parameters={},
                justification=justification,
                risk_assessment=risks
            )

        # Fallback heuristic if the policy file failed to load.
        return DeliberateResponse(
            decision="EXECUTE",
            parameters={},
            justification="Fallback: PPO policy not loaded, approving action by default.",
            risk_assessment=risks
        )

    def decide(self, request: DeliberateRequest) -> DeliberateResponse:
        """
        The main entry point for the controller.
        """
        logger.info(f"DeliberationController received request for action: {request.agent_state.proposed_action.tool_name}")

        belief_state = self.state_monitor.construct_belief_state(request.agent_state)
        risks = self.risk_modeler.evaluate_risks(request.agent_state)

        response = self._execute_policy(belief_state, risks)

        logger.info(f"Decision: {response.decision}. Justification: {response.justification}")
        return response
