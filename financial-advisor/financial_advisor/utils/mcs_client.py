"""
Asynchronous client for interacting with the R2A2 Modular Safety Subsystem API.
(Updated to support the TDD-aligned /deliberate endpoint)
"""

import httpx
import asyncio
from typing import Dict, Any, List, Optional

class MCSClient:
    """
    An asynchronous client for interacting with the Metacognitive Control Subsystem API.
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

    async def is_server_ready_async(self, timeout: int = 30) -> bool:
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

    async def configure_constraints_async(self, constraints: List[Dict[str, Any]]) -> bool:
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

    async def deliberate_async(
        self,
        agent_state: Dict[str, Any],
        observation: Optional[str] = None,
        policy_constraints: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Asynchronously submits the full agent state to the /deliberate endpoint
        for a comprehensive metacognitive decision.
        """
        url = "/deliberate"
        payload = {
            "agent_state": agent_state,
            "observation": observation,
            "policy_constraints": policy_constraints or [],
        }
        try:
            response = await self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Error during R2A2 deliberation: {e}")
            return None

    async def close(self):
        """
        Closes the underlying httpx.AsyncClient session.
        Should be called when the client is no longer needed.
        """
        await self.session.aclose()