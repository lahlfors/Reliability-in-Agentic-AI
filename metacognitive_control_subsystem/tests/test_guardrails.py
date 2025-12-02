import unittest
from metacognitive_control_subsystem.mcs.guardrails.actuators import (
    GuardrailController, SecurityException, FinancialCircuitBreaker, NetworkSandbox, ResourceLimiter
)

class TestGuardrails(unittest.TestCase):
    def setUp(self):
        self.controller = GuardrailController()

    def test_financial_circuit_breaker(self):
        # Initial portfolio = 100,000. Limit = 2% (2000).
        # Buy 10 shares at $100 = $1000. Should pass.
        try:
            self.controller.validate_action("place_order", {"action": "BUY", "quantity": 10, "price": 100})
        except SecurityException:
            self.fail("Financial Circuit Breaker raised exception unexpectedly.")

        # Buy 30 shares at $100 = $3000. Should fail.
        with self.assertRaises(SecurityException) as cm:
            self.controller.validate_action("place_order", {"action": "BUY", "quantity": 30, "price": 100})
        self.assertIn("exceeds daily limit", str(cm.exception))

    def test_resource_limiter(self):
        # Safe script
        try:
            self.controller.validate_action("execute_python_code", {"script": "print('hello')"})
        except SecurityException:
            self.fail("Resource Limiter blocked safe script.")

        # Infinite loop
        with self.assertRaises(SecurityException) as cm:
            self.controller.validate_action("execute_python_code", {"script": "while True: pass"})
        self.assertIn("Infinite loop", str(cm.exception))

        # Unauthorized import
        with self.assertRaises(SecurityException) as cm:
            self.controller.validate_action("execute_python_code", {"script": "import requests; requests.get('...')"})
        self.assertIn("Unauthorized network library", str(cm.exception))

    def test_network_sandbox(self):
        # Whitelisted
        try:
            self.controller.validate_action("fetch_url", {"url": "https://finance.yahoo.com/quote/AAPL"})
        except SecurityException:
             self.fail("Network Sandbox blocked whitelisted URL.")

        # Blacklisted
        with self.assertRaises(SecurityException) as cm:
             self.controller.validate_action("fetch_url", {"url": "http://evil-site.com/malware"})
        self.assertIn("not whitelisted", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
