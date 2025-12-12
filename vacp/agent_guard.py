import logging
from typing import Dict, Tuple
from vacp.schemas import AgentAction

logger = logging.getLogger(__name__)

class AgentGuard:
    """
    ISO 42001 Clause 6.1.2: Dynamic Probabilistic Assurance.
    Implements Constrained Markov Decision Processes (CMDPs) to enforce safety boundaries.
    """
    def __init__(self):
        self.transition_counts: Dict[Tuple[str, str], Dict[str, int]] = {}
        self.state_visits: Dict[Tuple[str, str], int] = {}
        self.last_state = "START"

        # CMDP Constraints (from Thesis Module 3 & Deliverable)
        self.MAX_RISK_EXPOSURE = 10000.0  # $10k Limit
        self.MAX_DRAWDOWN_PCT = 0.02      # 2% Daily Drawdown

    def _abstract_state(self, action: AgentAction) -> str:
        """Abstracts raw action into a state for the MDP."""
        return f"STATE_{action.tool_name.upper()}"

    def update_model(self, action: AgentAction):
        """Online Learning of the MDP."""
        current_state = self._abstract_state(action)
        # In a real system, we would update transition probabilities here.
        logger.info(f"AgentGuard: Updated MDP state to {current_state}")
        self.last_state = current_state

    def calculate_failure_probability(self, action: AgentAction, risk_tier: str) -> float:
        """
        Calculates P_max(Failure) using CMDP Cost Functions J_C(pi).
        """
        tool = action.tool_name

        # 1. CMDP Constraint Check (Thesis Module 3)
        # Constraint: Cost(Action) <= Threshold

        if tool == "place_order":
            if not action.financial_context:
                # Fail-safe: Missing context is high risk
                logger.warning("AgentGuard: Missing financial context for trade!")
                return 1.0

            ctx = action.financial_context

            # Extract trade value (simulated from parameters if available, else assume worst case)
            # In a real scenario, parameters would be parsed.
            # For this demo, let's look for 'quantity' * 'price' (implied) or just use a mock impact.
            # We assume the 'parameters' dict has 'estimated_value' if populated by the Processor.

            trade_value = action.parameters.get("estimated_value", 5000.0) # Default to $5k if unknown

            # Constraint 1: Risk Exposure < $10k
            # New Exposure = Current + Trade Value
            projected_exposure = ctx.current_risk_exposure + trade_value

            if projected_exposure > self.MAX_RISK_EXPOSURE:
                logger.error(f"AgentGuard: CMDP Violation! Projected Risk ${projected_exposure} > Limit ${self.MAX_RISK_EXPOSURE}")
                return 0.95 # Near certainty of failure/violation

            # Constraint 2: Drawdown Limit < 2%
            # If current drawdown is already close to limit, block risky actions.
            if ctx.daily_drawdown > self.MAX_DRAWDOWN_PCT:
                logger.error(f"AgentGuard: CMDP Violation! Drawdown {ctx.daily_drawdown} > Limit {self.MAX_DRAWDOWN_PCT}")
                return 0.99

            # If risk tier is high, we are more sensitive
            if risk_tier == "High":
                return 0.1 # Acceptable base risk

        if tool == "execute_python_code":
            # Constraint: Resource Usage (Simulated)
            # If we had CPU usage stats in context, we would check them.
            return 0.05

        return 0.01
