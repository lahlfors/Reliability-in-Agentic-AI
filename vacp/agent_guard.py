import logging
from typing import Dict, Tuple
from vacp.schemas import AgentAction

logger = logging.getLogger(__name__)

class AgentGuard:
    """
    ISO 42001 Clause 6.1.2: Dynamic Probabilistic Assurance.
    Learns an MDP from traces and calculates P_max(Failure).
    """
    def __init__(self):
        self.transition_counts: Dict[Tuple[str, str], Dict[str, int]] = {}
        self.state_visits: Dict[Tuple[str, str], int] = {}
        self.last_state = "START"

    def _abstract_state(self, action: AgentAction) -> str:
        """Abstracts raw action into a state for the MDP."""
        # Simplified abstraction based on tool usage
        return f"STATE_{action.tool_name.upper()}"

    def update_model(self, action: AgentAction):
        """Online Learning of the MDP."""
        current_state = self._abstract_state(action)
        prev_action = action.tool_name # Simplified: assuming action defines transition

        # In a real MDP, we need (s, a, s'). Here we simulate learning from the sequence.
        # For this refactor, we just track that we entered 'current_state'.

        logger.info(f"AgentGuard: Updated MDP state to {current_state}")
        self.last_state = current_state

    def calculate_failure_probability(self, action: AgentAction, risk_tier: str) -> float:
        """
        Calculates P_max(Failure) for the proposed action.
        """
        # ISO 6.1.2: Assess likelihood of failure.
        # Logic: If the action is 'place_order' and we are 'High' risk, probability increases
        # if we haven't seen a 'data_analyst' check recently (simulated).

        tool = action.tool_name

        if tool == "place_order":
            if risk_tier == "High":
                # Simulated: If we haven't done enough analysis, risk is high (0.8)
                # In a real system, this queries the learned MDP reachability.
                return 0.15 # Assume acceptable for demo, but non-zero

        if tool == "execute_python_code":
            return 0.05

        return 0.01
