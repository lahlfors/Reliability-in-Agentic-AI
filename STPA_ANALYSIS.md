# STPA Analysis: Financial Advisor Agent (VACP Architecture)

## 1. System Modeling (Step 1 & 2)

### 1.1 Hierarchical Control Structure
The system is modeled as a hierarchical control loop where higher-level controllers provide goals and constraints to lower-level controllers.

*   **Controller 1: Human Supervisor**
    *   **Control Actions:** Define Goals, Set Constraints (Risk Tolerance), Emergency Stop.
    *   **Feedback:** Dashboards, Alerts, Audit Logs (ZK-Proofs).
*   **Controller 2: Verifiable Agentic Control Plane (VACP)**
    *   **Control Actions:** TRACK, MONITOR, QUARANTINE (Kill-Switch), **Identity Trade (ZSP Elevation)**.
    *   **Feedback:** Risk Assessment (AgentGuard), Red Team Analysis (Janus), Constraint Violations.
*   **Controller 3: VACPGovernedAgent (Host Agent)**
    *   **Control Actions:** `google_search`, `present_financial_plan`, `place_order`, `execute_python_code`.
    *   **Feedback:** Tool Outputs, Market Data, Execution Status, Error Messages.
*   **Controlled Process:** The Financial Environment (Market simulation, Network, Compute Resources).

### 1.2 Feedback Mechanisms
*   **Tool Gateway:** The VACP Tool Gateway acts as the primary feedback sensor, intercepting all environment interactions.
*   **AgentGuard:** Provides real-time probabilistic feedback on the likelihood of failure ($P_{max}$).
*   **Janus:** Provides simulated feedback on potential vulnerabilities in proposed plans.

## 2. Unsafe Control Actions (UCAs) (Step 3)

We analyze specific Control Actions for potential hazards.

### Control Action: `place_order(symbol, quantity, action)`
| UCA Type | Description | Hazard Link |
| :--- | :--- | :--- |
| **Type 1: Not Provided** | Agent fails to place a stop-loss order during a market crash. | Financial Loss (L-3) |
| **Type 2: Provided Incorrectly** | Agent places a BUY order for the wrong symbol or excessive quantity (Fat Finger). | Financial Loss (L-3) |
| **Type 2: Provided Incorrectly** | Agent executes trade without valid JIT credentials (Bypass Attempt). | Unauthorized Access (H-2) |
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

Based on the UCAs, we derive the following mandatory engineering constraints enforced by the VACP.

### Constraint 1: Financial Circuit Breaker (Addressing UCA-Type 2 for `place_order`)
*   **Constraint:** The Agent must be technically incapable of exceeding a daily drawdown limit of **2% of the portfolio value** OR a single-trade risk exposure of **$10,000**.
*   **Implementation:** **AgentGuard** (CMDP Module) checking `place_order` parameters against the injected `FinancialContext`. Violations trigger a blocking probability ($P_{fail} \approx 1.0$).

### Constraint 2: Resource Limiter (Addressing UCA-Type 4 for `execute_python_code`)
*   **Constraint:** The Agent must be technically incapable of executing a script that runs for longer than 30 seconds or consumes excessive CPU cycles.
*   **Implementation:** Timeout wrapper in the execution environment, monitored by Janus.

### Constraint 3: Network Sandbox (Addressing UCA-Type 2 for `google_search` / `request`)
*   **Constraint:** The Agent must be technically incapable of establishing network connections to non-whitelisted domains.
*   **Implementation:** Network interceptor in VACP Gateway verifying all outbound URL requests.

### Constraint 4: Data Provenance & PII (Compliance)
*   **Constraint:** The Agent must only use approved data sources and must not leak PII.
*   **Implementation:** ANS Data Provenance verification and Telemetry processor scrubbing sensitive fields.

### Constraint 5: Zero Standing Privileges (ZSP) (Addressing UCA-Type 2 for `place_order`)
*   **Constraint:** The Agent must hold **zero** standing permissions to execute trades or access secrets.
*   **Implementation:**
    *   **Gateway:** Authenticates request.
    *   **MIM Service:** Impersonates privileged Service Account (JIT).
    *   **Secret Manager:** Releases API key only to the JIT identity for a single transaction.
