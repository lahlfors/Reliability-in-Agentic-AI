# Agent System Setup Guide

## Introduction

This guide provides step-by-by-step instructions for setting up and deploying the Financial Advisor agent with the **Verifiable Agentic Control Plane (VACP)**.

The Financial Advisor is a multi-agent system designed to assist with financial analysis. The VACP is an ISO 42001-compliant governance layer that ensures the agent's actions are safe, auditable, and aligned with organizational policy.

## Prerequisites

Before you begin, ensure you have the following software installed:

- **Python 3.11+**
- **Poetry**: For dependency management.
- **Google Cloud CLI**: For deploying the agent to Vertex AI.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/lahlfors/Reliability-in-Agentic-AI
   cd adk-samples/python/agents/financial_advisor
   ```
2. **Install dependencies**:
   This project uses Poetry to manage dependencies. Run the following command from the `financial-advisor` directory to install them:
   ```bash
   cd financial-advisor
   poetry install --with dev,deployment
   ```

## Configuration

1. **Set up Google Cloud credentials**:
   You can set the following environment variables in your shell or in a `.env` file:
   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=true
   export GOOGLE_CLOUD_PROJECT=<your-project-id>
   export GOOGLE_CLOUD_LOCATION=<your-project-location>
   ```
2. **Authenticate with gcloud**:
   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
   ```

## Running the System

To run the complete system (Financial Advisor and VACP), use the `deploy_all.py` script from the root of the repository:
```bash
PYTHONPATH=. poetry -C financial-advisor run python3 deploy_all.py
```
This script will start the Financial Advisor web application with the VACP sidecar enabled.

## Running Tests

To verify that everything is set up correctly, you can run the test suites.

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
