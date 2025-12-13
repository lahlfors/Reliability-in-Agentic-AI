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
*   **Constraint:** The Agent must be technically incapable of exceeding a daily drawdown limit of 2% of the portfolio value.
*   **Implementation:** VACP Tool Gateway "Reference Monitor" checking `place_order` parameters against current portfolio state.

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

### Constraint 6: Uncontrolled Tool Use (Addressing UCA-Type 2 for all tools)
*   **Constraint:** The Agent must be technically incapable of calling tools that are not explicitly authorized in its Identity Card (agent.json).
*   **Implementation:**
    *   **Mitigated by vacp.governor enforcing constraints defined in agent.json (System 5 Policy).**
    *   **Agent Card:** Cryptographically verified JSON artifact defining the `tools_allowed` and `tools_denied` lists.
    *   **Tool Gateway:** Enforces the Allow/Deny lists at the point of tool invocation.

## 4. Implementation Verification (VACP)

The hazards identified in the STPA analysis above have been mitigated through the implementation of the Verifiable Agentic Control Plane (VACP).

### Mitigation Mapping

| Hazard ID | Hazard Description | Mitigation Implementation (Component) |
| :--- | :--- | :--- |
| **H-1** | **Uncontrolled Tool Use**<br>(Agent executes dangerous shell commands or financial transfers without authorization) | **Policy Governor (System 3)**<br>Implemented in `vacp.governor.Governor`. The `agent.json` artifact defines a strict `tools_denied` list (e.g., `shell_execute`). The `ToolGateway` enforces this policy at runtime, blocking any tool call not explicitly allowed or explicitly denied. |
| **H-2** | **Unauthorized Policy Modification**<br>(Attacker alters the `agent.json` to allow dangerous tools) | **Identity & Verification (System 5)**<br>Implemented in `vacp.c2pa.C2PASigner` and `vacp.card_loader`. The system requires a cryptographic signature (`agent.json.sig`) to match the configuration file. The `CardLoader` prevents the agent from starting if the signature verification fails. |
| **H-3** | **Unobserved Failure**<br>(Governance violations occur silently) | **Observability Monitor (System 4)**<br>Implemented in `vacp.processor.VACPSpanProcessor`. All governance checks emit OpenTelemetry spans. Policy violations (e.g., blocked tool calls) are tagged with `vacp.policy_violation` attributes, ensuring they are visible in the audit trail. |

### Verification Evidence
* **Unit Tests:** `financial-advisor/tests/test_agents.py` verifies that the `VACPGovernedAgent` correctly emits telemetry spans.
* **Integration Tests:** `verify_agent_card.py` confirms that the loader rejects unsigned cards and the Governor blocks tools listed in the denial list.
