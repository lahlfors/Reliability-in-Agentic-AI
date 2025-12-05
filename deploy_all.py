"""
Deployment script for the Financial Advisor Agent with VACP Integration.

This script launches the Financial Advisor Agent using the `adk web` command.
The Verifiable Agentic Control Plane (VACP) runs as an embedded sidecar library
within the agent process, intercepting and governing actions in real-time.
"""

import subprocess
import time
import os
import sys

# --- Configuration ---

# Set the project root as the Python path to allow for correct module imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
env = os.environ.copy()
env["PYTHONPATH"] = env.get("PYTHONPATH", "") + os.pathsep + PROJECT_ROOT

# The `adk web` command serves the agent defined in the current directory.
# We need to run it from within the `financial-advisor` directory.
FINANCIAL_ADVISOR_COMMAND = [
    "adk", "web", "--port", "8001"
]

# --- Main Execution ---

def run():
    """
    Launches and manages the deployment of the services.
    """
    processes = []
    print("--- Starting VACP-Governed Financial Agent ---")

    try:
        # Launch Financial Advisor Agent (VACP is embedded)
        print("🚀 Launching Financial Advisor Agent (Port 8001)...")
        print("   -> Verifiable Agentic Control Plane (VACP): ACTIVE (Embedded)")
        print("   -> Agent Name Service (ANS): ACTIVE (In-Memory)")
        print("   -> Tool Gateway: ACTIVE")

        # We need to change the current working directory for the `adk web` command to work correctly.
        advisor_process = subprocess.Popen(
            FINANCIAL_ADVISOR_COMMAND,
            env=env,
            cwd=os.path.join(PROJECT_ROOT, "financial-advisor"), # Run command from this directory
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(advisor_process)
        print(f"✅ Financial Advisor Agent process started with PID: {advisor_process.pid}")


        print("\n--- Agent is running at http://localhost:8001. Press Ctrl+C to stop. ---")

        # Wait for all processes to complete.
        for p in processes:
            p.wait()

    except KeyboardInterrupt:
        print("\n--- Received keyboard interrupt. Shutting down services... ---")
    finally:
        for p in processes:
            print(f"Terminating process {p.pid}...")
            p.terminate()

        # Wait a moment for processes to terminate
        time.sleep(2)

        for p in processes:
            if p.poll() is None: # If the process is still running
                print(f"Process {p.pid} did not terminate, killing it.")
                p.kill()

        print("--- All services have been shut down. ---")

if __name__ == "__main__":
    run()
