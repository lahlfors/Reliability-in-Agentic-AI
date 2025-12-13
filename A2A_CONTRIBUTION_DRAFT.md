# Analysis of A2A Discussion #741: "Agent Registry - Proposal"

## Context
The discussion revolves around defining a standard for an "Agent Registry" to enable discovery, management, and entitlement of AI agents.
*   **Key Tension:** Centralized Catalog (xRegistry) vs. Decentralized Federation (SecureAgentTools).
*   **Missing Piece:** While there is significant discussion on *discovery protocols* (API endpoints, mTLS, namespaces) and *technical metadata* (inputs/outputs, skills), there is very little focus on **Regulatory Compliance** and **Safety Governance**.

## The Gap: Governance & Compliance
Current proposals focus on:
*   **Identity:** `did:web`, `spiffe`
*   **Capabilities:** Skills, tools, endpoints
*   **Auth:** OAuth2, mTLS

However, for Enterprise adoption (especially in EU/regulated sectors), an Agent Registry must also convey:
*   **Risk Profile:** Is this a High-Risk AI system under the EU AI Act?
*   **Operational Constraints:** What are the hard limits (e.g., max drawdown, disallowed tools)?
*   **Data Governance:** Where was the model trained? Is it copyright compliant?

## Proposed Contribution
We can contribute the **Compliance-Ready Agent Card Schema** developed in the VACP project. This bridges the gap between the technical discovery layer and the legal/safety layer.

---

## Draft GitHub Comment

**Title:** Proposal: Adding a "Governance & Compliance" Facet to the Agent Card Standard

**Body:**

Hi @kthota-g, @ognis1205, and @SecureAgentTools,

This is a fascinating discussion. The debate between Centralized vs. Federated discovery is critical, but I'd like to highlight a third dimension that is essential for enterprise adoption: **Regulatory Governance**.

As organizations move to deploy agents in production, especially in regulated industries (Finance, Healthcare), the "Agent Card" needs to act not just as a technical interface description (like WSDL/OpenAPI) but also as a **Compliance Passport** (like an SBOM for AI).

We have been working on an implementation aligned with **ISO 42001** and the **EU AI Act (Annex IV)**. We found that the Agent Card must explicitly declare its safety boundaries so that the Registry (or a Governor sidecar) can enforce them.

I propose extending the Agent Card schema to include a top-level `governance` or `compliance` object.

**Example Schema Extension:**

```json
{
  "$schema": "https://standards.a2a.org/agent-card/v1.0",
  "identity": {
    "provider": "Acme Corp",
    "lei_code": "5493006MIPVJEZ2P6F12",
    "did": "did:web:acme.com:agent-01"
  },
  "capabilities": {
    "intended_purpose": "Automated Financial Trading",
    "high_risk_category": "Annex III (5)(b) - Credit scoring / Financial Services",
    "tools_allowed": ["get_stock_price", "place_order"],
    "tools_denied": ["email_user", "transfer_funds"]
  },
  "operational_constraints": {
    "human_oversight_mode": "HUMAN_IN_THE_LOOP",
    "intervention_trigger": "Confidence < 0.85",
    "kill_switch": "https://api.acme.com/agent/kill"
  }
}
```

**Why this matters:**
1.  **Automated Policy Enforcement:** A registry or gateway can automatically block an agent if it requests a tool listed in `tools_denied`.
2.  **Liability & Trust:** The `lei_code` (Legal Entity Identifier) provides legally binding identity resolution, which is crucial for high-trust federation.
3.  **EU AI Act Readiness:** Fields like `intended_purpose` and `high_risk_category` map directly to regulatory reporting requirements.

Would there be interest in merging these "Safety & Compliance" fields into the v1.0 Agent Card specification? I am happy to share the full Pydantic models we are using.
