#!/usr/bin/env python3
"""
FinGuard Governance Deployment Pipeline
=======================================
This script acts as the "Compliance Gate" for deploying the FinGuard agent.
It enforces:
1. Automated Testing (Pre-Flight Checks)
2. Policy Existence Verification
3. Zero Standing Privileges (Identity Provisioning)
4. Immutable Artifact Build (Containerization)
5. Cloud Run Deployment

Usage:
    python3 finguard/deploy/deploy_all.py --project <PROJECT_ID> [--region <REGION>]
"""

import argparse
import subprocess
import sys
import os
import shutil

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

def run_cmd(cmd, cwd=None, check=True):
    log(f"Running: {' '.join(cmd)}", YELLOW)
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if check and result.returncode != 0:
        log(f"Command failed: {' '.join(cmd)}", RED)
        sys.exit(result.returncode)
    return result

def check_preflight():
    log("\n=== [1/5] Pre-Flight Checks (Compliance Gate) ===", GREEN)

    # 1. Verify Policy Exists
    policy_path = "finguard/policies/trade.rego"
    if not os.path.exists(policy_path):
        log(f"CRITICAL: Governance Policy not found at {policy_path}", RED)
        sys.exit(1)
    log(f"✓ Policy found: {policy_path}")

    # 2. Run Integration Tests (Verification Suite)
    log("Running Integration Tests (finguard/main.py)...")
    # We use PYTHONPATH=. to ensure finguard package is resolved
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    # We assume 'poetry' is available or we use the current venv python
    # Ideally we use the python that invoked this script
    python_exe = sys.executable

    # Check dependencies (simplified)
    # In a real pipeline, we'd ensure environment is set up.
    # Here we just try to run it.
    try:
        # We run the script. It exits with 0 on success.
        subprocess.run(
            [python_exe, "finguard/main.py"],
            env=env,
            check=True
        )
        log("✓ Integration Tests Passed")
    except subprocess.CalledProcessError:
        log("CRITICAL: Integration Tests Failed. Aborting Deployment.", RED)
        sys.exit(1)

def provision_identity(project_id):
    log("\n=== [3/5] Identity Provisioning (ZSP Architecture) ===", GREEN)

    executor_sa = f"finguard-executor-sa@{project_id}.iam.gserviceaccount.com"
    viewer_sa = f"finguard-readonly-sa@{project_id}.iam.gserviceaccount.com"

    # Helper to check if SA exists
    def sa_exists(email):
        res = subprocess.run(
            ["gcloud", "iam", "service-accounts", "describe", email, "--project", project_id],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return res.returncode == 0

    # 1. Create Executor Identity
    if not sa_exists(executor_sa):
        log(f"Creating Executor SA: {executor_sa}")
        run_cmd([
            "gcloud", "iam", "service-accounts", "create", "finguard-executor-sa",
            "--display-name", "FinGuard Executor (ZSP)",
            "--project", project_id
        ])
    else:
        log(f"Executor SA exists: {executor_sa}")

    # 2. Grant Brokerage Permission (Simulated via AI Platform User or similar)
    # In reality, this SA would be the ONLY one allowed to hit the Brokerage API.
    # We grant it aiplatform.user to invoke models.
    log("Granting roles/aiplatform.user to Executor...")
    run_cmd([
        "gcloud", "projects", "add-iam-policy-binding", project_id,
        f"--member=serviceAccount:{executor_sa}",
        "--role=roles/aiplatform.user"
    ])

    # 3. Create ReadOnly Identity
    if not sa_exists(viewer_sa):
        log(f"Creating Viewer SA: {viewer_sa}")
        run_cmd([
            "gcloud", "iam", "service-accounts", "create", "finguard-readonly-sa",
            "--display-name", "FinGuard ReadOnly",
            "--project", project_id
        ])

    log("Granting roles/logging.logWriter to Viewer...")
    run_cmd([
        "gcloud", "projects", "add-iam-policy-binding", project_id,
        f"--member=serviceAccount:{viewer_sa}",
        "--role=roles/logging.logWriter"
    ])

def build_container(project_id, region):
    log("\n=== [2/5] Build & Push (Artifact Registry) ===", GREEN)

    image_name = f"{region}-docker.pkg.dev/{project_id}/finguard/agent:latest"
    # Note: We assume a repo named 'finguard' exists in Artifact Registry.
    # Creating it if missing:
    run_cmd([
        "gcloud", "artifacts", "repositories", "create", "finguard",
        "--repository-format=docker", "--location", region, "--project", project_id
    ], check=False) # Ignore if exists

    log(f"Building Container: {image_name}")
    # Build from Root context
    run_cmd([
        "docker", "build",
        "-f", "finguard/deploy/Dockerfile",
        "-t", image_name,
        "."
    ])

    log("Pushing to Registry...")
    run_cmd(["docker", "push", image_name])
    return image_name

def deploy_cloud_run(project_id, region, image_name):
    log("\n=== [5/5] Deploy to Cloud Run ===", GREEN)

    service_name = "finguard-agent"
    executor_sa = f"finguard-executor-sa@{project_id}.iam.gserviceaccount.com"

    log(f"Deploying {service_name} with Identity: {executor_sa}")

    # Deploy command
    run_cmd([
        "gcloud", "run", "deploy", service_name,
        "--image", image_name,
        "--region", region,
        "--project", project_id,
        "--service-account", executor_sa,
        "--set-env-vars", f"GOOGLE_CLOUD_PROJECT={project_id},OPA_ENABLED=true",
        "--no-allow-unauthenticated" # Governance: No public access
    ])

    log(f"✓ Deployment Complete: {service_name}", GREEN)

def main():
    parser = argparse.ArgumentParser(description="FinGuard Deployment Pipeline")
    parser.add_argument("--project", required=True, help="Google Cloud Project ID")
    parser.add_argument("--region", default="us-central1", help="GCP Region")
    parser.add_argument("--skip-identity", action="store_true", help="Skip IAM provisioning (for updates)")
    parser.add_argument("--dry-run", action="store_true", help="Don't execute gcloud/docker commands")

    args = parser.parse_args()

    # Robustly determine repo root and switch to it
    script_path = os.path.abspath(__file__) # /app/finguard/deploy/deploy_all.py
    deploy_dir = os.path.dirname(script_path) # /app/finguard/deploy
    finguard_dir = os.path.dirname(deploy_dir) # /app/finguard
    repo_root = os.path.dirname(finguard_dir) # /app

    if os.getcwd() != repo_root:
        log(f"Changing CWD to Repo Root: {repo_root}", YELLOW)
        os.chdir(repo_root)

    # Make sure we are in repo root
    if not os.path.exists("finguard/deploy/deploy_all.py"):
        log("Error: Could not verify repository root structure.", RED)
        sys.exit(1)

    # 1. Pre-Flight (Compliance Check)
    check_preflight()

    if args.dry_run:
        log("Dry Run: Skipping Build/Identity/Deploy steps.", YELLOW)
        return

    # 2. Build
    image_name = build_container(args.project, args.region)

    # 3. Identity
    if not args.skip_identity:
        provision_identity(args.project)

    # 4. Deploy
    deploy_cloud_run(args.project, args.region, image_name)

if __name__ == "__main__":
    main()
