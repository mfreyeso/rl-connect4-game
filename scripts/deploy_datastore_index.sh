#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_datastore_index.sh
# Description: Deploys composite indexes from index.yaml to GCP Datastore.
# Usage:
#   ./scripts/deploy_datastore_index.sh [PROJECT_ID] [DATASTORE_DATABASE]
# Examples:
#   ./scripts/deploy_datastore_index.sh my-gcp-project connect4-db
# ==============================================================================

set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || true)}"
DATASTORE_DATABASE="${2:-${DATASTORE_DATABASE:-}}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP Project ID is required."
  echo "Usage: $0 [PROJECT_ID] [DATASTORE_DATABASE]"
  exit 1
fi

if [ ! -f "index.yaml" ]; then
  echo "Error: index.yaml file not found in current directory."
  exit 1
fi

CMD=(gcloud datastore indexes create index.yaml --project="$PROJECT_ID" --quiet)
if [ -n "$DATASTORE_DATABASE" ]; then
  CMD+=(--database="$DATASTORE_DATABASE")
fi

echo "[INFO] Deploying Datastore indexes to Project: $PROJECT_ID | Database: ${DATASTORE_DATABASE:-(default)}"
"${CMD[@]}"
