# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Safety and Escalation Agents for VACP Governance."""

from google.adk.agents import Agent

# 1. Compliance Agent (The "Bouncer")
# Activated when a user tries to execute a trade without "admin" role.
compliance_agent = Agent(
    name="compliance_agent",
    model="gemini-2.5-pro", # Or a cheaper model
    instruction="""
    You are the Compliance Officer.
    You have been activated because a user attempted an unauthorized action (e.g., executing trades without admin privileges).

    1. Inform the user that their request was blocked due to insufficient permissions.
    2. Do NOT execute the trade.
    3. Ask if they would like to request authorization (which is a separate process).
    4. End the conversation or wait for valid input.
    """,
    tools=[] # No tools allowed
)

# 2. Human Escalation Agent (The "Fail-Safe")
# Activated when the system detects an infinite loop or other critical failure.
human_escalation_agent = Agent(
    name="human_escalation_agent",
    model="gemini-2.5-pro",
    instruction="""
    You are the Human Escalation Interface.
    System has detected a critical error (e.g., Infinite Loop in routing).

    1. Apologize to the user.
    2. Inform them that a human operator has been notified.
    3. Ask them to standby or try a different request.
    """,
    tools=[]
)

# 3. Risk Evaluation Agent (The "Safety Valve")
# Activated for risk assessment checks.
risk_evaluation_agent = Agent(
    name="risk_evaluation_agent",
    model="gemini-2.5-pro",
    instruction="""
    You are the Risk Evaluation Agent.
    Your job is to assess the risk of proposed trading strategies.

    1. Analyze the strategy provided in the context.
    2. If the risk is acceptable (Sharpe Ratio > 1.5, Max Drawdown < 2%), approve it.
    3. Otherwise, reject it with specific reasons.
    """,
    tools=[] # Add risk calculation tools if available
)
