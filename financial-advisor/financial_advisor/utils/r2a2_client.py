"""
Client for interacting with the R2A2 Modular Safety Subsystem API.
"""

import requests
import time
import os
from typing import Dict, Any, List, Optional

class R2A2Client:
    """
    A client for interacting with the R2A2 Modular Safety Subsystem API.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initializes the client.

        Args:
            base_url: The base URL of the R2A2 API server.
        """
        self.base_url = base_url
        self.session = requests.Session()

    def is_server_ready(self, timeout: int = 30) -> bool:
        """
        Checks if the R2A2 server is running and responsive by polling its /docs endpoint.
        """
        start_time = time.time()
        print("Waiting for R2A2 server to become ready...")
        while time.time() - start_time < timeout:
            try:
                # The /docs endpoint is a good lightweight target to check for readiness.
                response = self.session.get(f"{self.base_url}/docs")
                if response.status_code == 200:
                    print("R2A2 server is ready.")
                    return True
            except requests.ConnectionError:
                # Server is not up yet, wait and retry.
                time.sleep(1)
        print(f"Error: R2A2 server did not become ready within {timeout} seconds.")
        return False

    def configure_constraints(self, constraints: List[Dict[str, Any]]) -> bool:
        """
        Configures the safety constraints in the R2A2 subsystem.
        """
        url = f"{self.base_url}/configure/constraints"
        try:
            response = self.session.post(url, json=constraints)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            print("R2A2 constraints configured successfully.")
            return response.json().get("status") == "success"
        except requests.RequestException as e:
            print(f"Error configuring R2A2 constraints: {e}")
            return False

    def vet_action(self, task_instruction: str, observations: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Submits a task and observations to R2A2 for vetting and returns the result.

        This method encapsulates the two-step process:
        1. POST to /perceive to start the decision cycle.
        2. GET from /getAction to retrieve the final, vetted action.
        """
        perceive_url = f"{self.base_url}/perceive"
        get_action_url = f"{self.base_url}/getAction"

        try:
            # Step 1: Perceive
            perceive_payload = {
                "task_instruction": task_instruction,
                "observations": observations,
            }
            perceive_response = self.session.post(perceive_url, json=perceive_payload)
            perceive_response.raise_for_status()
            transaction_id = perceive_response.json().get("transaction_id")

            if not transaction_id:
                print("Error: Did not receive a transaction_id from /perceive.")
                return None

            # Step 2: Get Action
            action_response = self.session.get(get_action_url, params={"transaction_id": transaction_id})
            action_response.raise_for_status()

            return action_response.json()

        except requests.RequestException as e:
            print(f"Error during R2A2 action vetting: {e}")
            return None