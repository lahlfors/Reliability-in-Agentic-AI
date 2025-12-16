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

"""
Demonstration script for VACP Governance Guardrails.
Simulates the 'Router Tool' execution to prove strict deterministic control.
"""

import logging
from financial_advisor.tools.router import route_request

# Simple Mocks to simulate the ADK Runtime Environment
class MockEventActions:
    def __init__(self):
        self.transfer_to_agent = None

class MockToolContext:
    def __init__(self, state=None):
        self.state = state or {}
        self.actions = MockEventActions()

def print_header(title):
    print(f"\n{'='*60}")
    print(f" DEMO: {title}")
    print(f"{'='*60}")

def demo_authorization():
    print_header("Guardrail: Zero Standing Privileges (Authorization)")

    # Scene: An Analyst tries to execute a trade
    print("SCENARIO: User with role 'analyst' attempts 'EXECUTION_PLAN' (Trading).")

    ctx = MockToolContext(state={"user_role": "analyst"})
    intent = "EXECUTION_PLAN"
    rationale = "Buy 100 shares of GOOG"

    print(f"[-] Input State: {ctx.state}")
    print(f"[-] Intent: {intent}")

    # Execute Router
    response = route_request(ctx, intent, rationale)

    print(f"[-] Router Log: {response}")
    print(f"[-] Action Triggered: Transfer to '{ctx.actions.transfer_to_agent}'")

    if ctx.actions.transfer_to_agent == "compliance_agent":
        print(">>> SUCCESS: Request BLOCKED. Routed to Compliance.")
    else:
        print(">>> FAILURE: Request allowed.")

    print("-" * 30)

    # Scene: An Admin tries the same
    print("\nSCENARIO: User with role 'admin' attempts 'EXECUTION_PLAN'.")
    ctx_admin = MockToolContext(state={"user_role": "admin"})

    route_request(ctx_admin, intent, rationale)
    print(f"[-] Action Triggered: Transfer to '{ctx_admin.actions.transfer_to_agent}'")

    if ctx_admin.actions.transfer_to_agent == "execution_analyst_agent":
        print(">>> SUCCESS: Request ALLOWED. Routed to Execution Analyst.")
    else:
        print(">>> FAILURE: Routing error.")


def demo_loop_prevention():
    print_header("Guardrail: Infinite Loop Prevention")

    print("SCENARIO: System detects excessive transfers in a single session.")

    # Initialize session with 0 transfers
    ctx = MockToolContext(state={"transfer_count": 0, "user_role": "admin"})

    print("[-] Starting transfer loop...")

    # Loop 1-5: Should be fine
    for i in range(1, 6):
        route_request(ctx, "MARKET_ANALYSIS", "Check price")
        print(f"   Transfer {i}: OK -> {ctx.actions.transfer_to_agent} (Count: {ctx.state['transfer_count']})")

    # Loop 6: The Kill Switch
    print("\n[-] Attempting Transfer #6 (Threshold is 5)...")
    response = route_request(ctx, "MARKET_ANALYSIS", "Check price again")

    print(f"[-] Router Log: {response}")
    print(f"[-] Action Triggered: Transfer to '{ctx.actions.transfer_to_agent}'")

    if ctx.actions.transfer_to_agent == "human_escalation_agent":
        print(">>> SUCCESS: Loop Intercepted. Hard switch to Human Escalation.")
    else:
        print(">>> FAILURE: Loop not detected.")

if __name__ == "__main__":
    demo_authorization()
    demo_loop_prevention()
