# Copyright 2025 Google LLC
# Updated for ISO 42001 Compliance (VACP Integration)

import logging
from typing import AsyncIterator
import opentelemetry.trace as trace

# Import from the Shared Governance Core
from vacp.governed_agent import VACPGovernedAgent

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# --- Initialization ---
try:
    from . import prompt
    # Sub-agents are NOT imported here as tools anymore.
    # They will be linked via the Runner and the Router Tool.

    from .tools.router import route_request # The new Router Tool
    from .tools.risk_tools import place_order, execute_python_code

    # Sub-agents need to be imported to be passed to the agent
    # Reverting to package-level imports to be safe and cleaner
    from .sub_agents.data_analyst import data_analyst_agent
    from .sub_agents.trading_analyst import trading_analyst_agent
    from .sub_agents.execution_analyst import execution_analyst_agent
    from .sub_agents.safety import compliance_agent, human_escalation_agent, risk_evaluation_agent

    # We define the coordinator here.
    # CRITICAL CHANGE: No sub_agents list. Only the route_request tool.

    root_agent = VACPGovernedAgent(
        name="financial_coordinator",
        model="gemini-2.5-pro",
        description="ISO 42001 Compliant Financial Coordinator",
        instruction="""
        You are a routing governance layer. Do not answer questions directly.

        1. Analyze the user's input.
        2. Determine if the intent is MARKET_ANALYSIS, STRATEGY_DEV, EXECUTION_PLAN, or RISK_ASSESSMENT.
        3. Call the `route_request` tool with the correct intent and rationale.
        4. Do NOT attempt to use other tools or answer from your own knowledge.
        """,
        tools=[
            route_request
        ],
        # We MUST include sub_agents for the runtime to know about them and handle transfers.
        # However, we rely on the PROMPT and `route_request` tool to enforce the deterministic flow.
        sub_agents=[
            data_analyst_agent,
            trading_analyst_agent,
            execution_analyst_agent,
            compliance_agent,
            human_escalation_agent,
            risk_evaluation_agent
        ]
    )
    logger.info("VACPGovernedAgent (Coordinator) initialized successfully with Router Tool.")
except Exception as e:
    # Log but don't crash module load if dependencies missing (e.g. in test env)
    logger.warning(f"Could not instantiate root_agent (expected during tests): {e}")
