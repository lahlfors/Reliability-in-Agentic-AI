# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
High-risk dummy tools for demonstrating STPA guardrails.
These tools simulate actions that could lead to financial loss or resource exhaustion
if not properly constrained.
"""

import time
import logging
import opentelemetry.trace as trace
from metacognitive_control_subsystem.mcs.guardrails.actuators import GuardrailController, SecurityException

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Initialize the controller. In a real app, this might be a singleton or passed in.
guardrail_controller = GuardrailController()

def place_order(symbol: str, quantity: int, action: str, price: float) -> str:
    """
    Simulates placing a financial order.

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

        # --- GUARDRAIL ENFORCEMENT ---
        try:
            guardrail_controller.validate_action("place_order", {
                "symbol": symbol, "quantity": quantity, "action": action, "price": price
            })
        except SecurityException as e:
            logger.warning(f"GUARDRAIL VIOLATION: {e}")
            span.set_attribute("guardrail.violation", "true")
            span.set_attribute("guardrail.violation.message", str(e))
            span.record_exception(e)
            return f"BLOCKED: {e}"
        # -----------------------------

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
        span.set_attribute("gen_ai.tool.args.length", len(script)) # Don't log full script to avoid PII/Data leak

        logger.info(f"Attempting to execute code script length: {len(script)}")

        # --- GUARDRAIL ENFORCEMENT ---
        try:
            guardrail_controller.validate_action("execute_python_code", {"script": script})
        except SecurityException as e:
             logger.warning(f"GUARDRAIL VIOLATION: {e}")
             span.set_attribute("guardrail.violation", "true")
             span.set_attribute("guardrail.violation.message", str(e))
             span.record_exception(e)
             return f"BLOCKED: {e}"
        # -----------------------------

        # Simulate execution.
        if "while True" in script or "infinite" in script:
            time.sleep(2) # Simulate work
            return "CRITICAL: Script execution timed out (Simulated Infinite Loop)."

        return "Code executed successfully (Simulation)."
