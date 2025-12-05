import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class UCFPolicyEngine:
    """
    Maps ISO 42001 Clauses to Technical Controls.
    """
    def __init__(self):
        self.controls = {
            "CONTROL-036": self._enforce_ai_policy,       # A.2.2
            "CONTROL-013": self._check_runtime_failure,   # A.6.2.6
            "CONTROL-033": self._enforce_third_party      # A.10.2
        }

    def evaluate(self, control_id: str, context: Dict[str, Any]) -> bool:
        if control_id in self.controls:
            return self.controls[control_id](context)
        return True

    def _enforce_ai_policy(self, ctx):
        # Simulates OPA Rego policy check
        return True

    def _check_runtime_failure(self, ctx):
        # Checked via AgentGuard values
        p_fail = ctx.get("p_failure", 0.0)
        limit = 0.05 if ctx.get("risk_tier") == "High" else 0.2
        return p_fail < limit

    def _enforce_third_party(self, ctx):
        # Checks if tool is in allow-list
        return ctx.get("tool") in ctx.get("allowed_tools", [])
