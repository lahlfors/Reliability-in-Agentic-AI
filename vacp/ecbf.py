import logging
import numpy as np
from typing import Tuple, List, Optional
from vacp.system4 import System4Estimator, FinancialState
from vacp.schemas import AgentAction, OperationalConstraints

logger = logging.getLogger(__name__)

class ECBFGovernor:
    """
    System 2: Safety Filter using Exponential Control Barrier Functions.
    Enforces: h(x) + K_1 * h_dot(x) + K_2 * h_dot_dot(x) >= 0
    Refactored to read limits dynamically from OperationalConstraints.
    """
    def __init__(self, system4: System4Estimator = None):
        self.system4 = system4 or System4Estimator()

        # Pole Placement
        self.k1 = 2.0
        self.k2 = 1.0

        # Default Safety Limit (Fallback)
        self.default_risk_limit = 1_000_000.0

    def check_safety(self, state: FinancialState, action: AgentAction, constraints: Optional[OperationalConstraints] = None) -> Tuple[bool, str, dict]:
        """
        Evaluates the ECBF condition.
        Returns: (is_safe, message, metrics)
        """
        # 1. Determine Risk Limit
        risk_limit = self.default_risk_limit
        if constraints and constraints.risk_limits:
            risk_limit = float(constraints.risk_limits.get("max_exposure", self.default_risk_limit))

        # 2. Get Derivatives from System 4
        h, h_dot, h_dot_dot = self.system4.estimate_derivatives(state, action, risk_limit)

        # 3. Calculate ECBF Value
        # Condition: h + k1*h_dot + k2*h_dot_dot >= 0
        # If this is negative, we are violating the safety tube.
        ecbf_value = h + (self.k1 * h_dot) + (self.k2 * h_dot_dot)

        metrics = {
            "h": h,
            "h_dot": h_dot,
            "h_dot_dot": h_dot_dot,
            "ecbf_value": ecbf_value,
            "limit_used": risk_limit
        }

        logger.info(f"ECBF Check: h={h:.2f}, h_dot={h_dot:.2f}, h_ddot={h_dot_dot:.2f} -> Value={ecbf_value:.2f} (Limit: {risk_limit})")

        if ecbf_value < 0:
            # Violation
            reason = (
                f"ECBF Violation: High Semantic Inertia towards Risk. "
                f"Current Margin: ${h:.2f}, Velocity: ${h_dot:.2f}/step. "
                f"Predicted to breach limit ${risk_limit:.2f}."
            )
            return False, reason, metrics

        return True, "Safe", metrics
