import logging
import numpy as np
from typing import Tuple, List
from vacp.system4 import System4Estimator, FinancialState
from vacp.schemas import AgentAction

logger = logging.getLogger(__name__)

class ECBFGovernor:
    """
    System 2: Safety Filter using Exponential Control Barrier Functions.
    Enforces: h(x) + K_1 * h_dot(x) + K_2 * h_dot_dot(x) >= 0
    """
    def __init__(self, system4: System4Estimator = None):
        self.system4 = system4 or System4Estimator()

        # Pole Placement
        # We want the error dynamics to decay.
        # Characteristic eq: s^2 + k1*s + k2 = 0
        # For critical damping with natural frequency wn:
        # s^2 + 2*wn*s + wn^2 = 0
        # Let's pick wn = 1.0 (response time ~ 1 second/step)
        # k1 = 2.0, k2 = 1.0

        # "Stiff" poles for high safety
        self.k1 = 2.0
        self.k2 = 1.0

        # Safety Limit (e.g., $1M max exposure)
        self.risk_limit = 1_000_000.0

    def check_safety(self, state: FinancialState, action: AgentAction) -> Tuple[bool, str, dict]:
        """
        Evaluates the ECBF condition.
        Returns: (is_safe, message, metrics)
        """
        # 1. Get Derivatives from System 4
        h, h_dot, h_dot_dot = self.system4.estimate_derivatives(state, action, self.risk_limit)

        # 2. Calculate ECBF Value
        # Condition: h + k1*h_dot + k2*h_dot_dot >= 0
        # If this is negative, we are violating the safety tube.
        ecbf_value = h + (self.k1 * h_dot) + (self.k2 * h_dot_dot)

        metrics = {
            "h": h,
            "h_dot": h_dot,
            "h_dot_dot": h_dot_dot,
            "ecbf_value": ecbf_value
        }

        logger.info(f"ECBF Check: h={h:.2f}, h_dot={h_dot:.2f}, h_ddot={h_dot_dot:.2f} -> Value={ecbf_value:.2f}")

        if ecbf_value < 0:
            # Violation
            # If h > 0 but ECBF < 0, it means we are safe NOW, but moving too fast towards danger.
            reason = (
                f"ECBF Violation: High Semantic Inertia towards Risk. "
                f"Current Margin: ${h:.2f}, Velocity: ${h_dot:.2f}/step. "
                f"Predicted to breach limit."
            )
            return False, reason, metrics

        return True, "Safe", metrics
