# Agent System Setup Guide

## Introduction

This guide provides step-by-by-step instructions for setting up, training, and deploying the agent system, which includes the Financial Advisor agent and the Metacognitive Control Subsystem (MCS).

The Financial Advisor is a multi-agent system designed to assist with financial analysis and decision-making. The MCS acts as a modular safety and governance layer, ensuring the agent's actions are aligned with predefined safety constraints.

## Prerequisites

Before you begin, ensure you have the following software installed:

- **Python 3.11+**
- **Poetry**: For dependency management. You can install it by following the official [Poetry documentation](https://python-poetry.org/docs/).
- **Google Cloud CLI**: For deploying the agent to Vertex AI. Follow the instructions on the [Google Cloud website](https://cloud.google.com/sdk/docs/install) to install it.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/google/adk-samples.git
   cd adk-samples/python/agents/financial_advisor
   ```
2. **Install dependencies**:
   This project uses Poetry to manage dependencies. Run the following command from the `financial-advisor` directory to install them:
   ```bash
   poetry install --with dev,deployment
   ```
   **Note for Linux users**: If you encounter an error related to `keyring` during installation, you can disable it with the following command:
   ```bash
   poetry config keyring.enabled false
   ```

## Configuration

1. **Set up Google Cloud credentials**:
   You can set the following environment variables in your shell or in a `.env` file:
   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=true
   export GOOGLE_CLOUD_PROJECT=<your-project-id>
   export GOOGLE_CLOUD_LOCATION=<your-project-location>
   export GOOGLE_CLOUD_STORAGE_BUCKET=<your-storage-bucket>
   ```
2. **Authenticate with gcloud**:
   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
   ```

## Training the RL Model

The MCS uses a reinforcement learning model to make decisions. To train the model, run the following command from the root of the repository:
```bash
PYTHONPATH=/app poetry -C financial-advisor run python3 metacognitive_control_subsystem/train.py
```
This will create a `ppo_mcs_policy.zip` file in the `metacognitive_control_subsystem` directory.

## Running the System

To run the complete system (Financial Advisor and MCS), use the `deploy_all.py` script from the root of the repository:
```bash
PYTHONPATH=/app poetry -C financial-advisor run python3 deploy_all.py
```
This script will start both the MCS API server and the Financial Advisor web application.

## Running Tests

To verify that everything is set up correctly, you can run the test suites for both components.

1. **Run Financial Advisor tests**:
   From the `financial-advisor` directory:
   ```bash
   python3 -m pytest tests
   python3 -m pytest eval
   ```
2. **Run MCS tests**:
   From the root of the repository:
   ```bash
   PYTHONPATH=/app poetry -C financial-advisor run python3 -m pytest metacognitive_control_subsystem/tests/
   ```
