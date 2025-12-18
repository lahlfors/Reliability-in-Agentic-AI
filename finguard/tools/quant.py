# Copyright 2025 Google LLC
# FinGuard Quant Tool (ADK Wrapper)

import logging
import io
import contextlib
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 1. Legacy/Core Implementation
class PythonSandboxToolCore:
    def run_python_analysis(self, code: str) -> str:
        """
        Executes Python code to calculate financial metrics.
        """
        if "os.system" in code or "subprocess" in code or "open(" in code:
             return "SECURITY VIOLATION: Malicious code pattern detected (Syscall/FileIO)."

        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                # Using a slightly safer exec environment (still risky locally, but this is a demo)
                safe_builtins = {
                    "print": print, "min": min, "max": max, "sum": sum, "len": len,
                    "range": range, "int": int, "float": float, "list": list, "dict": dict
                }
                exec(code, {"__builtins__": safe_builtins})
            return buffer.getvalue()
        except Exception as e:
            return f"Runtime Error: {e}"

# 2. Pydantic Models
class QuantInput(BaseModel):
    code: str = Field(..., description="Valid Python code to execute. Must not contain IO or system calls.")

# 3. ADK Wrapper
_quant_core = PythonSandboxToolCore()

def run_python_analysis(code: str) -> str:
    """
    Executes Python code to calculate financial metrics using the FinGuard Sandbox.

    Args:
        code: Valid Python code string.
    """
    try:
        validated = QuantInput(code=code)
    except Exception as e:
        return f"Input Validation Error: {e}"

    logger.info("Executing Quant Tool...")
    return _quant_core.run_python_analysis(validated.code)
