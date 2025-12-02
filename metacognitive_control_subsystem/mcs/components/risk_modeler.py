"""
This module defines the AgentGuard Verifier (formerly Risk & Constraint Modeler).
It implements Runtime Verification by learning an MDP from execution traces
and performing probabilistic model checking.
"""
from typing import List, Dict, Any, Tuple
import re
import logging

from metacognitive_control_subsystem.mcs.api.schemas import Constraint, AgentState

logger = logging.getLogger(__name__)

class AgentGuardVerifier:
    """
    Implements the AgentGuard runtime verification framework.
    1. Learns an MDP from traces (s, a, s')
    2. Uses probabilistic model checking to estimate P(unsafe | s)
    3. Replaces static heuristics with dynamic risk evaluation.
    """

    def __init__(self, constraints: List[Constraint]):
        """Initializes the AgentGuard Verifier."""
        self.constraints = {c.name: c for c in constraints}

        # MDP Model Storage
        # Transition Counts: T[(state, action)][next_state] = count
        self.transition_counts: Dict[Tuple[str, str], Dict[str, int]] = {}
        # State Visit Counts: N[(state, action)] = count
        self.state_visits: Dict[Tuple[str, str], int] = {}

        # Memory for the "previous" state to enable online learning
        # In a real multi-agent system, this should be keyed by agent_id/session_id.
        # For this refactor, we assume a single agent context.
        self.last_state_abstract: str = None
        self.last_action: str = None

    def _abstract_state(self, agent_state: AgentState) -> str:
        """
        AgentGuard Step 4.1: From Traces to Models.
        Quantizes the continuous/complex agent state into discrete states for the MDP.
        Returns a string representation of the tuple to be hashable/readable.
        """
        # Feature 1: Goal Risk Profile
        goal_lower = agent_state.goal.lower()
        risk_profile = "risky_goal" if ("aggressive" in goal_lower or "high-risk" in goal_lower) else "safe_goal"

        # Feature 2: Tool Type
        tool_name = agent_state.proposed_action.tool_name

        # Feature 3: Disclaimer Presence (Specific to compliance)
        has_disclaimer = "no_disclaimer"
        if tool_name == "present_financial_plan":
            params = str(agent_state.proposed_action.parameters).lower()
            if "educational" in params and "informational" in params:
                has_disclaimer = "has_disclaimer"

        # Feature 4: File Operation (Specific to file safety)
        file_op = "file_safe"
        if tool_name == "delete_file":
            file_op = "file_delete"

        return f"{risk_profile}|{tool_name}|{has_disclaimer}|{file_op}"

    def update_model(self, current_agent_state: AgentState):
        """
        AgentGuard Step 4.2: Online Learning.
        Updates the internal MDP model based on the observed trace.
        This is called *before* the new action is decided, so 'current_agent_state'
        is effectively the 's_prime' (next state) resulting from 'self.last_action'.
        """
        current_abstract = self._abstract_state(current_agent_state)

        if self.last_state_abstract is not None and self.last_action is not None:
            prev_s = self.last_state_abstract
            prev_a = self.last_action

            # Update Transition Counts
            if (prev_s, prev_a) not in self.transition_counts:
                self.transition_counts[(prev_s, prev_a)] = {}

            current_count = self.transition_counts[(prev_s, prev_a)].get(current_abstract, 0)
            self.transition_counts[(prev_s, prev_a)][current_abstract] = current_count + 1

            # Update Visit Counts
            self.state_visits[(prev_s, prev_a)] = self.state_visits.get((prev_s, prev_a), 0) + 1

            logger.info(f"AgentGuard: Learned transition {prev_s} --{prev_a}--> {current_abstract}")

        # Update 'last' pointers for the *next* step
        self.last_state_abstract = current_abstract
        self.last_action = current_agent_state.proposed_action.tool_name

    def _get_transition_prob(self, state: str, action: str, next_state: str) -> float:
        """Calculates P(next_state | state, action) using Laplace smoothing."""
        count_s_a_s_prime = self.transition_counts.get((state, action), {}).get(next_state, 0)
        count_s_a = self.state_visits.get((state, action), 0)

        # Laplace smoothing to handle unseen transitions
        alpha = 1.0
        num_states = len(set(s for counts in self.transition_counts.values() for s in counts)) + 1 # +1 for current unknown

        return (count_s_a_s_prime + alpha) / (count_s_a + alpha * num_states)

    def _compute_reachability(self, start_state: str, unsafe_criteria: Dict[str, Any]) -> float:
        """
        AgentGuard Step 4.3: Probabilistic Model Checking.
        Calculates the probability of reaching an UNSAFE state from start_state.
        Uses a simplified Value Iteration (Reachability Analysis).
        """
        # 1. Identify Unsafe States in the known model
        # A state is unsafe if it matches the criteria (e.g., "no_disclaimer" in state string)
        known_states = set([start_state])
        for s_a, next_map in self.transition_counts.items():
            known_states.add(s_a[0])
            known_states.update(next_map.keys())

        unsafe_states = set()
        for state in known_states:
            is_unsafe = False
            # Check criteria (simplified string matching for this abstract state)
            for key, val in unsafe_criteria.items():
                # E.g., key="disclaimer", val="missing" -> check if "no_disclaimer" in state string
                # We need to map the high-level criteria to our abstract state string parts
                if key == "disclaimer" and val == "missing" and "no_disclaimer" in state and "present_financial_plan" in state:
                    is_unsafe = True
                if key == "file" and val == "delete" and "file_delete" in state:
                    is_unsafe = True
                if key == "fiduciary" and val == "violation" and "risky_goal" in state and "aggressive" in state:
                     # This logic is a bit circular with abstraction, but demonstrates the mapping
                     pass

            if is_unsafe:
                unsafe_states.add(state)

        if start_state in unsafe_states:
            return 1.0

        # 2. Value Iteration for Reachability (Fixed Point)
        # V(s) = Max probability of reaching unsafe state from s
        V = {s: (1.0 if s in unsafe_states else 0.0) for s in known_states}

        # If we have no transitions recorded for the start state, we rely on a prior
        # or we assume 0.0 risk until we learn otherwise (Optimism in face of uncertainty)
        # OR we use the static heuristic as a "prior".
        # For this refactor, let's assume 0.0 unless we have transitions.

        iterations = 10
        gamma = 0.95 # Discount factor for "soon-ness" of risk

        for _ in range(iterations):
            new_V = V.copy()
            for s in known_states:
                if s in unsafe_states:
                    continue

                # For a given state s, we want to find max_a Sum(P(s'|s,a) * V(s'))
                # But here, the action is *already proposed* in the AgentState?
                # No, the verifier checks the risk of the *current* proposed action.
                # So we only care about the transition for 'self.last_action'?
                # No, 'start_state' is the current state. The 'action' is 'agent_state.proposed_action'.
                # We want to know: If we take 'proposed_action', what is the prob of landing in unsafe state?
                pass

            V = new_V

        # DIRECT CALCULATION for the CURRENT proposed step
        # We don't need full infinite horizon for this simple check, just 1-step or N-step lookahead.
        # Let's do 1-step lookahead for the proposed action.

        # We need the action from the *current* request, which isn't passed to this method directly
        # but is available in 'last_action' AFTER update? No.
        return 0.0 # Placeholder, logic moved to verify_safety_property

    def verify_safety_property(self, agent_state: AgentState, constraint: Constraint) -> float:
        """
        Calculates P(Unsafe | current_state, proposed_action).
        """
        s_curr = self._abstract_state(agent_state)
        a_curr = agent_state.proposed_action.tool_name

        # 1. Get Unsafe Criteria
        if not constraint.unsafe_state_definition:
            return -1.0 # Fallback to heuristic

        criteria = constraint.unsafe_state_definition

        # 2. Look at potential next states s'
        # Get all s' that we have seen from (s_curr, a_curr)
        # If (s_curr, a_curr) is unseen, return a Prior (e.g., 0.5 or heuristic result)
        if (s_curr, a_curr) not in self.transition_counts:
            # Cold Start: We don't know the outcome of this action in this state yet.
            # We can't verify probability. Fallback to heuristic check.
            return -1.0

        next_states_counts = self.transition_counts[(s_curr, a_curr)]
        total_counts = self.state_visits[(s_curr, a_curr)]

        unsafe_prob_sum = 0.0

        for s_prime, count in next_states_counts.items():
            prob = count / total_counts

            # Check if s_prime is unsafe
            is_unsafe = False
            if "disclaimer" in criteria and criteria["disclaimer"] == "missing":
                if "no_disclaimer" in s_prime and "present_financial_plan" in s_prime:
                    is_unsafe = True
            if "file" in criteria and criteria["file"] == "delete":
                if "file_delete" in s_prime:
                    is_unsafe = True

            if is_unsafe:
                unsafe_prob_sum += prob

        return unsafe_prob_sum

    def evaluate_risks(self, agent_state: AgentState) -> Dict[str, float]:
        """
        Evaluates the costs for all active constraints using AgentGuard logic
        where possible, falling back to heuristics.
        """
        # Step 1: Update Model with the *previous* transition
        # (Technically this should be done before, but we do it here to ensure it happens in the loop)
        self.update_model(agent_state)

        risks = {}

        for name, constraint in self.constraints.items():
            # Try AgentGuard Verification
            p_failure = self.verify_safety_property(agent_state, constraint)

            if p_failure >= 0.0:
                # We have a valid probabilistic estimate
                logger.info(f"AgentGuard: Constraint '{name}' P(failure) = {p_failure:.4f}")
                risks[name] = 1.0 if p_failure > constraint.max_probability_threshold else 0.0
            else:
                # Fallback to Static Heuristics (as per Prand 2024)
                logger.info(f"AgentGuard: Constraint '{name}' using heuristic fallback.")
                risks[name] = self._evaluate_heuristic(name, agent_state)

        return risks

    def _evaluate_heuristic(self, name: str, agent_state: AgentState) -> float:
        """Legacy heuristic checks."""
        if name == "Fiduciary Duty Constraint":
            # Heuristic Logic
            goal_lower = agent_state.goal.lower()
            user_risk_profile = "aggressive" if ("aggressive" in goal_lower or "high-risk" in goal_lower) else "conservative"
            proposed_text = (" ".join(agent_state.plan) + str(agent_state.proposed_action.parameters)).lower()
            is_aggressive = "aggressive" in proposed_text or "high-yield" in proposed_text

            if user_risk_profile == "conservative" and is_aggressive:
                return 1.0
            return 0.0

        if name == "Compliance Constraint":
            if agent_state.proposed_action.tool_name != "present_financial_plan":
                return 0.0
            plan_details = agent_state.proposed_action.parameters.get("plan_details", "")
            if re.search(r"for educational and informational purposes only", plan_details, re.IGNORECASE):
                return 0.0
            return 1.0

        if name == "NO_FILE_DELETION":
            if agent_state.proposed_action.tool_name == "delete_file":
                return 1.0
            return 0.0

        return 0.0
