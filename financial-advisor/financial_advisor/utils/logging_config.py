"""
Logging configuration for the Financial Advisor agent.

This module provides a standardized logging setup for the application.
Importing this module will automatically configure the root logger.
"""

import logging
import sys

def setup_logging():
    """
    Configures the root logger for the application.

    This setup provides structured, timestamped logs that are easy to read
    and parse. It directs all logs to standard output.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True  # Overwrite any existing configuration
    )
    # You can set the level of third-party libraries here if they are too noisy.
    # For example, to quiet down the noisy ADK startup warnings:
    logging.getLogger("google.adk").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Call setup_logging() when this module is imported to apply the configuration.
setup_logging()