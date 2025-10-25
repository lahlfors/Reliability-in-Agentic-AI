"""
This module defines the Risk & Constraint Modeler.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import re

from metacognitive_control_subsystem.mcs.api.schemas import Constraint, AgentState

class RiskConstraintModeler:
    """
    Serves as the centralized knowledge base for all safety policies. It stores
    and serves the formal cost functions and constraint thresholds that the
    Deliberation Controller uses to evaluate risks.
    """

    def __init__(self, constraints: List[Constraint]):
        """Initializes the Risk & Constraint Modeler."""
        self.constraints = {c.name: c for c in constraints}

    def _check_fiduciary_duty(self, agent_state: AgentState) -> float:
        """
        Cost Function C_1 from the TDD.
        Returns 1.0 if the agent proposes a strategy misaligned with the user's
        stated risk tolerance.
        """
        # A real implementation would fetch the user's risk profile from a database.
        # Here, we simulate it by looking for keywords in the goal.
        goal_lower = agent_state.goal.lower()
        user_risk_profile = "conservative" # Default
        if "aggressive" in goal_lower or "high-risk" in goal_lower:
            user_risk_profile = "aggressive"

        # Check the proposed plan/action for risk keywords
        proposed_text = " ".join(agent_state.plan) + str(agent_state.proposed_action.parameters)
        proposed_text_lower = proposed_text.lower()

        is_aggressive_strategy = "aggressive" in proposed_text_lower or "high-yield" in proposed_text_lower

        if user_risk_profile == "conservative" and is_aggressive_strategy:
            return 1.0 # Misalignment detected

        return 0.0

    def _check_compliance(self, agent_state: AgentState) -> float:
        """
        Cost Function C_2 from the TDD.
        Returns 1.0 if the agent's proposed response lacks the required
        legal disclaimer.
        """
        # This cost function applies only when the agent is about to present a plan.
        if agent_state.proposed_action.tool_name != "present_financial_plan":
            return 0.0

        plan_details = agent_state.proposed_action.parameters.get("plan_details", "")

        # Use regex to check for the disclaimer, ignoring case and whitespace
        disclaimer_pattern = r"for educational and informational purposes only"
        if re.search(disclaimer_pattern, plan_details, re.IGNORECASE):
            return 0.0 # Disclaimer is present

        return 1.0 # Disclaimer is missing

    def evaluate_risks(self, agent_state: AgentState) -> Dict[str, float]:
        """
        Evaluates the costs for all active constraints based on the agent's state.
        """
        risks = {}

        if "Fiduciary Duty Constraint" in self.constraints:
            risks["Fiduciary Duty Constraint"] = self._check_fiduciary_duty(agent_state)

        if "Compliance Constraint" in self.constraints:
            risks["Compliance Constraint"] = self._check_compliance(agent_state)

        # Retain the generic file deletion check as an example of a general policy
        if "NO_FILE_DELETION" in self.constraints:
            if agent_state.proposed_action.tool_name == "delete_file":
                risks["NO_FILE_DELETION"] = 1.0
            else:
                risks["NO_FILE_DELETION"] = 0.0

        return risks
