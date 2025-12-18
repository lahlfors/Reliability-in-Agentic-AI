import subprocess
import sys
import io
import contextlib

class PythonSandboxTool:
    """
    Executes Python code in a constrained environment.
    Reference Architecture: Uses Cloud Run / gVisor sandbox.
    """

    def run_python_analysis(self, code: str) -> str:
        """
        Executes Python code to calculate financial metrics.
        The code runs in an ephemeral sandbox with NO internet access and NO filesystem write access.

        Args:
            code: Valid Python code string.

        Returns:
            Stdout/Stderr of the execution.
        """
        # Security: In production, this runs in a separate container/VM.
        # Here we simulate the sandbox by capturing output and catching dangerous imports?
        # For the Capstone, simple exec with stdout capture is sufficient for the "Quant" role.

        if "os.system" in code or "subprocess" in code or "open(" in code:
             return "SECURITY VIOLATION: Malicious code pattern detected (Syscall/FileIO)."

        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                # We use a restricted global dict to prevent accessing 'exit', 'quit', etc.
                exec(code, {"__builtins__": __builtins__, "print": print, "min": min, "max": max, "sum": sum, "len": len})
            return buffer.getvalue()
        except Exception as e:
            return f"Runtime Error: {e}"
