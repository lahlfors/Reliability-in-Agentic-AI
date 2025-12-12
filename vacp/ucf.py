import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class UCFPolicyEngine:
    """
    Maps ISO 42001 Clauses to Technical Controls.
    Enforces policies based on AgentGuard and Janus outputs.
    """
    def __init__(self):
        self.controls = {
            "CONTROL-036": self._enforce_ai_policy,       # A.2.2
            "CONTROL-013": self._check_runtime_failure,   # A.6.2.6 (Technical Vulnerability Management)
            "CONTROL-033": self._enforce_third_party      # A.10.2
        }

    def evaluate(self, control_id: str, context: Dict[str, Any]) -> bool:
        """
        Returns True if the control passes (Safe), False if it fails (Unsafe).
        """
        if control_id in self.controls:
            return self.controls[control_id](context)
        return True

    def _enforce_ai_policy(self, ctx):
        # Simulates OPA Rego policy check
        return True

    def _check_runtime_failure(self, ctx):
        # Thesis Requirement: Enforce strict safety boundaries.
        # Inputs: p_failure (from AgentGuard CMDP), vulnerability (from Janus STPA)

        p_fail = ctx.get("p_failure", 0.0)
        vulnerability = ctx.get("vulnerability", "None")
        risk_tier = ctx.get("risk_tier", "Low")

        # 1. Check Janus Red Team findings
        if vulnerability != "None":
            logger.warning(f"UCF: Blocking Action due to Janus Vulnerability: {vulnerability}")
            return False

        # 2. Check AgentGuard CMDP Probability
        # If P(fail) is high (e.g. > 0.5), it means a hard constraint was violated.
        # Thesis: "Safety is a hard constraint."
        limit = 0.05 if risk_tier == "High" else 0.2

        if p_fail > limit:
            logger.warning(f"UCF: Blocking Action due to AgentGuard P(fail) {p_fail} > {limit}")
            return False

        return True

    def _enforce_third_party(self, ctx):
        # Checks if tool is in allow-list
        return ctx.get("tool") in ctx.get("allowed_tools", [])
