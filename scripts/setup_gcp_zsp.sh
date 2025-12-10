#!/bin/bash
# Copyright 2025 Google LLC
# Setup script for Zero Standing Privileges (ZSP) on Google Cloud
# Usage: ./setup_gcp_zsp.sh <PROJECT_ID> <REGION>

set -e

PROJECT_ID=$1
REGION=$2

if [ -z "$PROJECT_ID" ] || [ -z "$REGION" ]; then
    echo "Usage: $0 <PROJECT_ID> <REGION>"
    exit 1
fi

echo "--- Configuring ZSP Infrastructure for Project: $PROJECT_ID ---"

# Configuration
GATEWAY_SA_NAME="vacp-gateway-sa"
TRADER_SA_NAME="vacp-trader-sa"
SECRET_ID="TRADING_API_KEY"
TRADER_SA_EMAIL="$TRADER_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
GATEWAY_SA_EMAIL="$GATEWAY_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# 1. Enable Required APIs
echo "Enable IAM Credentials and Secret Manager APIs..."
gcloud services enable iamcredentials.googleapis.com secretmanager.googleapis.com --project "$PROJECT_ID"

# 2. Create Service Accounts
echo "Creating Low-Privilege Gateway Service Account..."
if ! gcloud iam service-accounts describe "$GATEWAY_SA_EMAIL" --project "$PROJECT_ID" > /dev/null 2>&1; then
    gcloud iam service-accounts create "$GATEWAY_SA_NAME" \
        --display-name="VACP Gateway (Low Privilege)" \
        --project "$PROJECT_ID"
fi

echo "Creating High-Privilege Trader Service Account..."
if ! gcloud iam service-accounts describe "$TRADER_SA_EMAIL" --project "$PROJECT_ID" > /dev/null 2>&1; then
    gcloud iam service-accounts create "$TRADER_SA_NAME" \
        --display-name="VACP Trader (Privileged)" \
        --project "$PROJECT_ID"
fi

# 3. Create Secret
echo "Creating Trading Secret..."
if ! gcloud secrets describe "$SECRET_ID" --project "$PROJECT_ID" > /dev/null 2>&1; then
    echo -n "super-secret-trading-key-12345" | gcloud secrets create "$SECRET_ID" \
        --data-file=- \
        --replication-policy="automatic" \
        --project "$PROJECT_ID"
else
    echo "Secret $SECRET_ID already exists."
fi

# 4. IAM Bindings: MIM Architecture
echo "Granting 'Secret Accessor' to Trader SA..."
gcloud secrets add-iam-policy-binding "$SECRET_ID" \
    --member="serviceAccount:$TRADER_SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --project "$PROJECT_ID" > /dev/null

echo "Granting 'Service Account Token Creator' to Gateway SA on Trader SA..."
# This allows the Gateway SA to impersonate the Trader SA
gcloud iam service-accounts add-iam-policy-binding "$TRADER_SA_EMAIL" \
    --member="serviceAccount:$GATEWAY_SA_EMAIL" \
    --role="roles/iam.serviceAccountTokenCreator" \
    --project "$PROJECT_ID" > /dev/null

# 5. Output for Deployment
echo "--- Configuration Complete ---"
echo "Deployment Environment Variables:"
echo "GCP_PROJECT_ID=$PROJECT_ID"
echo "VACP_PRIVILEGED_SA=$TRADER_SA_EMAIL"
echo "VACP_TRADING_SECRET_ID=$SECRET_ID"
echo "CLOUD_RUN_SA=$GATEWAY_SA_EMAIL"
echo "------------------------------"
