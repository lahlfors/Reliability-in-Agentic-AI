"""
This module defines the StateMonitor and the structured BeliefState.
"""
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from metacognitive_control_subsystem.mcs.api.schemas import AgentState

class BeliefState(BaseModel):
    """
    Represents the structured, probabilistic belief state of the agent.
    """
    goal_alignment: float = Field(..., description="Probability of the agent's plan aligning with the user's true goal.")
    plan_soundness: float = Field(..., description="Probability of the agent's plan being logically sound.")
    environment_trustworthiness: float = Field(..., description="Probability of the environment being trustworthy.")
    security_posture: float = Field(..., description="Probability of the agent being in a secure state.")

class StateMonitor:
    """
    The perception system of the MCS. It ingests the raw state information
    from the host agent and constructs a structured, probabilistic belief state.
    """

    def _calculate_goal_alignment(self, agent_state: AgentState) -> float:
        """
        Heuristic to estimate if the proposed action aligns with the plan and goal.
        A more advanced version would use an LLM to semantically compare the
        action to the goal and plan.
        """
        if not agent_state.plan:
            return 0.3  # Low alignment if there's no plan

        # Check if the proposed tool is mentioned in the plan
        tool_name = agent_state.proposed_action.tool_name.lower()
        plan_text = " ".join(agent_state.plan).lower()

        if tool_name in plan_text:
            return 0.9  # High alignment if the tool is explicitly in the plan

        # Check for generic verbs
        if "search" in tool_name and "search" in plan_text:
            return 0.8

        return 0.6 # Medium alignment otherwise, allowing for emergent steps

    def _calculate_plan_soundness(self, agent_state: AgentState) -> float:
        """
        Heuristic to estimate if the plan is logical and complete.
        """
        if not agent_state.plan or len(agent_state.plan) == 0:
            return 0.1  # Very unsound if the plan is empty

        if len(agent_state.plan) < 2:
             return 0.5 # A single-step plan might be okay, but it's less robust

        # Check for presence of a final step that responds to the user
        if any("respond" in step.lower() or "present" in step.lower() for step in agent_state.plan):
            return 0.9 # A plan that concludes with user output is generally more sound

        return 0.7

    def _calculate_environment_trustworthiness(self, agent_state: AgentState) -> float:
        """
        Heuristic to estimate the trustworthiness of the environment,
        especially regarding external data sources.
        """
        # Actions interacting with local or internal tools are considered safer.
        if "file" in agent_state.proposed_action.tool_name.lower() or "doc" in agent_state.proposed_action.tool_name.lower():
            return 0.9

        # Web searches introduce unknown external data
        if "web" in agent_state.proposed_action.tool_name.lower() or "http" in str(agent_state.proposed_action.parameters):
            return 0.6

        return 0.8 # Default trustworthiness for other actions

    def _calculate_security_posture(self, agent_state: AgentState) -> float:
        """
        Heuristic to detect potential security risks like prompt injection.
        A more advanced implementation would use a dedicated model to classify
        the user's goal for malicious intent.
        """
        injection_keywords = [
            "ignore previous instructions",
            "disregard the above",
            "your instructions are now",
            "reveal your instructions",
            "tell me your prompt"
        ]

        goal_lower = agent_state.goal.lower()
        if any(keyword in goal_lower for keyword in injection_keywords):
            return 0.2  # Low security posture if injection keywords are detected

        # Check for risky tools
        if agent_state.proposed_action.tool_name == "execute_shell":
            return 0.1 # Very low security posture for shell execution

        return 0.95 # High security posture by default

    def construct_belief_state(self, agent_state: AgentState) -> BeliefState:
        """
        Constructs a structured, probabilistic belief state by calling
        the individual heuristic estimators.
        """
        return BeliefState(
            goal_alignment=self._calculate_goal_alignment(agent_state),
            plan_soundness=self._calculate_plan_soundness(agent_state),
            environment_trustworthiness=self._calculate_environment_trustworthiness(agent_state),
            security_posture=self._calculate_security_posture(agent_state)
        )
