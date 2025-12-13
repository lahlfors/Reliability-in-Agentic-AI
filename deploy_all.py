import os
import subprocess
import sys
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_env_var(name, default=None, required=True):
    value = os.getenv(name, default)
    if required and not value:
        logging.error(f"Environment variable '{name}' is missing.")
        sys.exit(1)
    return value

def run_command(command, error_msg="Command failed"):
    """Runs a shell command and streams output."""
    logging.info(f"Running: {' '.join(command)}")
    try:
        process = subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"{error_msg}: {e}")
        sys.exit(1)

def main():
    # 1. Configuration
    PROJECT_ID = get_env_var("GOOGLE_CLOUD_PROJECT") # e.g., 'my-capstone-project'
    REGION = get_env_var("GOOGLE_CLOUD_REGION", "us-central1", required=False)
    SERVICE_NAME = get_env_var("SERVICE_NAME", "financial-advisor-agent", required=False)

    # Image name follows GCR/Artifact Registry convention
    IMAGE_URI = f"gcr.io/{PROJECT_ID}/{SERVICE_NAME}:latest"

    print(f"""
    ========================================
    🚀 VACP AGENT DEPLOYMENT (Cloud Run)
    ========================================
    Project: {PROJECT_ID}
    Region:  {REGION}
    Service: {SERVICE_NAME}
    Target:  {IMAGE_URI}
    ========================================
    """)

    # 2. Build Container
    logging.info("Building container image...")
    run_command(
        ["gcloud", "builds", "submit", "--tag", IMAGE_URI, "."],
        error_msg="Failed to build container"
    )

    # 3. Deploy to Cloud Run
    logging.info("Deploying to Cloud Run...")
    deploy_cmd = [
        "gcloud", "run", "deploy", SERVICE_NAME,
        "--image", IMAGE_URI,
        "--region", REGION,
        "--platform", "managed",
        "--allow-unauthenticated", # Adjust based on security needs
        "--set-env-vars", f"GOOGLE_CLOUD_PROJECT={PROJECT_ID}",
        # Bind the ZSP Service Account if you have the email
        # "--service-account", f"vacp-agent-sa@{PROJECT_ID}.iam.gserviceaccount.com"
    ]

    run_command(deploy_cmd, error_msg="Failed to deploy to Cloud Run")

    logging.info(f"✅ Deployment Complete! Service URL available via 'gcloud run services describe {SERVICE_NAME}'")

if __name__ == "__main__":
    main()
