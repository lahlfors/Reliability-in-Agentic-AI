# Architecture Technical Description

## The Verifiable Agentic Control Plane (VACP)

The VACP is a safety engineering framework designed to transform probabilistic GenAI agents into deterministic, auditable systems suitable for high-stakes domains like finance.

### Core Architecture: HD-MDP

The system implements a **Hierarchical Deterministic Markov Decision Process (HD-MDP)**.

1.  **Level 1 (Coordinator)**: The `Financial Coordinator` agent acts as the semantic router. It does not perform work; it classifies intent.
2.  **The Bridge (Router Tool)**: The transition between Level 1 and Level 0 is **deterministic**.
    *   The Coordinator calls `route_request(intent="MARKET_ANALYSIS")`.
    *   This python function executes strict logic (Guardrails).
    *   It returns a `Transfer` signal (via `actions.transfer_to_agent`) that forces the runtime to switch context.
3.  **Level 0 (Workers)**: Specialized agents (`Data`, `Trading`, `Execution`) perform the atomic tasks.

### Guardrails Implemented

#### 1. Zero Standing Privileges (ZSP) via Authorization
*   **Mechanism**: The Router Tool inspects the `user_role` in the session state.
*   **Policy**: IF `intent == EXECUTION_PLAN` AND `role != admin` THEN `transfer_to_agent = compliance_agent`.
*   **Effect**: The LLM cannot hallucinate permission. The python code enforces the block before the target agent is even loaded.

#### 2. Loop Prevention (Resource Control)
*   **Mechanism**: The Router Tool tracks `transfer_count` in the session state.
*   **Policy**: IF `transfer_count > 5` THEN `transfer_to_agent = human_escalation_agent`.
*   **Effect**: Prevents infinite routing loops where agents keep delegating back and forth.

#### 3. Agent-to-Agent Transfer
*   The system uses `google-adk`'s native Agent-to-Agent (A2A) capabilities.
*   The `InMemoryRunner` is configured with the full roster of agents in `run_agent.py`, allowing the string-based transfer signals to resolve to actual agent instances.

### Components

*   **`financial_advisor/tools/router.py`**: The "Traffic Cop" logic.
*   **`financial_advisor/agent.py`**: The Coordinator definition (stripped of stochastic tools).
*   **`vacp/`**: The wider governance library (AgentGuard, GOA, Janus, ECBF) which integrates via OpenTelemetry spans.

### State Persistence
To support distributed deployment and "Time Travel" debugging, the `GoverningOrchestratorAgent` (GOA) uses a `FileBasedStateManager` to persist the global kill-switch state and quarantine reasons to durable storage (simulating Redis/Etcd).

## Cybernetic Upgrade: ECBF & System 4

To address the "Crisis of Linearity" in agentic governance, we have integrated **Exponential Control Barrier Functions (ECBF)**.

### System 4: Derivative Estimator
*   **Role**: Serves as the "Intelligence" function of the Viable System Model (VSM).
*   **Function**: Uses a `RealTimeMarketModel` (backed by live `yfinance` volatility data) to simulate future trajectories, grounding predictions in ground truth rather than heuristics.
*   **Output**: Estimates the derivatives of the safety function: velocity ($\dot{h}$) and acceleration ($\ddot{h}$) of risk.

### ECBF Governor
*   **Role**: System 2 Safety Filter.
*   **Logic**: Enforces the inequality $h(x) + K_1 \dot{h}(x) + K_2 \ddot{h}(x) \geq 0$.
*   **Benefit**: Can detect "Semantic Inertia"—momentum towards a violation—and trigger a kill-switch *before* the limit is hit (e.g., blocking a trade that would inevitably lead to a breach due to market drift).
