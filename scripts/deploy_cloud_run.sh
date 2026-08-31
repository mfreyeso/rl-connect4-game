#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_cloud_run.sh
# Description: Automated deployment of Connect 4 Web App to GCP Cloud Run
#              configured with GCP Datastore (or PostgreSQL) backend.
# Usage:
#   ./scripts/deploy_cloud_run.sh [PROJECT_ID] [REGION] [DB_BACKEND] [DATABASE_URL] [DATASTORE_DATABASE]
# Examples:
#   ./scripts/deploy_cloud_run.sh my-gcp-project us-central1 datastore "" my-datastore-db
#   ./scripts/deploy_cloud_run.sh my-gcp-project us-central1 postgres "postgresql://user:pass@host/db"
# ==============================================================================

set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || true)}"
REGION="${2:-us-central1}"
DB_BACKEND="${3:-datastore}"
DATABASE_URL="${4:-${DATABASE_URL:-}}"
DATASTORE_DATABASE="${5:-${DATASTORE_DATABASE:-}}"
SERVICE_NAME="connect4-game"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP Project ID is required."
  echo "Usage: $0 <PROJECT_ID> [REGION] [DB_BACKEND] [DATABASE_URL] [DATASTORE_DATABASE]"
  exit 1
fi

echo "[INFO] Deploying Connect 4 to GCP Cloud Run service: $SERVICE_NAME"
echo "[INFO] Target Project: $PROJECT_ID | Region: $REGION | Backend: $DB_BACKEND"
if [ -n "$DATASTORE_DATABASE" ]; then
  echo "[INFO] Target Datastore Database: $DATASTORE_DATABASE"
fi

# 1. Enable Cloud Run, Artifact Registry, Cloud Build, and Datastore APIs
echo "[STEP 1/3] Enabling required GCP APIs (Cloud Run, Artifact Registry, Cloud Build, Datastore)..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  datastore.googleapis.com \
  --project="$PROJECT_ID"

# 2. Ensure default compute service account has Cloud Datastore & build permissions
echo "[STEP 2/3] Configuring IAM permissions for service account..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/datastore.user" &>/dev/null || true

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

if [ "$DB_BACKEND" = "postgres" ]; then
  if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL is required when DB_BACKEND is postgres."
    exit 1
  fi
  ENV_VARS="ENV=production,Q_TABLE_PATH=q_table.pkl,DB_BACKEND=postgres,DATABASE_URL=$DATABASE_URL"
else
  ENV_VARS="ENV=production,Q_TABLE_PATH=q_table.pkl,DB_BACKEND=datastore,GCP_PROJECT=$PROJECT_ID"
  if [ -n "$DATASTORE_DATABASE" ]; then
    ENV_VARS="$ENV_VARS,DATASTORE_DATABASE=$DATASTORE_DATABASE"
  fi
fi

gcloud run deploy "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --source=. \
  --allow-unauthenticated \
  --set-env-vars="$ENV_VARS"

echo ""
echo "[SUCCESS] Cloud Run deployment complete with $DB_BACKEND backend."
