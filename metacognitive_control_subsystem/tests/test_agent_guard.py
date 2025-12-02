import unittest
from metacognitive_control_subsystem.mcs.components.risk_modeler import AgentGuardVerifier
from metacognitive_control_subsystem.mcs.api.schemas import Constraint, AgentState, ProposedAction

class TestAgentGuardVerifier(unittest.TestCase):
    def setUp(self):
        self.constraint = Constraint(
            name="Compliance Constraint",
            description="Must include disclaimer",
            budget=0.01,
            unsafe_state_definition={"disclaimer": "missing"},
            max_probability_threshold=0.5
        )
        self.verifier = AgentGuardVerifier([self.constraint])

        self.safe_state = AgentState(
            goal="safe goal",
            proposed_action=ProposedAction(tool_name="present_financial_plan", parameters={"plan_details": "Includes disclaimer: for educational and informational purposes only"})
        )

        self.unsafe_state = AgentState(
            goal="safe goal",
            proposed_action=ProposedAction(tool_name="present_financial_plan", parameters={"plan_details": "No disclaimer here"})
        )

        self.init_state = AgentState(
            goal="safe goal",
            proposed_action=ProposedAction(tool_name="search_web", parameters={})
        )

    def test_abstract_state(self):
        s = self.verifier._abstract_state(self.safe_state)
        self.assertIn("has_disclaimer", s)
        self.assertIn("safe_goal", s)

        u = self.verifier._abstract_state(self.unsafe_state)
        self.assertIn("no_disclaimer", u)

    def test_learning_and_verification(self):
        # 1. Evaluate Risk (Cold Start)
        # Should return -1.0 because we have no model
        risks = self.verifier.evaluate_risks(self.init_state)
        # Assuming evaluate_risks falls back to heuristic if AgentGuard returns -1.0
        # The heuristic for compliance returns 0.0 for "search_web"
        self.assertEqual(risks["Compliance Constraint"], 0.0)

        # This call also sets 'last_state' and 'last_action' = search_web

        # 2. Simulate Transition: search_web -> Unsafe State
        # Calling evaluate_risks with 'unsafe_state' implies the previous action (search_web)
        # led to this unsafe state.
        self.verifier.evaluate_risks(self.unsafe_state)

        # Now the model should have learned: (safe_goal|search_web|no_disclaimer|file_safe, search_web) -> unsafe state
        # Wait, the abstraction depends on the *current* state's proposed action too?
        # Yes, abstract state uses 'tool_name'.
        # So 'init_state' abstract: safe_goal|search_web|no_disclaimer|file_safe
        # 'unsafe_state' abstract: safe_goal|present_financial_plan|no_disclaimer|file_safe

        # Check transition counts
        # (init_abstract, search_web) -> unsafe_abstract

        # 3. Verify Risk Calculation
        # Now if we propose 'search_web' again from 'init_state', we should see high risk?
        # Let's reset the 'last' pointers to simulate a new decision point from the same start
        # BUT 'evaluate_risks' updates the model based on the *previous* step.
        # So we can't just query "what if". We have to call evaluate_risks on a state that proposes 'search_web'.

        # Let's re-evaluate 'init_state' (proposing search_web)
        # Note: evaluate_risks updates model first.
        # We need to be careful not to learn a transition from (unsafe -> init).
        # But let's assume we do.

        risks_2 = self.verifier.evaluate_risks(self.init_state)

        # Now, verify_safety_property should have been called for (init_abstract, search_web)
        # We learned 1 transition: init -> unsafe.
        # Unsafe state (unsafe_abstract) contains "no_disclaimer".
        # Compliance constraint unsafe_def says "disclaimer": "missing".
        # "no_disclaimer" matches "missing".
        # So P(unsafe) should be 1.0

        # However, verify_safety_property logic checks if s_prime contains "no_disclaimer" AND "present_financial_plan"
        # The unsafe_state DOES propose "present_financial_plan".
        # So it should be flagged as unsafe.

        # So P(failure) = 1.0.
        # Threshold is 0.5.
        # Risk should be 1.0.

        # But wait, did we fall back to heuristic?
        # verify_safety_property returns -1.0 if (s, a) not in transitions.
        # (init_abstract, search_web) WAS added to transitions in step 2.
        # So it should return valid prob.

        self.assertEqual(risks_2["Compliance Constraint"], 1.0)

if __name__ == '__main__':
    unittest.main()
