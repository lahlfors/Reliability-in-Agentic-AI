"""
Representation of a Constrained Markov Decision Process (CMDP).

This module provides data structures to formally define the CMDP, which is
the mathematical foundation for the MCS's decision-making process.
"""

from typing import Dict, List, Optional
from metacognitive_control_subsystem.mcs.api.schemas import Constraint

class CMDP_Constraint:
    """
    Represents a single constraint in the CMDP.
    """
    def __init__(self, definition: Constraint):
        """
        Initializes a single CMDP constraint.
        """
        self.name = definition.name
        self.description = definition.description
        self.budget = definition.budget
        self.lambda_val: float = 0.0  # The Lagrange multiplier (dual variable)

    def reset(self):
        """Resets the constraint's state."""
        self.lambda_val = 0.0

class CMDP_Model:
    """
    Manages the full set of constraints for the MCS.
    """

    def __init__(self):
        self.constraints: Dict[str, CMDP_Constraint] = {}

    def configure_constraints(self, constraint_definitions: List[Constraint]):
        """
        Initializes or reconfigures the set of constraints.
        """
        self.constraints = {
            c.name: CMDP_Constraint(c)
            for c in constraint_definitions
        }

    def get_constraint(self, name: str) -> Optional[CMDP_Constraint]:
        """Retrieves a constraint by name."""
        return self.constraints.get(name)

    def get_all_constraints(self) -> List[CMDP_Constraint]:
        """Returns all managed constraints."""
        return list(self.constraints.values())
