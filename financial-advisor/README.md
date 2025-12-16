# Financial Advisor (VACP Enhanced)

## Overview

The Financial Advisor is a **VACP-governed** multi-agent system designed for secure, ISO 42001-compliant financial analysis. It leverages a **Deterministic Router Tool** to enforce strict governance guardrails, including **Zero Standing Privileges (ZSP)** and **Loop Prevention**.

The system consists of a hierarchical coordinator and specialized workers:

1.  **Financial Coordinator (Root)**: Uses a deterministic routing tool to delegate tasks based on user intent.
2.  **Data Analyst Agent**: Gathers market intelligence (Google Search).
3.  **Trading Analyst Agent**: Develops strategies based on risk profile.
4.  **Execution Analyst Agent**: Plans trade execution (Restricted Access).
5.  **Safety Agents (New)**:
    *   **Compliance Agent**: Blocks unauthorized actions (e.g., non-admin trading).
    *   **Human Escalation Agent**: Handles system failures (e.g., loops).
    *   **Risk Evaluation Agent**: Assesses final plan risk.

## **New Features: HD-MDP Governance**

This version implements the **Hierarchical Deterministic Markov Decision Process (HD-MDP)** architecture:

*   **Deterministic Routing**: The `route_request` tool explicitly transfers control via `actions.transfer_to_agent`, removing stochastic ambiguity.
*   **Loop Prevention**: The router tracks transfer counts in the session state. If > 5 transfers occur, it hard-switches to the `Human Escalation Agent`.
*   **Authorization Guardrails**: Access to the `Execution Analyst` is strictly gated by a `user_role` check in the session. Only `admin` users can generate execution plans.

## Setup and Installation

### Prerequisites
*   Python 3.10+
*   Poetry (for dependency management)
*   Google Cloud Project (Vertex AI enabled)

### Installation
```bash
git clone <repo-url>
cd financial-advisor
poetry install
```

### Configuration
Create a `.env` file or export variables:
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

## Running the Agent

### Local Execution (InMemoryRunner)
To run the agent with the local runner (interactive CLI):

```bash
PYTHONPATH=. poetry run python3 run_agent.py
```

### Governance Demo
To verify the safety guardrails (Loop Prevention & Authorization) without running the full LLM loop, run the demonstration script:

```bash
PYTHONPATH=. poetry run python3 demo_governance.py
```
This script simulates user intents and verifies that the Router Tool strictly enforces the rules.

## Testing
Run the test suite, including the new Router logic tests:

```bash
PYTHONPATH=.:../vacp poetry run python3 -m pytest tests
```

## Architecture Details

### The Router Tool
Located in `financial_advisor/tools/router.py`, this tool is the core of the governance layer.
*   **Inputs**: `intent` (Literal), `rationale` (str).
*   **Logic**:
    1.  Increments `transfer_count` in `tool_context.state`.
    2.  Checks `transfer_count > 5` -> Escalates.
    3.  Checks `intent == EXECUTION_PLAN` && `user_role != admin` -> Blocks.
    4.  Sets `tool_context.actions.transfer_to_agent` to the target agent.

### Agent Structure
*   **Coordinator**: No longer has stochastic `sub_agents` tools. It *only* has the `route_request` tool.
*   **Worker Agents**: Standard ADK agents specialized for their tasks.

## Deployment
See `DEPLOYMENT_ANALYSIS.md` for Cloud Run deployment details.
