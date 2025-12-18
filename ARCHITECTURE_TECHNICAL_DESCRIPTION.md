# Architecture Technical Description

## The Verifiable Agentic Control Plane (VACP) & FinGuard

The VACP is a safety engineering framework designed to transform probabilistic GenAI agents into deterministic, auditable systems suitable for high-stakes domains like finance.

---

## 🏗️ FinGuard Architecture (New Reference Implementation)

**FinGuard** represents the evolution of the VACP concepts into a production-hardened reference architecture compliant with ISO 42001.

### 1. Topology: The Star Pattern
Unlike the legacy hierarchical model, FinGuard uses a strict **Star Topology**.
*   **Hub:** The `FinGuardCoordinator` (Supervisor) is the only entity that routes requests.
*   **Spokes:** Specialized Workers (`Researcher`, `Quant`, `Compliance`, `Executor`) never communicate directly. All data flows through the Supervisor for inspection.
*   **Benefit:** Eliminates "Hidden Communication Channels" and ensures the Supervisor can perform a "Vaporwork Check" at every turn.

### 2. The "Brain": Governance Logic
*   **Policy-as-Code (OPA):** We have moved from Python-based mocks to **Open Policy Agent (OPA)**.
    *   **Mechanism:** Before any trade, the `ComplianceAgent` serializes the proposal to JSON and validates it against `finguard/policies/trade.rego` using a local OPA binary or sidecar.
    *   **Immutability:** Policies are defined in Rego, ensuring the LLM cannot overwrite or hallucinate exceptions.
*   **Semantic Drift Guard (The "Vaporwork" Check):**
    *   **Problem:** Agents can enter semantic loops where they rephrase the same intent ("I will analyze", "Analyzing now") without progress. Simple string matching fails here.
    *   **Solution:** We use **Vertex AI Embeddings** to calculate the cosine similarity of the agent's thought trace. If $Similarity(t, t-1..3) > Threshold$, the system triggers a **Safety Halt**.

### 3. The "Trapdoor": Isolation & Physics
*   **Quant Sandbox:** Code execution is isolated. The `QuantAgent` runs Python code in a restricted environment (simulating Cloud Run/gVisor isolation) to prevent file system access or unauthorized network calls.
*   **Zero Standing Privileges (ZSP):**
    *   The `ExecutorAgent` is the **only** identity with the `roles/brokerage.trader` IAM permission (simulated via strict tool gating).
    *   Even if the Coordinator is jailbroken, it physically lacks the credentials to execute a trade directly.

---

## Legacy Architecture Details (VACP 1.0)

### Core Architecture: HD-MDP
The legacy system implements a **Hierarchical Deterministic Markov Decision Process (HD-MDP)**.
1.  **Level 1 (Coordinator)**: Semantic router classifying intent.
2.  **The Bridge (Router Tool)**: Deterministic transition using `route_request`.
3.  **Level 0 (Workers)**: Atomic task execution.

### Cybernetic Upgrade: ECBF & System 4
*   **System 4 (Derivative Estimator):** Uses a `WorldModel` to estimate risk velocity ($\dot{h}$) and acceleration ($\ddot{h}$).
*   **ECBF Governor:** Enforces $h(x) + K_1 \dot{h}(x) + K_2 \ddot{h}(x) \geq 0$ to prevent "Semantic Inertia" (momentum towards violation).
