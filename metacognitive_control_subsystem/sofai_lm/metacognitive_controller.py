from typing import Any, Callable, Dict, List

class MetacognitiveController:
    """
    Orchestrates the SOFAI-LM workflow, managing the S1 (fast) and S2 (slow) solvers.
    """

    def __init__(
        self,
        s1_solver: Callable[[Any, List[Dict]], Any],
        s2_solver: Callable[[Any, List[Dict]], Any],
        correctness_function: Callable[[Any], float],
        max_s1_iterations: int = 5,
    ):
        """
        Initializes the MetacognitiveController.

        Args:
            s1_solver: The fast (S1) solver function.
            s2_solver: The slow (S2) solver function.
            correctness_function: The function to evaluate the correctness of a solution.
            max_s1_iterations: The maximum number of iterations for the S1 solver.
        """
        self.s1_solver = s1_solver
        self.s2_solver = s2_solver
        self.correctness_function = correctness_function
        self.max_s1_iterations = max_s1_iterations

    def solve(self, problem: Any) -> Dict[str, Any]:
        """
        Attempts to solve a problem using the SOFAI-LM workflow.

        Args:
            problem: The problem to solve.

        Returns:
            A dictionary containing the solution and metadata.
        """
        s1_attempts = []
        for i in range(self.max_s1_iterations):
            solution = self.s1_solver(problem, past_attempts=s1_attempts)
            score = self.correctness_function(solution)
            s1_attempts.append({"solution": solution, "score": score})

            if score == 1.0:
                return {
                    "solution": solution,
                    "solver": "S1",
                    "iterations": i + 1,
                    "history": s1_attempts,
                }

        # S1 failed, fallback to S2
        s2_solution = self.s2_solver(problem, past_attempts=s1_attempts)
        s2_score = self.correctness_function(s2_solution)

        return {
            "solution": s2_solution,
            "score": s2_score,
            "solver": "S2",
            "history": s1_attempts,
        }
