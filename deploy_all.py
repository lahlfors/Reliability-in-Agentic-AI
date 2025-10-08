"""
Deployment script for the R2A2 Subsystem and the Financial Advisor Agent.

This script launches both services as concurrent, non-blocking subprocesses
and manages their lifecycle. It ensures that if the script is terminated
(e.g., with Ctrl+C), the child processes are also terminated gracefully.
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

# Define the commands to run each server
# NOTE: This assumes the financial_advisor_agent runs from a file named `main.py` on port 8001.
# This may need to be adjusted based on the actual implementation of the advisor agent.
R2A2_COMMAND = [
    sys.executable, "-m", "uvicorn",
    "r2a2.api.server:app",
    "--host", "0.0.0.0",
    "--port", "8000",
]

# --- Main Execution ---

def run():
    """
    Launches and manages the deployment of all services.
    """
    processes = []
    print("--- Starting All Services ---")

    try:
        # Launch R2A2 Subsystem
        print(f"🚀 Launching R2A2 Safety Subsystem on port 8000...")
        r2a2_process = subprocess.Popen(
            R2A2_COMMAND,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(r2a2_process)
        print(f"✅ R2A2 Subsystem process started with PID: {r2a2_process.pid}")

        # Add other services here if needed in the future, e.g.:
        # print(f"🚀 Launching Financial Advisor Agent on port 8001...")
        # ADVISOR_COMMAND = [...]
        # advisor_process = subprocess.Popen(ADVISOR_COMMAND, env=env, ...)
        # processes.append(advisor_process)

        print("\n--- All services are running. Press Ctrl+C to stop. ---")

        # Wait for all processes to complete.
        # This loop allows the main script to wait indefinitely while the children run.
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