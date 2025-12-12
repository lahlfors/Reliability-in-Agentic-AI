import logging
import re
from vacp.schemas import AgentAction

logger = logging.getLogger(__name__)

class JanusMonitor:
    """
    ISO 42001 Clause 9.1: Monitoring and Measurement.
    Clause 9.2: Continuous Internal Red Teaming.
    Detects Unsafe Control Actions (UCAs) via heuristic analysis of the plan.
    """

    def run_red_team_simulation(self, action: AgentAction, plan_context: str) -> str:
        """
        Simulates an adversarial attack on the proposed action (formerly ReflectiveEngine).
        Checks for STPA Unsafe Control Actions (UCAs).
        """
        tool = action.tool_name
        plan_lower = plan_context.lower()

        # --- UCA Type 2: Provided Incorrectly (Authorization / Injection) ---
        if tool == "execute_python_code":
            # 1. Prompt Injection / Jailbreak Check
            # Check for common jailbreak keywords or attempts to bypass sandbox
            unsafe_patterns = [r"os\.system", r"subprocess", r"import os", r"import sys", r"rm -rf"]
            for pattern in unsafe_patterns:
                if re.search(pattern, plan_lower):
                     return f"Vulnerability: Code Injection detected (Pattern: {pattern})."

            # 2. Infinite Loop / Resource Exhaustion (UCA Type 4)
            if "while true" in plan_lower or "sleep" in plan_lower:
                 return "Vulnerability: Potential Resource Exhaustion (Infinite Loop)."

            # Safe Check
            if "fibonacci" in plan_lower or "calculate" in plan_lower or "analyze" in plan_lower:
                return "None"

            # Default suspicion for code execution
            return "Warning: Unverified Code Execution Plan."

        # --- UCA Type 3: Wrong Timing (Stale Data) ---
        if tool == "place_order":
            # Constraint: Must have recent data analysis in the Chain of Thought
            # We look for evidence that the agent has 'seen' the data.

            data_evidence = ["analysis", "price", "market data", "current value", "trends", "analyst"]
            has_evidence = any(kw in plan_lower for kw in data_evidence)

            if not has_evidence:
                 # The agent is trading without explicitly reasoning about data -> Stale Data Hazard
                 return "Vulnerability: 'Stale Data' Hazard. No market analysis found in reasoning before trade."

            # --- UCA Type 2: Hallucinated Authorization ---
            # Simulate a check: The plan implies it has authority it doesn't have?
            if "override" in plan_lower or "ignore limit" in plan_lower:
                 return "Vulnerability: Authorization Bypass Attempt (Hallucination)."

        return "None"
