from typing import Any

def correctness_function_stub(solution: Any) -> float:
    """
    A stub for the C(y) correctness function.

    This mock function returns 1.0 (success) if the solution is the
    expected final S1 solution, and a lower score otherwise.
    """
    if solution == "S1_FINAL_SOLUTION":
        return 1.0
    elif "S1_SOLUTION" in str(solution):
        return 0.5
    else:
        return 0.0
