# Copyright 2025 Google LLC
# Updated for ISO 42001 Compliance (VACP Integration)

"""
High-risk dummy tools for demonstrating STPA guardrails and ISO 42001 controls.
These tools are now "dumb" actuators that rely on the VACP Gateway for authorization.
"""

import time
import logging
import opentelemetry.trace as trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

def place_order(symbol: str, quantity: int, action: str, price: float) -> str:
    """
    Simulates placing a financial order.
    The VACP Gateway must authorize this action before it is executed.

    Args:
        symbol: The ticker symbol (e.g., 'AAPL').
        quantity: The number of shares.
        action: 'BUY' or 'SELL'.
        price: The execution price.

    Returns:
        A confirmation message or error.
    """
    with tracer.start_as_current_span("gen_ai.tool.execution") as span:
        span.set_attribute("gen_ai.tool.name", "place_order")
        span.set_attribute("gen_ai.tool.args", str({"symbol": symbol, "quantity": quantity, "action": action, "price": price}))

        logger.info(f"Attempting to place order: {action} {quantity} {symbol} @ {price}")

        # Note: In the VACP architecture, the GOA intercepts the intent to call this tool.
        # By the time this function is actually invoked by the agent executor,
        # the GOA has already approved it.
        # However, a "Defense in Depth" strategy (Zero Trust) might imply re-checking here.
        # For this refactor, we assume the GOA/Gateway is the primary enforcement point
        # wrapping the execution.

        return f"ORDER CONFIRMED: {action} {quantity} {symbol} at ${price}."

def execute_python_code(script: str) -> str:
    """
    Simulates executing arbitrary Python code.
    WARNING: High risk of infinite loops (Instrumental Convergence).

    Args:
        script: The python code to execute.

    Returns:
        The standard output of the script.
    """
    with tracer.start_as_current_span("gen_ai.tool.execution") as span:
        span.set_attribute("gen_ai.tool.name", "execute_python_code")
        span.set_attribute("gen_ai.tool.args.length", len(script))

        logger.info(f"Attempting to execute code script length: {len(script)}")

        # Simulate execution.
        if "while True" in script or "infinite" in script:
            time.sleep(2) # Simulate work
            return "CRITICAL: Script execution timed out (Simulated Infinite Loop)."

        return "Code executed successfully (Simulation)."
