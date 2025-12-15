# Technical Architecture: Cybernetic Governance for Agentic AI

## 1. Executive Summary

This document describes the technical architecture of the "Cybernetic Governance" system implemented for the `financial-advisor` agent. The system shifts from "Governance by Policy" to "Governance by Engineering," embedding probabilistic agents within a deterministic control plane. It utilizes a Hierarchical Deterministic Markov Decision Process (MDP) approach to constrain agent behavior, ensuring safety and ISO 42001 compliance.

The core innovation is the **Dynamic Risk-Adaptive Stack**, which decouples risk logic from agent code and applies defense-in-depth strategies ranging from syntax validation to multi-model consensus.

## 2. System Context

The system consists of the following high-level entities:
*   **Host Agent (`VACPGovernedAgent`):** An LLM-based agent (Google ADK) responsible for financial coordination.
*   **Verifiable Agentic Control Plane (VACP):** A centralized governance framework that enforces policies.
*   **Cybernetic Stack (Internal):** A set of internal guards (`PolicyEngine`, `Verifier`, `ConsensusStrategy`) integrated directly into the agent's execution loop.
*   **External Dependencies (Mocked):** Open Policy Agent (OPA), Safety LLMs (ShieldGemma), and Frontier Models (GPT-4/Claude) for consensus.

## 3. The Cybernetic Stack (Defense-in-Depth)

The governance architecture is layered to balance latency and safety:

### Layer 1: Syntax Trapdoor (Pydantic)
*   **Mechanism:** Strict type validation using Pydantic schemas defined in `vacp/schemas.py`.
*   **Function:** Ensures tool parameters match expected types before execution.
*   **Latency:** Negligible (~0ms).

### Layer 2: Policy-as-Code (OPA Pattern)
*   **Component:** `vacp.policy.MockOPAPolicyEngine` (Mocking OPA sidecar).
*   **Interface:** `PolicyEngine.evaluate(context) -> PolicyResult`.
*   **Logic:**
    *   Evaluates actions against defined rules (e.g., "High Value Trades > $50k require Consensus").
    *   Returns `PolicyResult` containing `allowed` status, `risk_level` (LOW, HIGH, CRITICAL), and `requirements`.
*   **Latency:** Low (~5-10ms).

### Layer 3: Semantic Verification (Adversarial Verifier)
*   **Component:** `vacp.guards.ShieldGemmaMock`.
*   **Interface:** `Verifier.verify(content, context) -> bool`.
*   **Logic:**
    *   Simulates a fine-tuned safety model (ShieldGemma 8B) scanning for semantic hazards.
    *   Checks for adversarial patterns (e.g., "ignore previous instructions", "drop table").
*   **Latency:** Low/Medium (~100ms).

### Layer 4: Consensus Engine (Adaptive Compute)
*   **Component:** `vacp.guards.EnsembleConsensus`.
*   **Interface:** `ConsensusStrategy.vote(proposal, context) -> bool`.
*   **Logic:**
    *   Triggered dynamically by Layer 2 policies (e.g., for Critical risks).
    *   Simulates a vote among multiple frontier models (GPT-4, Claude 3.5, Gemini 1.5).
    *   Action is blocked if a majority vote against it.
*   **Latency:** High ($$$).

### Layer 5: Assisted Human-in-the-Loop (HITL)
*   **Component:** `vacp.reviewer.ReviewerAgent`.
*   **Logic:**
    *   Triggered when `PolicyResult` demands `human_approval`.
    *   Pre-computes context (`ReviewPacket`) summarizing the risk and recommendation to minimize human latency.
    *   Simulates a "One-Click" decision interface.

## 4. Component Interactions & Control Flow

The `VACPGovernedAgent` serves as the integration point. The control flow is enforced within the `_run_async_impl` method:

1.  **Event Interception:** The agent intercepts every `Event` yielded by the LLM.
2.  **Tool Use Detection:** If the event indicates `tool_use`, the `execute_governance_check(task_payload)` method is invoked.
3.  **Sequential Governance Check:**
    *   **Step 1:** `PolicyEngine` evaluates the action payload. If denied, **BLOCK**.
    *   **Step 2:** If `Consensus` is required, `ConsensusStrategy` votes. If failed, **BLOCK**.
    *   **Step 3:** `Verifier` scans parameters for semantic threats. If detected, **BLOCK**.
    *   **Step 4:** If `Human Approval` is required, `ReviewerAgent` prepares a packet. (Simulated auto-approval/rejection).
4.  **Enforcement (The Wall):**
    *   If any check fails, the method returns a `block_reason`.
    *   The agent **neutralizes** the event: `event.tool_use = None`.
    *   A refusal message is injected into `event.content.text` (e.g., "[SYSTEM: ACTION BLOCKED] Reason: ...").
    *   The modified event is yielded. The ADK runtime sees a text response instead of a tool call, preventing execution.

## 5. Data Flow

```
[LLM] -> (Generates Event with ToolUse)
   |
   v
[VACPGovernedAgent] -> (Intercepts Event)
   |
   +--> [PolicyEngine] -> (Evaluate Payload) -> [PolicyResult]
   |
   +--> (If High Risk) -> [ConsensusStrategy] -> (Vote) -> [Bool]
   |
   +--> [Verifier] -> (Scan Content) -> [Bool]
   |
   v
(Decision: ALLOW or BLOCK)
   |
   +-- If BLOCK:
   |      Modify Event: ToolUse = None
   |      Inject Text: "Action Blocked: Reason..."
   |
   v
[ADK Runtime]
   |
   +-- If Text: Display to User / Add to History
   +-- If ToolUse: Execute Tool (Real World Effect)
```

## 6. Key Mechanisms

*   **Verification Asymmetry:** The system does not attempt to control the *generation* of the plan (NP-Hard), but strictly verifies the *proposed action* (P-Time) against deterministic constraints.
*   **Zero Standing Privileges (ZSP):** (Implemented in `ToolGateway`) Access to sensitive tools requires JIT credential injection, coupled with the Policy checks.
*   **Governance by Engineering:** The agent cannot bypass the checks because they are hard-coded into the execution loop (`_run_async_impl`), distinct from the prompt/context.

## 7. Interfaces

Defined in `vacp/interfaces.py`, enforcing strict contracts for all governance components:
*   `PolicyEngine`: Decouples rule logic from agent logic.
*   `Verifier`: Abstract semantic checking.
*   `ConsensusStrategy`: Pluggable voting mechanisms.
