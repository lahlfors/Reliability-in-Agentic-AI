# **ADK Financial Advisor Agent: A Case Study in AI Systems Safety Engineering**

## **Introduction: A Praxis-Oriented Approach to AI Safety**

This repository contains the source code for the Financial Advisor Agent, a sample project built using Google's **Agent Development Kit (ADK)**. Its primary purpose extends beyond a simple demonstration of agentic capabilities; it serves as a live testbed for **"The Google AI Systems Safety Engineer: A Praxis-Oriented Professional Development Framework."**

The core philosophy of this program is "praxis"—learning through applied mastery. This codebase is a **baseline system** designed to be systematically analyzed, hardened, and transformed into a verifiably safe agent. The goal is to engineer a defensible, auditable safety case against the novel risks introduced by autonomous AI.

**Disclaimer:** This project is intended for educational and research purposes in the field of AI systems safety. It is not intended for use in a production environment or for providing actual financial advice.

## **New Features: STPA Safety & Observability**

This version of the agent has been refactored to implement a robust safety architecture based on **Systems-Theoretic Process Analysis (STPA)** and **ISO/IEC 42001:2023** standards.

### **1. STPA-Driven Guardrails (Actuators)**
Following a formal hazard analysis (see `STPA_ANALYSIS.md`), we have implemented "Reference Monitor" actuators that enforce hard safety constraints independent of the AI's probabilistic decision-making:

*   **Financial Circuit Breaker:** An immutable control that prevents the agent from executing trades that would exceed a 2% daily drawdown limit.
*   **Resource Limiter:** A mechanism to detect and block "Instrumental Convergence" risks, such as infinite execution loops or excessive resource consumption.
*   **Network Sandbox:** A strict Actuator that enforces domain whitelisting, preventing the agent from establishing unauthorized network connections (Data Exfiltration protection).

### **2. OpenTelemetry Observability**
The system is instrumented with **OpenTelemetry (OTel)** to provide deep visibility into the agent's "Cognitive Loop."
*   **Tracing:** Every agent thought, plan, and tool execution is traced.
*   **PII Redaction:** A custom processor automatically sanitizes sensitive data (PII) from traces before export, ensuring compliance.
*   **Guardrail Events:** Safety violations are tagged with specific attributes (`guardrail.violation=true`) for immediate alerting.

## **Getting Started**

For detailed setup instructions, please refer to [SETUP.md](./SETUP.md).

### **Prerequisites**
*   Python 3.11+
*   Poetry (for dependency management)
*   Google Cloud Project (with Vertex AI enabled)

### **1. Installation**
Clone the repository and install dependencies using Poetry from the `financial-advisor` directory:

```bash
git clone https://github.com/lahlfors/Reliability-in-Agentic-AI
cd Reliability-in-Agentic-AI

# Install dependencies including the new telemetry packages
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

## **Training the Safety Policy**

The **Metacognitive Control Subsystem (MCS)** uses a **Reinforcement Learning (RL)** policy to arbitrate decisions (Execute, Veto, Revise). You must train this policy before running the system.

Run the training script from the **root directory**:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 metacognitive_control_subsystem/train.py
```

**How it works:**
1.  **Environment:** A custom `CMDP_Environment` simulates high-risk scenarios.
2.  **Algorithm:** Uses Proximal Policy Optimization (PPO) with a **Lagrangian Constraint** mechanism.
3.  **Outcome:** The model learns to maximize reward (task completion) while keeping the "Cost" (safety violations) below a strict threshold. The trained model is saved as `metacognitive_control_subsystem/ppo_mcs_policy.zip`.

## **Deployment**

To launch the full system, use the `deploy_all.py` script. This starts both the **MCS Safety API** (Port 8000) and the **Financial Advisor Web UI** (Port 8001) concurrently.

Run from the **root directory**:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 deploy_all.py
```

Access the agent at: `http://localhost:8001`

## **Verifying Safety Controls**

We have provided a verification script to demonstrate the guardrails in action. This script attempts to force the agent to perform unsafe actions (e.g., placing a large order, running an infinite loop, accessing a malware site).

Run the verification script from the **root directory**:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 verify_safety.py
```

**Expected Output:**
You should see `GUARDRAIL VIOLATION` logs and confirmation that all unsafe attempts were `BLOCKED`.

## **The Safety Engineering Lifecycle**

Working with this agent involves a cumulative, multi-stage process that mirrors a rigorous safety engineering lifecycle:

1.  **System Modeling:** Defining the control structure and hazards (`STPA_ANALYSIS.md`).
2.  **Operational Safety:** Implementing independent Actuators (`actuators.py`) and Observability (`telemetry.py`).
3.  **Formal Methods:** Training a constrained policy using CMDPs (`train.py`).
4.  **Verification:** Validating the controls via Red Teaming (`verify_safety.py`).

## **License**

This project is licensed under the Apache 2.0 License. See the LICENSE file for more details.
