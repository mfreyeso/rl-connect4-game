#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_cloud_run.sh
# Description: Automated deployment of Connect 4 Web App to GCP Cloud Run
#              connecting to Render PostgreSQL database.
# Usage:
#   ./scripts/deploy_cloud_run.sh [PROJECT_ID] [REGION] [DATABASE_URL]
# Example:
#   ./scripts/deploy_cloud_run.sh my-gcp-project us-central1 "postgresql://user:pass@host/db"
# ==============================================================================

set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || true)}"
REGION="${2:-us-central1}"
DATABASE_URL="${3:-${DATABASE_URL:-}}"
SERVICE_NAME="connect4-game"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP Project ID is required."
  echo "Usage: $0 <PROJECT_ID> [REGION] [DATABASE_URL]"
  exit 1
fi

if [ -z "$DATABASE_URL" ]; then
  echo "Error: Render DATABASE_URL is required."
  echo "Usage: $0 <PROJECT_ID> <REGION> <DATABASE_URL>"
  echo "Or set DATABASE_URL environment variable."
  exit 1
fi

echo "[INFO] Deploying Connect 4 to GCP Cloud Run service: $SERVICE_NAME"
echo "[INFO] Target Project: $PROJECT_ID | Region: $REGION"

# 1. Enable Cloud Run, Artifact Registry, and Cloud Build APIs
echo "[STEP 1/3] Enabling GCP Cloud Run, Artifact Registry, and Cloud Build APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project="$PROJECT_ID"

# 2. Ensure default compute service account has storage & build permissions
echo "[STEP 2/3] Configuring IAM permissions for build service account..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.objectViewer" &>/dev/null || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/artifactregistry.writer" &>/dev/null || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/logging.logWriter" &>/dev/null || true

# 3. Build & Deploy to Cloud Run from source
echo "[STEP 3/3] Building and deploying application to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --source=. \
  --allow-unauthenticated \
  --set-env-vars="ENV=production,Q_TABLE_PATH=q_table.pkl,DATABASE_URL=$DATABASE_URL"

echo ""
echo "[SUCCESS] Cloud Run deployment complete."
