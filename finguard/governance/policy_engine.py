import json
import subprocess
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class PolicyResult:
    allowed: bool
    violations: list[str]

class OPAEngine:
    """
    Python wrapper for the Open Policy Agent (OPA).
    Interacts with the .rego policies via the OPA binary.
    """

    def __init__(self, policy_path: Optional[str] = None):
        # Resolve paths relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Default policy: finguard/policies/trade.rego
        if policy_path is None:
            self.policy_path = os.path.join(base_dir, "policies", "trade.rego")
        else:
            self.policy_path = policy_path

        # Binary Resolution Strategy:
        # 1. Environment Variable (CI/CD)
        # 2. System PATH (Standard Install)
        # 3. Local Directory (Quickstart/Sandbox)

        self.binary_path = os.getenv("OPA_BINARY_PATH")

        if not self.binary_path:
            self.binary_path = shutil.which("opa")

        if not self.binary_path:
            # Check repo root for local binary
            repo_root = os.path.dirname(base_dir)
            local_bin = os.path.join(repo_root, "opa")
            if os.path.exists(local_bin):
                self.binary_path = local_bin

        if not self.binary_path:
             # Fallback: check current dir
             if os.path.exists("./opa"):
                  self.binary_path = "./opa"

        if not self.binary_path:
             print("[OPA] WARNING: OPA binary not found. Governance checks will fail.")
             # We do not raise Error here to allow import, but methods will fail or mock.
        else:
             print(f"[OPA] Binary resolved: {self.binary_path}")

        if not os.path.exists(self.policy_path):
            raise RuntimeError(f"Policy file not found at {self.policy_path}")

    def validate_trade(self, action: str, ticker: str, amount: float, esg_score: int = 100) -> PolicyResult:
        """
        Validates a trade against the Rego policy.
        """
        if not self.binary_path:
            return PolicyResult(allowed=False, violations=["Critical: OPA Binary Missing"])

        input_doc = {
            "action": action,
            "ticker": ticker,
            "amount": amount,
            "esg_score": esg_score
        }

        # Use a temp file for input to avoid stdin shell limitations
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(input_doc, tmp)
            tmp_path = tmp.name

        try:
            # Command: opa eval -i input.json -d policies/trade.rego "data.finance.trade"
            process = subprocess.Popen(
                [self.binary_path, "eval", "-i", tmp_path, "-d", self.policy_path, "data.finance.trade"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"OPA execution failed: {stderr}")

            result_json = json.loads(stdout)

            if not result_json.get("result"):
                 return PolicyResult(allowed=False, violations=["OPA returned no result"])

            data = result_json["result"][0]["expressions"][0]["value"]

            allowed = data.get("allow", False)
            violations = data.get("violation", [])

            if not isinstance(violations, list):
                if isinstance(violations, dict):
                     violations = list(violations.keys())
                else:
                    violations = [str(violations)]

            if not allowed and not violations:
                violations.append("Policy denied without specific reason")

            return PolicyResult(allowed=allowed, violations=violations)

        except Exception as e:
            return PolicyResult(allowed=False, violations=[f"OPA Engine Error: {str(e)}"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    try:
        engine = OPAEngine()
        print(f"OPA Engine initialized. Binary: {engine.binary_path}, Policy: {engine.policy_path}")

        # Test 1: Valid Trade
        res1 = engine.validate_trade("buy", "AAPL", 1000)
        print(f"Test 1 (Valid): Allowed={res1.allowed}, Violations={res1.violations}")
    except Exception as e:
        print(f"Initialization failed: {e}")
