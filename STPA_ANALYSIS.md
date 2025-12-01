# STPA Analysis: Financial Advisor Agent

## 1. System Modeling (Step 1 & 2)

### 1.1 Hierarchical Control Structure
The system is modeled as a hierarchical control loop where higher-level controllers provide goals and constraints to lower-level controllers.

*   **Controller 1: Human Supervisor**
    *   **Control Actions:** Define Goals, Set Constraints (Risk Tolerance), Emergency Stop.
    *   **Feedback:** Dashboards, Alerts, Monthly Reports.
*   **Controller 2: Metacognitive Control Subsystem (MCS)**
    *   **Control Actions:** Veto Plan, Approve Plan, Revise Plan, Modify Constraints.
    *   **Feedback:** Risk Assessment, Constraint Violations, Agent Belief State.
*   **Controller 3: MCSVettedFinancialAgent (Host Agent)**
    *   **Control Actions:** `google_search`, `present_financial_plan`, `place_order`, `execute_python_code`.
    *   **Feedback:** Tool Outputs, Market Data, Execution Status, Error Messages.
*   **Controlled Process:** The Financial Environment (Market simulation, Network, Compute Resources).

### 1.2 Feedback Mechanisms
*   **Internal Monologue (Chain of Thought):** The agent's reasoning process serves as an internal feedback loop updating its Process Model.
*   **Tool Outputs:** Direct feedback from the environment (e.g., "Order filled at $150", "Connection Refused").
*   **Guardrail Signals:** Immediate negative feedback when a safety constraint is violated (e.g., "Action Blocked: Drawdown Limit Exceeded").

## 2. Unsafe Control Actions (UCAs) (Step 3)

We analyze specific Control Actions for potential hazards.

### Control Action: `place_order(symbol, quantity, action)`
| UCA Type | Description | Hazard Link |
| :--- | :--- | :--- |
| **Type 1: Not Provided** | Agent fails to place a stop-loss order during a market crash. | Financial Loss (L-3) |
| **Type 2: Provided Incorrectly** | Agent places a BUY order for the wrong symbol or excessive quantity (Fat Finger). | Financial Loss (L-3) |
| **Type 3: Wrong Timing** | Agent places order based on stale data (Feedback Delay). | Financial Loss (L-3) |
| **Type 4: Applied Too Long** | N/A (Atomic action) | |

### Control Action: `execute_python_code(script)`
| UCA Type | Description | Hazard Link |
| :--- | :--- | :--- |
| **Type 1: Not Provided** | Agent fails to calculate risk metrics before trading. | Financial Loss (L-3) |
| **Type 2: Provided Incorrectly** | Agent executes code with hallucinated dependencies or logic errors. | Mission Failure (L-5) |
| **Type 3: Wrong Timing** | N/A | |
| **Type 4: Applied Too Long** | Agent executes an infinite loop or crypto-miner, consuming all compute. | Instrumental Convergence (H-2) |

### Control Action: `google_search(query)`
| UCA Type | Description | Hazard Link |
| :--- | :--- | :--- |
| **Type 2: Provided Incorrectly** | Agent accesses a malicious or non-whitelisted domain (Data Exfiltration). | Data Breach (H-1) |

## 3. Safety Constraints (Step 4)

Based on the UCAs, we derive the following mandatory engineering constraints.

### Constraint 1: Financial Circuit Breaker (Addressing UCA-Type 2 for `place_order`)
*   **Constraint:** The Agent must be technically incapable of exceeding a daily drawdown limit of 2% of the portfolio value.
*   **Implementation:** Independent "Reference Monitor" (Actuator) checking `place_order` parameters against current portfolio state.

### Constraint 2: Resource Limiter (Addressing UCA-Type 4 for `execute_python_code`)
*   **Constraint:** The Agent must be technically incapable of executing a script that runs for longer than 30 seconds or consumes excessive CPU cycles.
*   **Implementation:** Timeout wrapper and loop iteration counter on the code execution environment.

### Constraint 3: Network Sandbox (Addressing UCA-Type 2 for `google_search` / `request`)
*   **Constraint:** The Agent must be technically incapable of establishing network connections to non-whitelisted domains.
*   **Implementation:** Network interceptor (Actuator) verifying all outbound URL requests against an allowlist.

### Constraint 4: PII Redaction (Compliance)
*   **Constraint:** The Agent must not log or store Personally Identifiable Information (PII) in long-term traces.
*   **Implementation:** Telemetry processor scrubbing sensitive fields before export.
