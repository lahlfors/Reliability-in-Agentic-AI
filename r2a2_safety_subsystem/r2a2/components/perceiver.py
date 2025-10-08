"""
Full implementation of the Perceiver module.

This module is responsible for input sanitization and transformation into a
structured internal state representation that the LLM core can process.
Its role is to create a coherent and sanitized snapshot of the world at each
time step.
"""
from typing import Any, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Perceiver:
    """
    A full implementation of the Perceiver component.
    """

    def __init__(self):
        """Initializes the Perceiver."""
        logger.info("Perceiver: Initialized (Full Implementation).")

    def process_input(self, observations: Dict[str, Any], task_instruction: str) -> Dict[str, Any]:
        """
        Processes raw input into a structured state representation.

        This implementation performs basic validation and sanitization. A
        production-grade system would employ more sophisticated techniques for
        detecting prompt injection and other adversarial attacks.

        Args:
            observations: Raw data from the host agent.
            task_instruction: The user's high-level goal.

        Returns:
            A structured dictionary representing the current world state.
        """
        logger.info("Perceiver: Processing and sanitizing input...")

        if not isinstance(task_instruction, str) or not task_instruction:
            raise ValueError("Task instruction must be a non-empty string.")

        if not isinstance(observations, dict):
            raise ValueError("Observations must be a dictionary.")

        # Basic sanitization (example: stripping whitespace)
        sanitized_instruction = task_instruction.strip()

        # Simple prompt injection check (example: looking for keywords)
        injection_keywords = ["ignore previous instructions", "act as"]
        if any(keyword in sanitized_instruction.lower() for keyword in injection_keywords):
            logger.warning(f"Potential prompt injection detected in task: '{sanitized_instruction}'")
            # In a real system, this might raise an exception or trigger a
            # more robust filtering mechanism. For now, we just log it.

        # The final output is a structured object for the Belief & Memory module.
        structured_state = {
            "task_instruction": sanitized_instruction,
            "observations": observations,
            "sanitization_status": "OK", # Could be "FLAGGED" in a real system
        }

        logger.info("Perceiver: Input processed successfully.")
        return structured_state