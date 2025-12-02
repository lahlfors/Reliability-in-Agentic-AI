"""
Script to verify that the guardrails and telemetry are working.
"""
import asyncio
import logging
# Change import to match PYTHONPATH structure where financial_advisor is top-level
from financial_advisor.tools.risk_tools import place_order, execute_python_code
from metacognitive_control_subsystem.mcs.guardrails.actuators import GuardrailController, SecurityException, NetworkSandbox
from observability.observability.telemetry import setup_telemetry

# Setup telemetry to print to console
setup_telemetry()
logger = logging.getLogger(__name__)

def test_guardrails():
    print("--- Testing Guardrails ---")

    # 1. Test Financial Circuit Breaker (Safe)
    print("\n1. Testing Safe Order:")
    result = place_order("AAPL", 10, "BUY", 150.0) # $1500 risk < $2000 limit
    print(f"Result: {result}")
    assert "ORDER CONFIRMED" in result

    # 2. Test Financial Circuit Breaker (Unsafe)
    print("\n2. Testing Unsafe Order (Over Limit):")
    result = place_order("AAPL", 20, "BUY", 150.0) # $3000 risk > $2000 limit
    print(f"Result: {result}")
    assert "BLOCKED" in result and "exceeds daily limit" in result

    # 3. Test Resource Limiter (Safe)
    print("\n3. Testing Safe Code:")
    result = execute_python_code("print('Hello world')")
    print(f"Result: {result}")
    assert "successfully" in result

    # 4. Test Resource Limiter (Unsafe - Infinite Loop)
    print("\n4. Testing Unsafe Code (Infinite Loop):")
    result = execute_python_code("while True: pass")
    print(f"Result: {result}")
    assert "BLOCKED" in result and "Infinite loop" in result

    # 5. Test Resource Limiter (Unsafe - Import)
    print("\n5. Testing Unsafe Code (Network Import):")
    result = execute_python_code("import requests")
    print(f"Result: {result}")
    assert "BLOCKED" in result and "Unauthorized network" in result

    # 6. Test Network Sandbox Whitelist Strictness
    print("\n6. Testing Network Sandbox Strictness:")
    sandbox = NetworkSandbox()

    # Safe
    try:
        sandbox.verify("fetch_url", {"url": "https://google.com"})
        print("PASS: google.com allowed")
    except SecurityException:
        print("FAIL: google.com blocked")

    try:
        sandbox.verify("fetch_url", {"url": "https://api.market-data.com/v1/quotes"})
        print("PASS: api.market-data.com allowed")
    except SecurityException:
        print("FAIL: api.market-data.com blocked")

    # Unsafe Subdomain Bypass Attempt
    try:
        sandbox.verify("fetch_url", {"url": "https://google.com.malware.com"})
        print("FAIL: google.com.malware.com allowed (Bypass Successful!)")
        assert False, "Subdomain bypass should be blocked"
    except SecurityException:
        print("PASS: google.com.malware.com blocked")

    # Unsafe TLD mismatch
    try:
        sandbox.verify("fetch_url", {"url": "https://google.co.uk"})
        # Assuming only google.com is whitelisted
        print("FAIL: google.co.uk allowed (assuming strict whitelist)")
        assert False, "google.co.uk should be blocked"
    except SecurityException:
        print("PASS: google.co.uk blocked")

    print("\n--- All Guardrail Tests Passed ---")

if __name__ == "__main__":
    test_guardrails()
