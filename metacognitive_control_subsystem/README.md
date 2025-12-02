# The MCS Modular Safety Subsystem

This directory contains the source code for the **Metacognitive Control Subsystem (MCS)**, a modular governance layer for autonomous AI agents. The implementation is based on the technical design for a "Reflective" safety system.

## Project Structure

-   `/mcs`: Core source code.
    -   `/api`: FastAPI server and Pydantic schemas.
    -   `/components`: Cognitive modules (Perceiver, Planner, World Model).
    -   `/formal`: Mathematical foundations (CMDP, PID Controller).
    -   `/utils`: Utility functions.
-   `/tests`: Unit and integration tests.
-   `train.py`: Script to train the safety policy.

## Development & Usage

**Prerequisites:** Ensure you have installed dependencies as described in the root [SETUP.md](../SETUP.md).

### 1. Training the Policy
The MCS relies on a Reinforcement Learning policy. You must train this policy before running the system.

From the **repository root**:
```bash
PYTHONPATH=. poetry -C financial-advisor run python3 metacognitive_control_subsystem/train.py
```
This produces `metacognitive_control_subsystem/ppo_mcs_policy.zip`.

### 2. Running Tests
To verify the subsystem's functionality:

From the **repository root**:
```bash
PYTHONPATH=. poetry -C financial-advisor run python3 -m pytest metacognitive_control_subsystem/tests/
```

### 3. Running the API
The MCS API is typically launched as part of the full system via `deploy_all.py`. However, you can run it standalone for debugging:

From the **repository root**:
```bash
PYTHONPATH=. poetry -C financial-advisor run python3 -m uvicorn metacognitive_control_subsystem.mcs.api.server:app --port 8000
```

---

## Technical Design Analysis

### Pros
*   **Principled Safety:** Founded on Constrained Markov Decision Processes (CMDPs).
*   **Proactive Risk Mitigation:** Simulates actions before execution.
*   **Adaptive Alignment:** Includes an Introspective Reflection module.
*   **Robust Control:** Uses a PID controller for stable dual variable updates.

### Cons
*   **Complexity:** High engineering effort.
*   **Overhead:** Latency from simulation and planning.
*   **Dependencies:** Relies on accurate world models and defined constraints.
