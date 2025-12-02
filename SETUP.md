# Agent System Setup Guide

## Introduction

This guide provides step-by-by-step instructions for setting up, training, and deploying the agent system, which includes the **Financial Advisor** agent and the **Metacognitive Control Subsystem (MCS)**.

The Financial Advisor is a multi-agent system designed to assist with financial analysis and decision-making. The MCS acts as a modular safety and governance layer, ensuring the agent's actions are aligned with predefined safety constraints using the 'AgentGuard' Runtime Verification framework.

## Prerequisites

Before you begin, ensure you have the following software installed:

- **Python 3.11+**
- **Poetry**: For dependency management. Install instructions: [Poetry Documentation](https://python-poetry.org/docs/).
- **Google Cloud CLI**: For Vertex AI authentication. Install instructions: [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/lahlfors/Reliability-in-Agentic-AI.git
    cd Reliability-in-Agentic-AI
    ```

2.  **Install dependencies**:
    All dependencies for both the Financial Advisor and the MCS are managed in the `financial-advisor` directory.

    ```bash
    cd financial-advisor
    poetry install --with dev,deployment
    ```

    *Note for Linux users*: If you encounter `keyring` errors, run: `poetry config keyring.enabled false`

## Configuration

1.  **Set up Google Cloud credentials**:
    Create a `.env` file in the `financial-advisor` directory or set these in your shell:

    ```bash
    export GOOGLE_GENAI_USE_VERTEXAI=true
    export GOOGLE_CLOUD_PROJECT=<your-project-id>
    export GOOGLE_CLOUD_LOCATION=us-central1
    # export GOOGLE_CLOUD_STORAGE_BUCKET=<your-storage-bucket> # Optional, for remote deployment
    ```

2.  **Authenticate with gcloud**:
    ```bash
    gcloud auth application-default login
    gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
    ```

## Training the Safety Policy (MCS)

The MCS uses a Reinforcement Learning (PPO) policy to arbitrate decisions. You must train this policy before running the system.

From the **repository root**:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 metacognitive_control_subsystem/train.py
```
This will generate `metacognitive_control_subsystem/ppo_mcs_policy.zip`.

## Running the Full System

To launch both the **MCS Safety API** and the **Financial Advisor Web UI** concurrently, use the `deploy_all.py` script.

From the **repository root**:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 deploy_all.py
```

- **MCS API:** `http://localhost:8000`
- **Agent UI:** `http://localhost:8001`

## Running Tests

### 1. Financial Advisor Tests
Run these from the `financial-advisor` directory to verify the agent logic.

```bash
cd financial-advisor
# Run unit tests
python3 -m unittest discover tests/
# OR using pytest
python3 -m pytest tests/
```

### 2. Metacognitive Control Subsystem (MCS) Tests
Run these from the **repository root** to verify the safety subsystem.

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 -m pytest metacognitive_control_subsystem/tests/
```
