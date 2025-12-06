#!/usr/bin/env python3
"""
Deployment script for the Financial Advisor Agent with VACP Integration.

Usage:
    python3 deploy_all.py run       # Run locally
    python3 deploy_all.py build     # Build Docker image
    python3 deploy_all.py deploy    # Build and Deploy to Cloud Run

Configuration:
    Set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_REGION environment variables
    or pass them as flags (not implemented yet, uses env or gcloud defaults).
"""

import subprocess
import os
import sys
import argparse
import time

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SERVICE_NAME = "financial-advisor-vacp"
DEFAULT_PORT = "8001"

def check_gcloud():
    """Checks if gcloud is installed and available."""
    try:
        subprocess.run(["gcloud", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Error: 'gcloud' CLI not found. Please install Google Cloud SDK.")
        sys.exit(1)

def get_project_id():
    """Gets the Google Cloud Project ID."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        # Try to get from gcloud config
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True, text=True, check=True
            )
            project_id = result.stdout.strip()
        except subprocess.CalledProcessError:
            pass

    if not project_id:
        print("Error: Could not determine Google Cloud Project ID.")
        print("Please set GOOGLE_CLOUD_PROJECT env var or run 'gcloud config set project <PROJECT_ID>'.")
        sys.exit(1)
    return project_id

def get_region():
    """Gets the Google Cloud Region."""
    region = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    return region

def run_local():
    """Runs the agent locally using adk web."""
    print(f"--- Starting VACP-Governed Financial Agent Locally on Port {DEFAULT_PORT} ---")

    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "") + os.pathsep + PROJECT_ROOT
    port = os.environ.get("PORT", DEFAULT_PORT)

    cmd = ["adk", "web", "--host", "0.0.0.0", "--port", port]

    try:
        print(f"🚀 Launching in {os.path.join(PROJECT_ROOT, 'financial-advisor')}...")
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=os.path.join(PROJECT_ROOT, "financial-advisor"),
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        process.wait()
    except KeyboardInterrupt:
        print("\nStopping...")
        process.terminate()

def build_image(project_id):
    """Builds the Docker image using Cloud Build."""
    print(f"--- Building Docker Image for Project {project_id} ---")
    image_tag = f"gcr.io/{project_id}/{SERVICE_NAME}"

    cmd = ["gcloud", "builds", "submit", "--tag", image_tag, PROJECT_ROOT]

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Image built successfully: {image_tag}")
        return image_tag
    except subprocess.CalledProcessError:
        print("❌ Build failed.")
        sys.exit(1)

def deploy_service(project_id, region, image_tag):
    """Deploys the image to Cloud Run."""
    print(f"--- Deploying {SERVICE_NAME} to Cloud Run ({region}) ---")

    cmd = [
        "gcloud", "run", "deploy", SERVICE_NAME,
        "--image", image_tag,
        "--platform", "managed",
        "--region", region,
        "--allow-unauthenticated", # Public for demo; restrict in prod
        "--set-env-vars", f"GOOGLE_CLOUD_PROJECT={project_id},GOOGLE_CLOUD_LOCATION={region}"
        # Add other env vars here (e.g., API keys) if needed
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Service deployed successfully.")
    except subprocess.CalledProcessError:
        print("❌ Deployment failed.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Manage VACP Financial Advisor Deployment")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("run", help="Run locally")
    subparsers.add_parser("build", help="Build Docker image")
    subparsers.add_parser("deploy", help="Build and Deploy to Cloud Run")

    args = parser.parse_args()

    if args.command == "run":
        run_local()
    elif args.command in ["build", "deploy"]:
        check_gcloud()
        project_id = get_project_id()
        region = get_region()

        image_tag = build_image(project_id)

        if args.command == "deploy":
            deploy_service(project_id, region, image_tag)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
