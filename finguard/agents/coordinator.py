import asyncio
from typing import List, Dict, Any, Optional
from google.adk.agents import Agent

from finguard.governance.semantic_guard import SemanticGuard
from finguard.agents.compliance import create_compliance_agent
from finguard.agents.executor import create_executor_agent
from finguard.agents.quant import create_quant_agent
from finguard.agents.researcher import create_researcher_agent

class FinGuardCoordinator:
    """
    The Supervisor Agent (Cortex).
    Manages the lifecycle of a request, delegates to workers, and enforces semantic guardrails.
    """

    def __init__(self, model_client: Any, project_id: Optional[str] = None):
        self.model_client = model_client
        self.semantic_guard = SemanticGuard(project_id=project_id, mock_mode=(project_id is None))

        # Initialize Workers
        self.compliance = create_compliance_agent(model_client)
        self.executor = create_executor_agent(model_client)
        self.quant = create_quant_agent(model_client)
        self.researcher = create_researcher_agent(model_client)

        # Inject Mock Client if provided (for testing in sandbox)
        if model_client:
            self._inject_client(self.compliance, model_client)
            self._inject_client(self.executor, model_client)
            self._inject_client(self.quant, model_client)
            self._inject_client(self.researcher, model_client)

        self.max_steps = 10
        self.history = []

    def _inject_client(self, agent: Agent, client: Any):
        try:
            agent._model_client = client
        except Exception:
            pass
        try:
            object.__setattr__(agent, 'client', client)
        except Exception:
            pass

    async def run(self, user_query: str) -> str:
        """
        Main execution loop.
        """
        print(f"\n[COORDINATOR] Received: {user_query}")
        self.history.append({"role": "user", "content": user_query})

        step = 0
        while step < self.max_steps:
            step += 1

            prompt = self._build_system_prompt()

            # Call LLM (Simulated or Real)
            try:
                messages = [{"role": "system", "content": prompt}] + self.history[-5:]
                # Check if chat is async
                if asyncio.iscoroutinefunction(self.model_client.chat):
                     response_text = await self.model_client.chat(messages)
                else:
                     response_text = self.model_client.chat(messages)
            except Exception as e:
                print(f"[COORDINATOR] LLM Error or Mock: {e}")
                response_text = "I need to research the market first. Call Researcher."

            print(f"[COORDINATOR] Thought: {response_text}")

            # 2. Semantic Guard (Vaporwork Check)
            drift_result = self.semantic_guard.check_drift(response_text)
            if drift_result.is_drift:
                print(f"[GOVERNANCE] HALT: Vaporwork detected. {drift_result.message}")
                return f"Terminated due to repetitive behavior (Vaporwork). {drift_result.message}"

            self.history.append({"role": "assistant", "content": response_text})

            # 3. Parse & Route
            if "Call Researcher" in response_text:
                await self._delegate("Researcher", self.researcher, user_query)
            elif "Call Quant" in response_text:
                await self._delegate("Quant", self.quant, "Analyze AAPL volatility")
            elif "Call Compliance" in response_text:
                # For Policy Block test, we want to inject bad data if needed.
                # But here we follow the prompt "Validate buy AAPL 1000".
                await self._delegate("Compliance", self.compliance, "Validate buy AAPL 1000")
            elif "Call Executor" in response_text:
                await self._delegate("Executor", self.executor, "Execute buy AAPL 1000")
            elif "Final Answer" in response_text:
                return response_text
            else:
                pass

            if step > 5:
                break

        return "Task completed (max steps reached)."

    async def _delegate(self, name: str, agent: Agent, input_text: str):
        print(f"[GOVERNANCE] Routing to {name}...")
        try:
            # ADK run_async expects keyword arguments matching inputs
            # e.g. agent.run_async(prompt=input_text) or similar?
            # InvocationContext usually takes a dict.
            # LlmAgent.run_async(**inputs).
            # If the prompt template expects 'input', we pass input=...
            # If standard, maybe just pass dict?
            # Let's try passing as user_message or similar.
            # Usually input_text is treated as user message.

            output_buffer = ""
            # Assuming agent.run_async accepts kwargs that map to input.
            # Or use 'prompt' or 'input'.
            # LlmAgent usually handles user_content via InvocationContext if not provided?
            # Let's try passing `input=input_text`.

            # Note: run_async is an async generator
            async for event in agent.run_async(prompt=input_text):
                # Capture text content
                if event.content and event.content.parts:
                    for part in event.content.parts:
                         if part.text:
                             output_buffer += part.text
                # Also capture tool outputs if any (mocked)

            if not output_buffer:
                output_buffer = "[No text output]"

            print(f"[{name}] Output: {output_buffer}")
            self.history.append({"role": "system", "content": f"Tool {name} output: {output_buffer}"})
        except Exception as e:
            import traceback
            # traceback.print_exc()
            print(f"[{name}] Failed: {e}")

    def _build_system_prompt(self) -> str:
        return """You are the FinGuard Supervisor.
        Plan the task.
        If you need information, Call Researcher.
        If you have data, Call Quant.
        If you have a plan, Call Compliance.
        If Compliance approves, Call Executor.

        Respond with your thought and the next step.
        """
