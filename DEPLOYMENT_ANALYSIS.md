# Deployment Analysis: Financial Advisor Agent (VACP)

This document provides an analysis of deployment options for the Financial Advisor Agent, specifically focusing on the requirements of the **Verifiable Agentic Control Plane (VACP)** and **ISO 42001 compliance**.

## 1. Vertex AI Agent Engine (Reasoning Engine)

Vertex AI Agent Engine is a fully managed service for deploying and reasoning with LangChain and other agent frameworks.

### **Pros**
*   **Managed Infrastructure:** No need to manage servers, containers, or scaling.
*   **Integrated Evaluation:** Native integration with Vertex AI Evaluation services.
*   **Ease of Use:** Simple Python SDK (`reasoning_engines.create`) to deploy directly from code.
*   **Traceability:** Built-in integration with Cloud Logging and Trace for basic agent interactions.

### **Cons**
*   **Serialization Limits:** The Reasoning Engine pickles the agent object. Complex custom runtime logic like the VACP sidecar (which relies on local state, in-memory registries, and `async` event loops) may face pickling or runtime execution issues in the managed environment.
*   **Dependency Constraints:** Including the local `vacp` package requires packaging it as a tarball or private PyPI package, adding build complexity.
*   **Lack of Network Control:** You cannot easily inject an **Istio Sidecar** or enforce strict network policies (Allow-listing) at the container level, which is a core requirement of the VACP (Constraint 3).
*   **"Black Box" Runtime:** Harder to implement the "Millisecond Kill-Switch" (Constraint 4) if you don't control the ingress/egress layer directly.

### **Suitability for VACP:** **LOW**
While excellent for standard agents, the "black box" nature of the managed runtime makes it difficult to enforce the *strict, verifiable engineering controls* (Network Sandbox, Independent Watchdogs) required by the ISO 42001 VACP architecture.

---

## 2. Google Cloud Run

Cloud Run is a serverless container platform that abstracts away infrastructure while providing full container control.

### **Pros**
*   **Container Control:** You build the Dockerfile. This allows full customization of the runtime environment (Python version, system libraries).
*   **Sidecar Support:** Cloud Run now natively supports [sidecar containers](https://cloud.google.com/run/docs/deploying-sidecars). This allows you to run the **VACP** as a true network proxy or separate process alongside the agent in the same instance.
*   **Scaling:** Scales to zero automatically.
*   **VPC Connectivity:** Can connect to VPCs to access private resources or restrict egress traffic (partially satisfying the Network Sandbox).

### **Cons**
*   **Ephemeral Filesystem:** In-memory registries (like the current ANS implementation) are lost on scale-down. (Though VACP should use Redis/SQL in prod).
*   **No "Mesh" features:** While it supports sidecars, it lacks the full traffic management features of a Service Mesh (Istio) for complex traffic shaping or mutual TLS (mTLS) between micro-agents.

### **Suitability for VACP:** **MEDIUM-HIGH**
Cloud Run is the "Sweet Spot" for this stage of development. It offers enough control to implement the VACP logic and network restrictions without the massive operational overhead of Kubernetes.

---

## 3. Google Kubernetes Engine (GKE)

GKE is Google's managed Kubernetes service, offering the highest level of control and orchestration.

### **Pros**
*   **Perfect Architectural Fit:** The TDD explicitly references **Istio**, **Sidecars**, and **Kubernetes**. GKE is the native home for this architecture.
*   **Istio Service Mesh:** Allows for:
    *   **Zero-Trust Security (mTLS)** between the Agent and the VACP.
    *   **Egress Gateways:** Strict allow-listing of external URLs (Google Search, APIs) at the network packet level (Constraint 3).
    *   **Fault Injection:** Perfect for "Red Teaming" and testing the robustness of the VACP.
*   **Persistence:** easy integration with StatefulSets or PersistentVolumes for the Ledger/Audit logs.
*   **Isolation:** Namespace-level isolation for different Risk Tiers (Low/Med/High).

### **Cons**
*   **Complexity:** Requires managing clusters, nodes, YAML manifests, and Helm charts. Significantly higher learning curve and maintenance burden.
*   **Cost:** "Always-on" control plane and node pools (unless using GKE Autopilot, which is still more expensive than Cloud Run for low traffic).

### **Suitability for VACP:** **HIGH (Gold Standard)**
For a "Verifiable, ISO-Compliant" system, GKE + Istio is the industry standard pattern. It allows the **Policy Enforcement Point (PEP)** to be decoupled from the application logic entirely.

---

## Final Recommendation

### **Scenario A: Proof of Concept / MVP (Current Stage)**
**Recommendation: Google Cloud Run**
*   **Why:** It allows you to package the `vacp` library and the agent into a single container image (or main + sidecar) easily. It respects the standard HTTP/Web interface of `adk web`. It provides sufficient observability and security controls (VPC, IAM) without the overhead of managing a cluster.
*   **Action:** Create a `Dockerfile` that installs `poetry`, copies the `vacp` and `financial-advisor` directories, and runs `deploy_all.py` (or just `adk web`).

### **Scenario B: Production / ISO Certification (Target State)**
**Recommendation: Google Kubernetes Engine (GKE) with Istio**
*   **Why:** To truly satisfy the "Verifiability" and "Independent Layer" requirements of ISO 42001, you need the network-level guarantees that only a Service Mesh can provide.
    *   The **Tool Gateway** becomes an **Istio AuthorizationPolicy**.
    *   The **Kill Switch** becomes a network rule change, not just a Python variable.
*   **Action:** Transition the `ToolGateway` logic from Python code into **Rego policies (OPA)** or **Istio Configs** running on GKE.

---

### **Immediate Next Steps (for this repo)**
1.  Stick with the **Cloud Run** model for the immediate deployment script.
2.  Update `deploy_all.py` to be "Container-Ready" (ensure it listens on `0.0.0.0` and accepts `$PORT` env var).
