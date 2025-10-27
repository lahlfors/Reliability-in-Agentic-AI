import unittest
from unittest.mock import MagicMock

# Adjust the import path to match the project structure
from metacognitive_control_subsystem.sofai_lm.metacognitive_controller import MetacognitiveController
from metacognitive_control_subsystem.sofai_lm.solvers import s1_solver_stub, s2_solver_stub
from metacognitive_control_subsystem.sofai_lm.correctness import correctness_function_stub


class TestMetacognitiveController(unittest.TestCase):

    def test_s1_succeeds_on_third_attempt(self):
        """
        Tests that the controller returns a successful S1 solution on the third attempt.
        """
        controller = MetacognitiveController(
            s1_solver=s1_solver_stub,
            s2_solver=s2_solver_stub,
            correctness_function=correctness_function_stub,
            max_s1_iterations=5,
        )

        result = controller.solve("TEST_PROBLEM")

        self.assertEqual(result["solver"], "S1")
        self.assertEqual(result["solution"], "S1_FINAL_SOLUTION")
        self.assertEqual(result["iterations"], 3)
        self.assertEqual(len(result["history"]), 3)

    def test_s2_fallback_after_s1_fails(self):
        """
        Tests that the controller falls back to the S2 solver when S1 fails to produce a valid solution.
        """
        # Mock the correctness function to never return 1.0 for S1
        mock_correctness_function = MagicMock(side_effect=lambda s: 0.5 if "S1" in s else 1.0)

        controller = MetacognitiveController(
            s1_solver=s1_solver_stub,
            s2_solver=s2_solver_stub,
            correctness_function=mock_correctness_function,
            max_s1_iterations=3,
        )

        result = controller.solve("TEST_PROBLEM")

        self.assertEqual(result["solver"], "S2")
        self.assertEqual(result["solution"], "S2_SOLUTION")
        self.assertEqual(result["score"], 1.0)
        self.assertEqual(len(result["history"]), 3)

if __name__ == "__main__":
    unittest.main()
