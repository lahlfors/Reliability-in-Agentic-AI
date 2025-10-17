"""
Deployment script for the MCS Subsystem and the Financial Advisor Agent.

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
# Define the commands to run each server
MCS_COMMAND = [
    sys.executable, "-m", "uvicorn",
    "metacognitive_control_subsystem.mcs.api.server:app",  # <--- Corrected path
    "--host", "0.0.0.0",
    "--port", "8000",
]

# The `adk web` command serves the agent defined in the current directory.
# We need to run it from within the `financial-advisor` directory.
# We will also specify a different port to avoid conflicts.
FINANCIAL_ADVISOR_COMMAND = [
    "adk", "web", "--port", "8001"
]

# --- Main Execution ---

def run():
    """
    Launches and manages the deployment of all services.
    """
    processes = []
    print("--- Starting All Services ---")

    try:
        # Launch MCS Subsystem
        print("🚀 Launching MCS Safety Subsystem on port 8000...")
        mcs_process = subprocess.Popen(
            MCS_COMMAND,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(mcs_process)
        print(f"✅ MCS Subsystem process started with PID: {mcs_process.pid}")

        # Launch Financial Advisor Agent
        print("🚀 Launching Financial Advisor Agent on port 8001...")
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
