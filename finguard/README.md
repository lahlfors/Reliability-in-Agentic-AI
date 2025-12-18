# FinGuard: Reference Architecture for ISO 42001 Compliance

**FinGuard** is a high-assurance autonomous agent system designed to execute personal finance tasks (portfolio rebalancing, tax-loss harvesting) while adhering to strict governance controls. It serves as the reference implementation for the **Verifiable Agentic Control Plane (VACP)** concepts.

## 🏗️ Architecture: The Star Topology

FinGuard rejects the "Monolithic LLM" pattern in favor of a specialized **Star Topology**:

*   **Coordinator (Supervisor):** The central hub. It plans tasks and routes them to workers. It performs **Semantic Drift Checks** on every turn.
*   **Compliance Officer:** The **Internal Auditor**. It validates every proposed trade against immutable **OPA Policies (Rego)**.
*   **Executor:** The **Arm**. It is the ONLY agent with the Identity (Service Account) to execute trades.
*   **Quant Analyst:** The **Brain**. It runs Python code in a **Sandbox** to calculate risk metrics.
*   **Researcher:** The **Eyes**. It fetches market data.

## 🛡️ Governance Features

### 1. Policy-as-Code (OPA)
We use **Open Policy Agent (OPA)** to enforce business logic. The policy is defined in `policies/trade.rego`.
*   **Rule:** Trades > $50,000 are BLOCKED.
*   **Rule:** Restricted assets (ESG < 50) are BLOCKED.

### 2. Semantic Guard (Vaporwork Detection)
We use **Vertex AI Embeddings** to detect "Vaporwork" (infinite loops where the agent rephrases intent without progress).
*   **Mechanism:** Cosine Similarity of thought vectors.
*   **Threshold:** > 0.9 similarity triggers a HALT.

### 3. Zero Standing Privileges (ZSP)
Isolation is enforced at the identity level. The `Quant` agent cannot trade because it lacks the IAM role. The `Coordinator` cannot trade because it lacks the tool definition.

## 🚀 How to Run

### Prerequisites
1.  **OPA Binary:** Ensure `opa` is installed or the `OPAEngine` wrapper can find it.
2.  **Google Cloud:** Authenticated session for Vertex AI (Embeddings).

### Run Integration Tests (Verification Suite)
This runs the full end-to-end scenarios (Happy Path, Policy Block, Vaporwork, Isolation).

```bash
# From the financial-advisor/ directory
PYTHONPATH=$(pwd) poetry -C financial-advisor run python3 finguard/main.py
```

### Directory Structure

```text
finguard/
├── agents/             # The Supervisor and Workers
├── governance/         # OPA Engine & Semantic Guard
├── policies/           # Rego Files
├── tools/              # Specialized Tools (Brokerage, Sandbox)
└── main.py             # Integration Tests
```
