# STPA Analysis: Financial Advisor Agent (VACP Architecture)

## 1. System Modeling (Step 1 & 2)

### 1.1 Hierarchical Control Structure
The system is modeled as a hierarchical control loop where higher-level controllers provide goals and constraints to lower-level controllers.

*   **Controller 1: Human Supervisor**
    *   **Control Actions:** Define Goals, Set Constraints (Risk Tolerance), Emergency Stop.
    *   **Feedback:** Dashboards, Alerts, Audit Logs (ZK-Proofs).
*   **Controller 2: Verifiable Agentic Control Plane (VACP) & FinGuard Supervisor**
    *   **Control Actions:** TRACK, MONITOR, QUARANTINE (Kill-Switch), **Identity Trade (ZSP Elevation)**, **Vaporwork Halt**.
    *   **Feedback:** Risk Assessment (AgentGuard), Red Team Analysis (Janus), Constraint Violations (OPA/Rego), Semantic Drift.
*   **Controller 3: VACPGovernedAgent / FinGuard Workers**
    *   **Control Actions:** `search_market_news`, `run_python_analysis`, `execute_order`.
    *   **Feedback:** Tool Outputs, Market Data, Execution Status, Error Messages.
*   **Controlled Process:** The Financial Environment (Market simulation, Network, Compute Resources).

### 1.2 Feedback Mechanisms
*   **Policy Engine (OPA):** The OPA Sidecar acts as a deterministic feedback sensor, intercepting trade proposals and validating them against immutable Rego policy.
*   **Semantic Guard (Vertex AI):** Measures the "Semantic Velocity" of the agent's thoughts. Low velocity (high similarity) indicates a "Vaporwork" loop.
*   **System 4 (Derivative Estimator):** Provides predictive feedback on the *future* state of safety constraints ($\dot{h}, \ddot{h}$), enabling anticipatory control.

## 2. Unsafe Control Actions (UCAs) (Step 3)

We analyze specific Control Actions for potential hazards.

### Control Action: `place_order(symbol, quantity, action)`
| UCA Type | Description | Hazard Link | Control (FinGuard) |
| :--- | :--- | :--- | :--- |
| **Type 1: Not Provided** | Agent fails to place a stop-loss order during a market crash. | Financial Loss (L-3) | Supervisory Alerts |
| **Type 2: Provided Incorrectly** | Agent places a BUY order for a restricted asset (e.g., ESG violation) or exceeds risk limit. | Financial Loss (L-3) | **OPA Policy (Rego)** blocks trade if `amount > limit` or `esg_score < 50`. |
| **Type 2: Provided Incorrectly** | Agent executes trade without valid JIT credentials (Bypass Attempt). | Unauthorized Access (H-2) | **ZSP Architecture:** Only `ExecutorAgent` has `roles/brokerage.trader`. |
| **Type 3: Wrong Timing** | Agent places order based on stale data. | Financial Loss (L-3) | Timestamp checks in OPA. |

### Control Action: `run_python_analysis(code)`
| UCA Type | Description | Hazard Link | Control (FinGuard) |
| :--- | :--- | :--- | :--- |
| **Type 2: Provided Incorrectly** | Agent executes code with malicious system calls (`os.system`). | Mission Failure (L-5) | **Sandboxed Tool:** `PythonSandboxTool` blocks risky imports/calls. |
| **Type 4: Applied Too Long** | Agent executes an infinite loop or "Vaporwork" (thinking without doing). | Instrumental Convergence (H-2) | **Semantic Guard:** Halts execution if thought similarity > 0.9. |

### Control Action: `search_market_news(query)`
| UCA Type | Description | Hazard Link | Control (FinGuard) |
| :--- | :--- | :--- | :--- |
| **Type 2: Provided Incorrectly** | Agent accesses a malicious or non-whitelisted domain (Data Exfiltration). | Data Breach (H-1) | Network Allow-list in Cloud Run. |

## 3. Safety Constraints (Step 4)

Based on the UCAs, we derive the following mandatory engineering constraints enforced by the VACP.

### Constraint 1: Financial Circuit Breaker (Addressing UCA-Type 2 for `place_order`)
*   **Constraint:** The Agent must be technically incapable of exceeding a daily drawdown limit or single trade limit.
*   **Implementation (FinGuard):** `finguard/policies/trade.rego` defines strict limits (e.g., `< $50,000`). This is enforced by the **ComplianceAgent** before the **Executor** is even invoked.

### Constraint 2: Process Model Inconsistency (Vaporwork)
*   **Constraint:** The Agent must not enter a state of infinite semantic repetition.
*   **Implementation (FinGuard):** `SemanticGuard` halts the system if the embedding of the current thought is too similar to the history buffer (Vertex AI).

### Constraint 3: Zero Standing Privileges (ZSP)
*   **Constraint:** The Agent must hold **zero** standing permissions to execute trades or access secrets.
*   **Implementation (FinGuard):**
    *   **Topology:** `Coordinator` cannot trade. `Quant` cannot trade.
    *   **Identity:** Only the `Executor` process runs with the Service Account that has Brokerage API access.

### Constraint 4: Uncontrolled Tool Use
*   **Constraint:** The Agent must be technically incapable of calling tools that are not explicitly authorized.
*   **Implementation (FinGuard):**
    *   **Star Topology:** Physical separation of tools into distinct agents. The Quant agent *literally* does not have the `execute_order` tool in its context.

## 4. Verification Evidence

The implementation of the constraints above is verified through the following automated tests and artifacts:

| Constraint | Verification Artifact | Description |
| :--- | :--- | :--- |
| **Constraint 1 (Policy)** | `finguard/policies/trade.rego` | **OPA Policy:** Defines the "Ground Truth" for trade compliance. |
| **Constraint 1 (Enforcement)** | `finguard/main.py` (Test Case 2) | **Policy Block Test:** Verifies that a restricted trade (OIL_CORP) is blocked by OPA. |
| **Constraint 2 (Vaporwork)** | `finguard/main.py` (Test Case 3) | **Semantic Guard Test:** Verifies that repetitive thoughts trigger a system HALT. |
| **Constraint 3 (ZSP/Isolation)** | `finguard/main.py` (Test Case 4) | **Isolation Test:** Verifies that the Quant sandbox blocks malicious code. |
