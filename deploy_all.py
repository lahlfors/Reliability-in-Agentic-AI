"""
Deployment script for the Financial Advisor Agent with VACP Integration.

This script launches the Financial Advisor Agent using the `adk web` command.
It is configured to be "Container-Ready" for deployment to Google Cloud Run:
- Binds to 0.0.0.0 (required for container ingress)
- Reads the PORT environment variable (required by Cloud Run contract)

The Verifiable Agentic Control Plane (VACP) runs as an embedded sidecar library
within the agent process.
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

# Cloud Run injects the PORT environment variable. Default to 8001 for local dev.
PORT = os.environ.get("PORT", "8001")

# The `adk web` command serves the agent defined in the current directory.
# We need to run it from within the `financial-advisor` directory.
FINANCIAL_ADVISOR_COMMAND = [
    "adk", "web",
    "--host", "0.0.0.0",
    "--port", PORT
]

# --- Main Execution ---

def run():
    """
    Launches and manages the deployment of the services.
    """
    processes = []
    print(f"--- Starting VACP-Governed Financial Agent on Port {PORT} ---")

    try:
        # Launch Financial Advisor Agent (VACP is embedded)
        print(f"🚀 Launching Financial Advisor Agent (0.0.0.0:{PORT})...")
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


        print(f"\n--- Agent is running at http://0.0.0.0:{PORT}. Press Ctrl+C to stop. ---")

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
