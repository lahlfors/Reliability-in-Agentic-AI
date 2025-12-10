# Copyright 2025 Google LLC
# Machine Identity Management (MIM) Service for Zero Standing Privileges (ZSP)

import logging
from google.auth import default
from google.auth.transport.requests import Request
from google.auth import impersonated_credentials
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

class MIMService:
    """
    Machine Identity Management Service.
    Handles Zero Standing Privilege (ZSP) flows on GCP.

    Implements the "Identity Trade" pattern:
    Workload Identity -> IAM Credentials API -> Short-lived Access Token -> Secret Manager
    """
    def __init__(self, privileged_sa_email: str, project_id: str):
        self.privileged_sa_email = privileged_sa_email
        self.project_id = project_id

        # Get the default credentials (the Low Privilege Cloud Run Identity)
        # In a local env, this might be your user credentials if you ran `gcloud auth application-default login`
        # In Cloud Run, this is the attached Service Account (Gateway SA).
        try:
            self.source_credentials, default_project = default()
            if not self.project_id and default_project:
                self.project_id = default_project
        except Exception as e:
            logger.warning(f"Failed to obtain default credentials: {e}. MIM Service may not function correctly.")
            self.source_credentials = None

    def get_jit_session(self):
        """
        Just-In-Time Access:
        Impersonates the Privileged Service Account to get a short-lived session.
        """
        if not self.source_credentials:
            raise RuntimeError("MIM Service: No source credentials available for impersonation.")

        logger.info(f"🔒 MIM: Requesting JIT access for {self.privileged_sa_email}...")

        # Create an impersonated credential.
        # This calls the IAM Credentials API.
        # We enforce a short lifetime (e.g., 5-15 minutes).
        # The snippet suggested 300s (5m).
        jit_creds = impersonated_credentials.Credentials(
            source_credentials=self.source_credentials,
            target_principal=self.privileged_sa_email,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            lifetime=300
        )

        # Refresh to generate the actual token immediately
        # This performs the API call to IAM Credentials
        try:
            jit_creds.refresh(Request())
            logger.info("✅ MIM: JIT Token acquired. Identity elevated.")
            return jit_creds
        except Exception as e:
            logger.error(f"❌ MIM: Failed to acquire JIT token: {e}")
            raise PermissionError(f"MIM Elevation Failed: {e}")

    def fetch_secret_with_jit(self, secret_id: str, jit_creds) -> str:
        """
        Uses the JIT credentials to access Secret Manager.
        The Low Privilege identity CANNOT do this directly.
        """
        try:
            client = secretmanager.SecretManagerServiceClient(credentials=jit_creds)
            # Build the resource name of the secret version.
            # We default to 'latest'.
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"

            logger.info(f"🔑 MIM: Accessing secret '{secret_id}' via JIT identity...")
            response = client.access_secret_version(request={"name": name})

            payload = response.payload.data.decode("UTF-8")
            return payload
        except Exception as e:
            logger.error(f"❌ MIM: Failed to fetch secret '{secret_id}': {e}")
            raise PermissionError(f"Secret Access Failed: {e}")
