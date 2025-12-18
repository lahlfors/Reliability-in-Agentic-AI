# Agent System Setup Guide

## Introduction

This guide provides step-by-by-step instructions for setting up and deploying the Financial Advisor agent with the **Verifiable Agentic Control Plane (VACP)** and the new **FinGuard Reference Architecture**.

## Prerequisites

Before you begin, ensure you have the following software installed:

- **Python 3.11+**
- **Poetry**: For dependency management.
- **Google Cloud CLI**: For deploying the agent to Vertex AI and managing IAM.
- **OPA (Open Policy Agent)**: The binary `opa` must be installed or available in PATH to run FinGuard policies. [Download OPA](https://www.openpolicyagent.org/docs/latest/#running-opa)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/lahlfors/Reliability-in-Agentic-AI
   cd adk-samples/python/agents/financial_advisor
   ```
2. **Install dependencies**:
   This project uses Poetry to manage dependencies. Run the following command from the `financial-advisor` directory to install them (this includes dependencies for both legacy and FinGuard):
   ```bash
   cd financial-advisor
   poetry install --with dev,deployment
   ```

## Infrastructure Setup (Zero Standing Privileges)

We utilize a **Zero Standing Privileges (ZSP)** architecture on Google Cloud. This requires specific Service Accounts and IAM bindings.

1. **Authenticate with gcloud**:
   ```bash
   gcloud auth login
   gcloud config set project <your-project-id>
   ```

2. **Run the Setup Script**:
   We provide a script to automatically provision the necessary infrastructure (Service Accounts, Secrets, and IAM roles).

   From the root of the repository:
   ```bash
   chmod +x scripts/setup_gcp_zsp.sh
   ./scripts/setup_gcp_zsp.sh <your-project-id> <region>
   ```
   *Example:* `./scripts/setup_gcp_zsp.sh my-gcp-project us-central1`

   **Note the output!** The script will print environment variables you need for the next step.

## Configuration

1. **Set Environment Variables**:
   Create a `.env` file in `financial-advisor/` or export these variables in your shell. Use the values output by the setup script:

   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=true
   export GOOGLE_CLOUD_PROJECT=<your-project-id>
   export GOOGLE_CLOUD_LOCATION=<your-project-location>

   # ZSP Configuration
   export GCP_PROJECT_ID=<your-project-id>
   export VACP_PRIVILEGED_SA=vacp-trader-sa@<your-project-id>.iam.gserviceaccount.com
   export VACP_TRADING_SECRET_ID=TRADING_API_KEY
   export CLOUD_RUN_SA=vacp-gateway-sa@<your-project-id>.iam.gserviceaccount.com
   ```

2. **Application Default Credentials (ADC)**:
   If running locally, you need to authenticate your user to allow the code to act as the "Source Credential" for the initial impersonation.

   ```bash
   gcloud auth application-default login
   ```

## Running the System

### Option A: Run FinGuard (New Reference Architecture)
To run the full FinGuard integration test suite (Star Topology + OPA + Semantic Guard):

```bash
PYTHONPATH=$(pwd) poetry -C financial-advisor run python3 finguard/main.py
```

### Option B: Run Legacy Financial Advisor
To run the original web-based agent:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 deploy_all.py
```

## Running Tests

1. **Run VACP (Control Plane) tests**:
   From the root of the repository:
   ```bash
   PYTHONPATH=. poetry -C financial-advisor run python3 -m unittest vacp/tests/test_vacp.py
   ```

2. **Run Financial Advisor tests**:
   From the root of the repository:
   ```bash
   PYTHONPATH=. poetry -C financial-advisor run python3 -m unittest discover financial-advisor/tests/
   ```

## Agent Card Configuration (ISO 42001)

The legacy system is governed by an **Agent Card** (`agent.json`). This file defines the agent's identity, regulatory compliance, and permitted capabilities.

### 1. File Location
The agent card is located at `financial-advisor/agent.json`.

### 2. Signing the Card
Before the system can run securely, the Agent Card must be cryptographically signed. We provide a utility script to mock this C2PA signing process:

```bash
PYTHONPATH=. poetry -C financial-advisor run python3 verify_safety.py
```
