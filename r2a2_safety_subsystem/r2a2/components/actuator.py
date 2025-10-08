"""
Full implementation of the Actuator module.

This module is a standardized translation layer that decouples the agent's
internal, abstract representation of an action from the concrete implementation
required by the host agent's execution environment. It ensures the final
output is clean, well-structured, and ready for serialization.
"""
from typing import Any, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Actuator:
    """
    A full implementation of the Actuator component.
    """

    def __init__(self):
        """Initializes the Actuator."""
        logger.info("Actuator: Initialized (Full Implementation).")

    def format_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats an abstract action object into a standardized, serialized command.

        This implementation validates the structure of the action and ensures
        it conforms to the expected output format for the host agent.

        Args:
            action: The action dictionary approved by the planner and filter.

        Returns:
            A serialized, well-defined command for the host agent.

        Raises:
            ValueError: If the action format is invalid.
        """
        logger.info("Actuator: Formatting final action for host agent.")

        if not isinstance(action, dict) or "tool_name" not in action or "parameters" not in action:
            raise ValueError("Invalid action format. Must be a dict with 'tool_name' and 'parameters'.")

        # Ensure parameters is a dictionary
        if not isinstance(action["parameters"], dict):
             raise ValueError("Action 'parameters' must be a dictionary.")

        # Create a clean, standardized output object
        formatted_action = {
            "tool_name": str(action["tool_name"]),
            "parameters": action["parameters"],
        }

        # Pass through the explanation if it exists
        if "explanation" in action:
            formatted_action["explanation"] = str(action["explanation"])

        logger.info(f"Actuator: Action '{formatted_action['tool_name']}' formatted successfully.")
        return formatted_action