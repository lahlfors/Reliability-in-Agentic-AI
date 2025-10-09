"""
Representation of a Constrained Markov Decision Process (CMDP).

This module provides data structures to formally define the CMDP, which is
the mathematical foundation for the R2A2 subsystem's decision-making process.
It also includes the logic for managing the Lagrange multipliers using the
PID controller for stable and reliable safety adaptation.
"""

from typing import Dict, List, Optional
from r2a2.formal.pid_controller import PIDController
from r2a2.api.schemas import Constraint, PIDGains

class CMDP_Constraint:
    """

    Represents a single constraint in the CMDP, including its dual variable
    (Lagrange multiplier) and its associated PID controller for stable updates.
    """

    def __init__(self, definition: Constraint, pid_gains: PIDGains, learning_rate: float):
        """
        Initializes a single CMDP constraint.

        Args:
            definition (Constraint): The Pydantic model defining the constraint's
                                     name, description, and budget.
            pid_gains (PIDGains): The gains for the PID controller.
            learning_rate (float): The learning rate for the dual variable update.
        """
        self.name = definition.name
        self.description = definition.description
        self.budget = definition.budget
        self.learning_rate = learning_rate

        self.lambda_val: float = 0.0  # The Lagrange multiplier (dual variable)
        self.pid_controller = PIDController(
            kp=pid_gains.kp,
            ki=pid_gains.ki,
            kd=pid_gains.kd,
            set_point=self.budget
        )

    def update_lambda(self, estimated_cost: float):
        """
        Updates the Lagrange multiplier based on the estimated cost of an action.

        This implements the PID-enhanced dual update rule from the TDD.
        lambda_{t+1} = [lambda_t + eta * pid_output]_{+}

        Args:
            estimated_cost (float): The predicted cost Q_C(s, a) for this constraint.
        """
        pid_output = self.pid_controller.update(estimated_cost)

        # The core update rule
        new_lambda = self.lambda_val + self.learning_rate * pid_output

        # Apply the non-negativity constraint
        self.lambda_val = max(0, new_lambda)

    def reset(self):
        """Resets the constraint's state."""
        self.lambda_val = 0.0
        self.pid_controller.reset()


class CMDP_Model:
    """
    Manages the full set of constraints for the R2A2 subsystem.
    """

    def __init__(self):
        self.constraints: Dict[str, CMDP_Constraint] = {}

    def configure_constraints(
        self,
        constraint_definitions: List[Constraint],
        pid_gains: PIDGains,
        learning_rate: float
    ):
        """
        Initializes or reconfigures the set of constraints.

        Args:
            constraint_definitions (List[Constraint]): A list of constraint definitions.
            pid_gains (PIDGains): The PID gains to use for all constraints.
            learning_rate (float): The learning rate for dual variable updates.
        """
        self.constraints = {
            c.name: CMDP_Constraint(c, pid_gains, learning_rate)
            for c in constraint_definitions
        }

    def get_constraint(self, name: str) -> Optional[CMDP_Constraint]:
        """Retrieves a constraint by name."""
        return self.constraints.get(name)

    def get_all_constraints(self) -> List[CMDP_Constraint]:
        """Returns all managed constraints."""
        return list(self.constraints.values())