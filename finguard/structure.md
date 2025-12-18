# FinGuard Reference Architecture: Structure & Implementation Plan

## 1. Project Overview
**FinGuard** is a high-assurance autonomous agent system designed for financial operations. It enforces a strict **Star Topology** where a central `CoordinatorAgent` (Supervisor) mediates all actions between specialized worker agents. It utilizes **Policy-as-Code (OPA)** and **Semantic Drift Detection** to prevent "Vaporwork" and unauthorized transactions.

**Key Constraints:**
- **Framework:** Google ADK (Agent Development Kit).
- **Topology:** Star (Coordinator + 4 Sub-Agents).
- **Isolation:** Zero Standing Privileges (ZSP) + Semantic Guardrails.
- **Compliance:** Real Rego policies via OPA.

---

## 2. Directory Structure

```text
finguard/
├── README.md                   # Architecture documentation & "Governance Readme"
├── requirements.txt            # google-cloud-aiplatform, opa-python, google-adk, pydantic
├── main.py                     # Entry point (FastAPI or CLI wrapper)
├── config.py                   # Environment variables & Risk Thresholds
├── policies/
│   └── trade_policy.rego       # REAL OPA Policy: Defines allowed assets/risk limits
├── governance/
│   ├── __init__.py
│   ├── policy_engine.py        # Python wrapper for OPA (interacts with .rego)
│   └── semantic_guard.py       # Vertex AI Embedding-based Loop Detector (Vaporwork)
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Abstract Base Class (inherits from ADK ModelClient)
│   ├── coordinator.py          # The Supervisor (The Cortex)
│   ├── compliance.py           # Worker: Checks proposed plans against OPA
│   ├── executor.py             # Worker: The ONLY agent with "Trade" permission
│   ├── quant.py                # Worker: Runs Python analysis (simulated sandbox)
│   └── researcher.py           # Worker: Fetches market data (Search Tool)
└── tools/
    ├── __init__.py
    ├── brokerage_tools.py      # Mock Brokerage API (buy/sell/hold)
    ├── analysis_tools.py       # Python REPL / Analysis functions
    └── search_tools.py         # Tavily/Bing search wrappers
```

## 3. Class Hierarchy & Responsibilities

### 3.1 Governance Layer (`governance/`)

**`class OPAEngine`** (in `policy_engine.py`)
*   **Responsibility:** Loads `trade_policy.rego` and validates JSON payloads.
*   **Methods:**
    *   `validate_trade(action: str, ticker: str, amount: float) -> bool`: Returns True/False based on Rego evaluation.
    *   `get_violation_reason() -> str`: Returns the "deny" message from OPA.

**`class SemanticGuard`** (in `semantic_guard.py`)
*   **Responsibility:** Prevents Semantic Drift (Vaporwork) using Vertex AI Embeddings.
*   **Attributes:**
    *   `history_buffer`: List[Vector] (Last 3 states).
    *   `threshold`: float (e.g., 0.92 cosine similarity).
*   **Methods:**
    *   `check_drift(current_thought: str) -> bool`: Embeds the thought and compares it to history. Returns True if "Stagnation" is detected.

### 3.2 Agent Layer (`agents/`)

**`class FinGuardCoordinator`** (in `coordinator.py`)
*   **Role:** The "Supervisor" / Router.
*   **Inherits:** `adk.Agent`
*   **Tools:** None (It does not act; it delegates).
*   **Logic:**
    1.  Receives User Goal ("Rebalance portfolio").
    2.  **Step 1:** Routes to Researcher for data.
    3.  **Step 2:** Routes data to Quant for analysis.
    4.  **Step 3:** Routes plan to Compliance for OPA check.
    5.  **Step 4:** IF Compliance=Pass, Route to Executor.
*   **Safety:** Implements the `SemanticGuard` check before every routing decision.

**`class ComplianceAgent`** (in `compliance.py`)
*   **Role:** The Internal Auditor.
*   **Tools:** `OPAEngine`.
*   **Prompt:** "You are a risk officer. You do not generate code. You only validate JSON payloads against the OPA policy."

**`class ExecutorAgent`** (in `executor.py`)
*   **Role:** The Arm.
*   **Tools:** `brokerage_tools.execute_order`.
*   **Identity:** This is the only class initialized with the `ZSP_BROKER_SA` service account credentials.

**`class QuantAgent`** (in `quant.py`)
*   **Role:** The Analyst.
*   **Tools:** `analysis_tools.calculate_volatility` (running in constrained scope).
*   **Constraint:** Cannot access the internet or the brokerage API.

---

## 4. Interaction Flow (The "Trace")

**User Input:** "Buy $50k of AAPL."

1.  **Coordinator:**
    *   Checks `SemanticGuard`: "Is this a repetitive loop?" (No).
    *   Routes to `ComplianceAgent`.

2.  **ComplianceAgent:**
    *   Constructs Payload: `{"action": "buy", "ticker": "AAPL", "amount": 50000}`.
    *   Calls `OPAEngine.validate_trade(payload)`.
    *   OPA (Rego): "Deny. Limit is $10k per trade."
    *   Returns: "VIOLATION: Trade exceeds risk limit."

3.  **Coordinator:**
    *   Receives violation.
    *   Routes to User: "I cannot execute this trade. It violates Risk Policy #4 (Max Trade Limit)."
    *   **Halt.** (Does NOT route to Executor).

---

## 5. Implementation Checklist

- [ ] **Setup:** `pip install google-cloud-aiplatform opa-python pydantic`
- [ ] **Policy:** Write `policies/trade.rego` first. This defines the "Ground Truth."
- [ ] **Governance:** Implement `SemanticGuard` using `VertexAIEmbeddings`.
- [ ] **Agents:** Implement the 4 workers using `adk.model.ModelClient`.
- [ ] **Coordinator:** Write the State Machine logic to wire them together.
- [ ] **Traceability:** Ensure every "Handoff" is printed to console with a `[GOVERNANCE]` tag.
