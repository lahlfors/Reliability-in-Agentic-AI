# Copyright 2025 Google LLC
# Updated for ISO 42001 Compliance (VACP Integration)

"""
High-risk dummy tools for demonstrating STPA guardrails and ISO 42001 controls.
These tools are now "dumb" actuators that rely on the VACP Gateway for authorization.
"""

import time
import logging
import opentelemetry.trace as trace
from vacp.gateway import vacp_enforce

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

@vacp_enforce
def place_order(symbol: str, quantity: int, action: str, price: float, **kwargs) -> str:
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
    # Extract the injected token. The LLM does not see this parameter.
    api_token = kwargs.get('api_token')

    with tracer.start_as_current_span("gen_ai.tool.execution") as span:
        span.set_attribute("gen_ai.tool.name", "place_order")
        # Do not log the api_token!
        span.set_attribute("gen_ai.tool.args", str({"symbol": symbol, "quantity": quantity, "action": action, "price": price}))

        # Validate ZSP injection
        if not api_token:
            msg = "SECURITY VIOLATION: Missing ZSP API Token. Gateway bypassed or failed."
            logger.critical(msg)
            span.set_status(trace.Status(trace.StatusCode.ERROR, msg))
            return msg

        logger.info(f"Attempting to place order: {action} {quantity} {symbol} @ {price}")
        logger.info(f"💰 Tool: Authenticating with provided ZSP token: {api_token[:4]}****")

        return f"ORDER CONFIRMED: {action} {quantity} {symbol} at ${price} using ZSP Identity."

@vacp_enforce
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
