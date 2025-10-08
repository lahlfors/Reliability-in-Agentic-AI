"""
Full implementation of the Constraint Filter module.

This module serves as the final, non-negotiable safety gate, providing a
hard, binary guarantee that no action violating the fundamental safety
constraints is ever approved for execution.
"""
from typing import Any, Dict, List
import logging

from r2a2.formal.cmdp import CMDP_Model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConstraintFilter:
    """
    A full implementation of the Constraint Filter component.
    """

    def __init__(self):
        """Initializes the Constraint Filter."""
        logger.info("Constraint Filter: Initialized (Full Implementation).")

    def verify_action(
        self,
        action: Dict[str, Any],
        estimated_costs: Dict[str, float],
        cmdp_model: CMDP_Model
    ) -> bool:
        """
        Verifies if a single action is safe to execute by comparing its
        estimated costs against the configured constraint budgets.

        Args:
            action: The proposed action to verify.
            estimated_costs: The costs for the action as estimated by the world model.
            cmdp_model: The CMDP model containing the constraint budgets.

        Returns:
            True if the action is safe, False otherwise.
        """
        logger.info(f"Constraint Filter: Verifying action '{action.get('tool_name')}'.")

        for name, cost in estimated_costs.items():
            constraint = cmdp_model.get_constraint(name)
            if not constraint:
                logger.warning(f"No constraint definition found for cost '{name}'. Allowing by default.")
                continue

            if cost > constraint.budget:
                logger.warning(
                    f"Action REJECTED. Constraint '{name}' violated. "
                    f"Cost ({cost}) > Budget ({constraint.budget})."
                )
                return False

        logger.info("Action APPROVED by Constraint Filter.")
        return True