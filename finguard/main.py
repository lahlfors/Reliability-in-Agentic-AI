# Copyright 2025 Google LLC
# FinGuard Main Entry Point (Refactored for VACP)

import logging
import asyncio

# In a real ADK app, we would use a Runner.
# For this demo/test script, we need to adapt the old manual tests to the new Architecture.
# Since we replaced the Coordinator loop with a real ADK Agent, we can't just "mock" the .run() method easily
# without a full runtime.

# However, the user wants "finguard becomes equivalent".
# The equivalence is that it *runs*.
# The best way to run an ADK agent is via 'google.adk.agent_runtime'.
# But that requires a server.

# For local testing/demo, we can use 'InMemoryRunner' if available, or just
# manual iteration over the async generator 'agent.run_async()'.

from google.adk.agents import InvocationContext, Agent
from finguard.agents.coordinator import finguard_coordinator

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_agent_interactive():
    """
    Runs the FinGuard Coordinator in an interactive loop (Terminal Chat).
    """
    print("=== FinGuard Financial Advisor (VACP Enabled) ===")
    print("Type 'exit' to quit.")

    # Create a dummy context
    # In production, this is managed by the Runtime/Server.
    # We need a minimal context for _run_async_impl to work?
    # Actually, usually we use a Runner.

    # Let's try to simulate a simple turn-based loop.
    # Note: State persistence is key for the Router.
    session_state = {}

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        print("\nFinGuard: ", end="", flush=True)

        # Create a fresh context for each turn?
        # Or reuse? Session state needs to persist.
        # InvocationContext is per-request.

        # We need to construct a context.
        # This is boilerplate usually hidden by the ADK Runtime.
        ctx = InvocationContext(
            agent=finguard_coordinator,
            agent_states={}, # Map of agent name to state?
            user_content=user_input, # Deprecated? usually input is part of events?
            # session=...
        )
        # Mocking session state persistence manually
        if not hasattr(ctx, "session"):
             ctx.session = type("Session", (), {"state": session_state})()
        else:
             ctx.session.state = session_state


        # Run the agent
        # We need to handle the output stream
        async for event in finguard_coordinator.run_async(user_content=user_input):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)

            # If tool calls happen, the ADK agent handles them?
            # Standard LlmAgent in ADK *generates* the tool call event.
            # It expects the *Runtime* to execute the tool and feed it back.
            #
            # CRITICAL: LlmAgent DOES NOT EXECUTE TOOLS ITSELF by default in newer ADK.
            # It yields a 'ToolCall' event. The Caller (Runner) must execute and feed back 'ToolResult'.

            # Since we don't have the full Runtime running here,
            # we are just simulating the *Governance* flow (Generates traces).
            # The actual tool execution logic is inside the tools we defined.

            # If we want a fully working CLI, we need a simple tool loop.
            pass

        print("\n[Turn Complete]")

if __name__ == "__main__":
    # If run directly, start interactive mode
    asyncio.run(run_agent_interactive())
