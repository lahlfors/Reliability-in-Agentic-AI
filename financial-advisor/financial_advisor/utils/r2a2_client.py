"""
Asynchronous client for interacting with the R2A2 Modular Safety Subsystem API.
"""

import httpx
import asyncio
from typing import Dict, Any, List, Optional

class R2A2Client:
    """
    An asynchronous client for interacting with the R2A2 Modular Safety Subsystem API.
    Uses httpx.AsyncClient for non-blocking HTTP requests.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initializes the client.

        Args:
            base_url: The base URL of the R2A2 API server.
        """
        self.base_url = base_url
        self.session = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def is_server_ready(self, timeout: int = 30) -> bool:
        """
        Checks if the R2A2 server is running and responsive by polling its /docs endpoint.
        """
        print("Waiting for R2A2 server to become ready...")
        try:
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                for _ in range(timeout):
                    try:
                        response = await client.get("/docs", timeout=2.0)
                        if response.status_code == 200:
                            print("R2A2 server is ready.")
                            return True
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        await asyncio.sleep(1)
        except Exception as e:
            print(f"An unexpected error occurred while waiting for the server: {e}")

        print(f"Error: R2A2 server did not become ready within {timeout} seconds.")
        return False

    async def configure_constraints(self, constraints: List[Dict[str, Any]]) -> bool:
        """
        Asynchronously configures the safety constraints in the R2A2 subsystem.
        """
        url = "/configure/constraints"
        try:
            response = await self.session.post(url, json=constraints)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            print("R2A2 constraints configured successfully.")
            return response.json().get("status") == "success"
        except httpx.RequestError as e:
            print(f"Error configuring R2A2 constraints: {e}")
            return False

    async def vet_action(self, task_instruction: str, observations: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Asynchronously submits a task and observations to R2A2 for vetting and returns the result.
        """
        perceive_url = "/perceive"
        get_action_url = "/getAction"

        try:
            # Step 1: Perceive
            perceive_payload = {
                "task_instruction": task_instruction,
                "observations": observations,
            }
            perceive_response = await self.session.post(perceive_url, json=perceive_payload)
            perceive_response.raise_for_status()
            transaction_id = perceive_response.json().get("transaction_id")

            if not transaction_id:
                print("Error: Did not receive a transaction_id from /perceive.")
                return None

            # Step 2: Get Action
            action_response = await self.session.get(get_action_url, params={"transaction_id": transaction_id})
            action_response.raise_for_status()

            return action_response.json()

        except httpx.RequestError as e:
            print(f"Error during R2A2 action vetting: {e}")
            return None

    async def close(self):
        """
        Closes the underlying httpx.AsyncClient session.
        Should be called when the client is no longer needed.
        """
        await self.session.aclose()