# **ADK Financial Advisor Agent: A Case Study in AI Systems Safety Engineering**

## **Introduction: A Praxis-Oriented Approach to AI Safety**

This repository contains the source code for the Financial Advisor Agent, a sample project built using Google's **Agent Development Kit (ADK)**. Its primary purpose extends beyond a simple demonstration of agentic capabilities; it serves as a live testbed for **"The Google AI Systems Safety Engineer: A Praxis-Oriented Professional Development Framework."**

**Disclaimer:** This project is intended for educational and research purposes in the field of AI systems safety. It is not intended for use in a production environment or for providing actual financial advice.

---

## **🆕 FinGuard: The Reference Architecture (ISO 42001)**

We have introduced **FinGuard**, a new clean-slate reference architecture located in the `finguard/` directory. FinGuard supersedes the previous `financial-advisor` demo for governance purposes, providing a production-ready blueprint for an **Autonomous Agent System** that complies with **ISO/IEC 42001** and **NIST AI RMF** standards.

**Key Features of FinGuard:**
*   **Star Topology:** A central `CoordinatorAgent` (Supervisor) manages specialized workers (`Researcher`, `Quant`, `Compliance`, `Executor`) to enforce separation of concerns.
*   **Policy-as-Code (OPA):** Real-time transaction gating using **Open Policy Agent (OPA)** and Rego policies (`finguard/policies/trade.rego`), replacing Python-based mocks.
*   **Semantic Guardrails:** A **Semantic Drift Detector** using Vertex AI Embeddings to prevent "Vaporwork" (infinite semantic loops) and enforce progress.
*   **Zero Standing Privileges (ZSP):** Strict identity isolation where only the `Executor` agent possesses the IAM credentials to interact with the Brokerage API.
*   **Sandboxed Execution:** `Quant` analysis runs in a simulated environment (designed for Cloud Run/gVisor) to prevent tool misuse and side-channel attacks.

👉 **[View the FinGuard Architecture & Structure](finguard/structure.md)**

---

## **Legacy Architecture: VACP Integration**

The original `financial-advisor` agent has been refactored to implement a robust safety architecture based on **ISO/IEC 42001:2023** standards and a **Verifiable Agentic Control Plane (VACP)**.

### **1. Zero Standing Privileges (ZSP) Architecture**
We have migrated from static keys to a **GCP-Native Zero Standing Privileges** model.
*   **No Long-Lived Secrets:** The application container has **zero** intrinsic permissions to trade.
*   **Identity Trade (MIM):** The agent must perform an "Identity Trade" via the `MIMService` (Machine Identity Management) to exchange its low-privilege Workload Identity for a short-lived, high-privilege JIT token.

### **2. Verifiable Agentic Control Plane (VACP)**
The VACP replaces the traditional "human-in-the-loop" with a "governance-in-the-loop" architecture, featuring:
*   **AgentGuard:** CMDP-based runtime verification.
*   **Janus Shadow-Monitor:** Continuous internal red-teaming.
*   **System 4 Derivative Estimator:** Predictive risk estimation.

### **3. STPA-Driven Guardrails**
Following a formal hazard analysis (see `STPA_ANALYSIS.md`), the VACP enforces hard safety constraints via **Exponential Control Barrier Functions (ECBF)**.

## **Getting Started**

### **Prerequisites**
*   Python 3.11+
*   Poetry (for dependency management)
*   Google Cloud Project (with Vertex AI enabled)
*   **OPA Binary** (required for FinGuard policy evaluation)

### **1. Installation**
Clone the repository and install dependencies using Poetry:

```bash
git clone https://github.com/lahlfors/Reliability-in-Agentic-AI
cd adk-samples/python/agents/financial_advisor

# Install dependencies (includes FinGuard reqs)
cd financial-advisor
poetry install --with dev,deployment
```

### **2. Running FinGuard (New)**
To run the FinGuard verification suite (Integration Tests):

```bash
PYTHONPATH=$(pwd) poetry -C financial-advisor run python3 finguard/main.py
```

### **3. Running Legacy Financial Advisor**
To run the original agent locally:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 financial-advisor/main.py
```

## **References & Further Reading**

This project's architecture is informed by the following research in AI safety and governance:

1.  **AgentGuard: Runtime Verification of AI Agents**
    *   *Koohestani, R.* (2025). [arXiv:2509.23864](https://arxiv.org/abs/2509.23864)
2.  **The Unified Control Framework: Establishing a Common Foundation for Enterprise AI Governance**
    *   *Eisenberg, I. W., Gamboa, L., & Sherman, E.* (2025). [arXiv:2503.05937](https://arxiv.org/abs/2503.05937)
3.  **Systematic Hazard Analysis for Frontier AI using STPA**
    *   *Mylius, S.* (2025). [arXiv:2506.01782](https://arxiv.org/abs/2506.01782)

## **License**

This project is licensed under the Apache 2.0 License. See the LICENSE file for more details.
