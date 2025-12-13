# **ADK Financial Advisor Agent: A Case Study in AI Systems Safety Engineering**

## **Introduction: A Praxis-Oriented Approach to AI Safety**

This repository contains the source code for the Financial Advisor Agent, a sample project built using Google's **Agent Development Kit (ADK)**. Its primary purpose extends beyond a simple demonstration of agentic capabilities; it serves as a live testbed for **"The Google AI Systems Safety Engineer: A Praxis-Oriented Professional Development Framework."**

The core philosophy of this program is "praxis"—learning through applied mastery. This codebase is a **baseline system** designed to be systematically analyzed, hardened, and transformed into a verifiably safe agent. The goal is to engineering a defensible, auditable safety case against the novel risks introduced by autonomous AI.

**Disclaimer:** This project is intended for educational and research purposes in the field of AI systems safety. It is not intended for use in a production environment or for providing actual financial advice.

## **New Features: ISO 42001 & Verifiable Agentic Control Plane (VACP)**

This version of the agent has been refactored to implement a robust safety architecture based on **ISO/IEC 42001:2023** standards and a **Verifiable Agentic Control Plane (VACP)**.

### **1. Zero Standing Privileges (ZSP) Architecture**
We have migrated from static keys to a **GCP-Native Zero Standing Privileges** model.
*   **No Long-Lived Secrets:** The application container has **zero** intrinsic permissions to trade.
*   **Identity Trade (MIM):** The agent must perform an "Identity Trade" via the `MIMService` (Machine Identity Management) to exchange its low-privilege Workload Identity for a short-lived, high-privilege JIT token.
*   **Secret Manager Injection:** API keys are retrieved from Google Secret Manager only at the exact moment of use and injected directly into the tool execution memory space.

### **2. Verifiable Agentic Control Plane (VACP)**
The VACP replaces the traditional "human-in-the-loop" with a "governance-in-the-loop" architecture. It consists of:
*   **Agent Name Service (ANS):** The "Source of Truth" that maintains a registry of authorized agents and their risk tiers.
*   **Tool Gateway:** An operational chokepoint that intercepts all side-effects (API calls), enforces access control, and handles JIT credential injection.
*   **AgentGuard:** A dynamic probabilistic assurance module that learns an MDP (Markov Decision Process) of the agent's behavior in real-time to calculate failure probabilities ($P_{max}(Failure)$).
*   **Janus Shadow-Monitor:** A continuous internal "Red Team" that evaluates proposed actions for vulnerabilities and policy compliance (ISO 42001 Clause 9.2).
*   **Governing-Orchestrator Agent (GOA):** The decision-making kernel that uses **SSVC (Stakeholder-Specific Vulnerability Categorization)** to decide whether to TRACK, MONITOR, or QUARANTINE an agent.

### **3. STPA-Driven Guardrails**
Following a formal hazard analysis (see `STPA_ANALYSIS.md`), the VACP enforces hard safety constraints:
*   **Financial Circuit Breaker:** Prevents trades exceeding daily drawdown limits.
*   **Resource Limiter:** Blocks infinite loops or excessive resource consumption.
*   **Network Sandbox:** Enforces strict domain allow-listing to prevent data exfiltration.

### **4. Auditability & Observability**
*   **Unified Control Framework (UCF):** Maps ISO 42001 clauses to technical controls in the code.
*   **Agent Card (EU AI Act):** A machine-readable `agent.json` artifact that acts as the "Passport" for the agent, defining strictly allowed/denied tools and risk boundaries.
*   **ZK-Prover (Mock):** Generates Zero-Knowledge proofs of compliance for a simulated public ledger (ETHOS), satisfying ISO audit requirements.
*   **OpenTelemetry:** Provides deep visibility into the agent's "Cognitive Loop" with PII redaction.

## **Getting Started**

### **Prerequisites**
*   Python 3.11+
*   Poetry (for dependency management)
*   Google Cloud Project (with Vertex AI enabled)

### **1. Installation**
Clone the repository and install dependencies using Poetry:

```bash
git clone https://github.com/lahlfors/Reliability-in-Agentic-AI
cd adk-samples/python/agents/financial_advisor

# Install dependencies
cd financial-advisor
poetry install --with dev,deployment
```

### **2. Configuration**
Create a `.env` file in `financial-advisor/` with your Google Cloud details:

```bash
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"
GOOGLE_GENAI_USE_VERTEXAI="True"
```

## **Running the System**

### **Cloud Deployment**
To deploy the full system (Agent + VACP) to Google Cloud Run:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
python3 deploy_all.py
```

### **Local Testing**
To run the agent locally for development:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 financial-advisor/main.py
```

Access the agent at: `http://localhost:8001`

**How it works:**
The agent runs as a "VACPGovernedAgent". Before executing any high-risk tool (like `place_order`), it pauses and consults the VACP Sidecar (GOA). The GOA runs risk assessments (AgentGuard, Janus) and returns a decision. If approved, the **Tool Gateway** performs a JIT Identity Trade to acquire the necessary permissions to execute the trade.

## **Verifying Safety Controls**

We have provided a verification script to demonstrate the guardrails in action. This script attempts to force the agent to perform unsafe actions (e.g., placing a large order, running an infinite loop).

Run the verification script:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 verify_safety.py
```

**Expected Output:**
You should see `GUARDRAIL VIOLATION` logs or VACP blocking decisions (QUARANTINE) confirming that unsafe attempts were prevented.

## **License**

This project is licensed under the Apache 2.0 License. See the LICENSE file for more details.
