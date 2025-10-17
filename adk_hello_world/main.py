"""
A minimal "Hello, World" agent to understand the core ADK framework.
This version includes the App wrapper to expose the agent as a web application.
"""
from typing import AsyncIterator, Any
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.apps import App

class HelloWorldAgent(BaseAgent):
    """A simple agent that says hello."""
    name: str

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncIterator[dict]:
        """The main execution method for the agent."""
        user_input = str(ctx.initial_user_content)
        yield {
            "output": f"Hello, World! You said: {user_input}",
            "is_final": True
        }

# 1. Instantiate the agent logic
hello_agent_impl = HelloWorldAgent(name="hello_world_agent")

# 2. Wrap the agent in an App object to expose it as a web service.
# The App requires a name and a root_agent.
root_agent = App(
    name="hello_world_app",
    root_agent=hello_agent_impl
)