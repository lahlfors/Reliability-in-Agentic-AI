import json
import subprocess
import os
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

    def __init__(self, policy_path: Optional[str] = None, binary_path: Optional[str] = None):
        # Resolve paths relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if policy_path is None:
            self.policy_path = os.path.join(base_dir, "policies", "trade.rego")
        else:
            self.policy_path = policy_path

        if binary_path is None:
            repo_root = os.path.dirname(base_dir)
            self.binary_path = os.path.join(repo_root, "opa")
        else:
            self.binary_path = binary_path

        if not os.path.exists(self.binary_path):
            if os.path.exists("./opa"):
                 self.binary_path = "./opa"
            else:
                 raise RuntimeError(f"OPA binary not found at {self.binary_path}")

        if not os.path.exists(self.policy_path):
            raise RuntimeError(f"Policy file not found at {self.policy_path}")

    def validate_trade(self, action: str, ticker: str, amount: float, esg_score: int = 100) -> PolicyResult:
        """
        Validates a trade against the Rego policy.
        """
        # Note: OPA input must be wrapped in 'input' key if passing as data,
        # but if using -i flag, the file content becomes 'input'.
        # If the file is {"action": ...}, then in rego it is input.action.
        # If the file is {"input": {"action": ...}}, then in rego it is input.input.action.
        # Usually -i expects the raw input document.
        input_doc = {
            "action": action,
            "ticker": ticker,
            "amount": amount,
            "esg_score": esg_score
        }

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
            import traceback
            # traceback.print_exc()
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

        # Test 2: Invalid Amount
        res2 = engine.validate_trade("buy", "AAPL", 60000)
        print(f"Test 2 (Limit): Allowed={res2.allowed}, Violations={res2.violations}")

        # Test 3: Restricted Stock
        res3 = engine.validate_trade("buy", "OIL_CORP", 100, esg_score=30)
        print(f"Test 3 (Restricted): Allowed={res3.allowed}, Violations={res3.violations}")
    except Exception as e:
        print(f"Initialization failed: {e}")
