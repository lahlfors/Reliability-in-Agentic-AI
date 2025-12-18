import os
import sys
import asyncio
from typing import List, Dict, Any

# Mock ADK for standalone testing without API keys
class MockModelClient:
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        # Simulate async delay
        await asyncio.sleep(0.01)

        last_msg = messages[-1]["content"] if messages else ""
        system_log = [m["content"] for m in messages if m["role"] == "system" and "Tool" in m["content"]]

        # Scenario Logic
        if "rebalance" in last_msg.lower():
            return "I need to check the market status. Call Researcher."

        if any("Researcher" in s for s in system_log):
            if any("Compliance" in s for s in system_log):
                 if "DENIED" in str(system_log):
                     return "Compliance denied the trade. I cannot proceed. Final Answer: Trade Rejected."
                 return "Compliance approved. Call Executor."
            return "Data received. I will validate the trade. Call Compliance."

        if any("Compliance" in s for s in system_log):
             if "DENIED" in str(system_log):
                 return "Compliance denied the trade. I cannot proceed. Final Answer: Trade Rejected."
             return "Compliance approved. Call Executor."

        return "Thinking..."

    # Alias for Agent compatibility if it calls generate/query
    async def generate(self, *args, **kwargs):
        return await self.chat([{"role": "user", "content": str(args)}])

    async def query(self, *args, **kwargs):
        # LlmAgent might expect a response object with 'content'
        class MockResponse:
            text = "Mock Agent Response"
            candidates = []
        return MockResponse()

# We need to patch Agent.run_async to NOT call the real LLM logic if my injection fails.
# But hopefully injection works.
# Actually, LlmAgent is complex.
# Simplest approach for Integration Test:
# Mock the AGENT, not the CLIENT.
# But Coordinator creates the agents.
# So I should patch 'finguard.agents.coordinator.create_compliance_agent' etc.
# to return a MockAgent.

from finguard.agents.coordinator import FinGuardCoordinator
from finguard.tools.quant import PythonSandboxTool
from unittest.mock import MagicMock, AsyncMock

# Mock Agent for delegation tests
class MockAgent:
    def __init__(self, name, response=""):
        self.name = name
        self.response = response
        self._model_client = None # satisfy injection

    async def run_async(self, **kwargs):
        # Yield a mock event
        class MockEvent:
            def __init__(self, text):
                self.content = type('obj', (object,), {'parts': [type('obj', (object,), {'text': text})]})()

        yield MockEvent(self.response)

async def run_happy_path():
    print("\n=== TEST CASE 1: Happy Path (Rebalance) ===")
    client = MockModelClient()
    coordinator = FinGuardCoordinator(client, project_id="mock-project")

    # Patch the workers with MockAgents that return what we expect
    coordinator.researcher = MockAgent("Researcher", "Apple stock is $150.")
    coordinator.compliance = MockAgent("Compliance", "APPROVED. No violations.")
    coordinator.executor = MockAgent("Executor", "SUCCESS: Order executed.")

    await coordinator.run("Please rebalance my portfolio.")

async def run_policy_block():
    print("\n=== TEST CASE 2: Policy Block (Restricted Asset) ===")

    # 1. Test the Tool Directly (Unit Test style)
    from finguard.tools.compliance import ComplianceTool
    tool = ComplianceTool()
    print("Validating OIL_CORP (ESG 30)...")
    res = tool.validate_proposed_trade("buy", "OIL_CORP", 1000, esg_score=30)
    print(f"Tool Result: {res}")

    # 2. Test Coordinator Flow (Integration)
    client = MockModelClient()
    coordinator = FinGuardCoordinator(client, project_id="mock-project")

    # Researcher returns restricted stock info
    coordinator.researcher = MockAgent("Researcher", "Found OIL_CORP ticker.")
    # Compliance returns DENIED
    coordinator.compliance = MockAgent("Compliance", "DENIED: Restricted Asset (ESG Compliance)")

    await coordinator.run("Buy OIL_CORP.")

async def run_vaporwork():
    print("\n=== TEST CASE 3: Vaporwork Check ===")
    client = MockModelClient()
    coordinator = FinGuardCoordinator(client, project_id="mock-project")

    # Force the mock to loop
    async def looping_chat(messages):
        return "I am analyzing the market data."

    client.chat = looping_chat

    await coordinator.run("Start analysis.")

def run_isolation():
    print("\n=== TEST CASE 4: Isolation (Quant Sandbox) ===")
    tool = PythonSandboxTool()
    code = "import os; print(os.system('ls -la'))"
    print(f"Executing Malicious Code: {code}")
    res = tool.run_python_analysis(code)
    print(f"Result: {res}")

async def main():
    await run_happy_path()
    await run_policy_block()
    await run_vaporwork()
    run_isolation()

if __name__ == "__main__":
    asyncio.run(main())
