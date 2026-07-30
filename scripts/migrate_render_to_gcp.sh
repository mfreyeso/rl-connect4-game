#!/usr/bin/env bash
# ==============================================================================
# Script: migrate_render_to_gcp.sh
# Description: Streams PostgreSQL database from Render to GCP.
# Usage:
#   ./scripts/migrate_render_to_gcp.sh <RENDER_DATABASE_URL> <GCP_DATABASE_URL>
# Or via environment variables:
#   RENDER_DATABASE_URL="..." GCP_DATABASE_URL="..." ./scripts/migrate_render_to_gcp.sh
# ==============================================================================

set -euo pipefail

RENDER_DB_URL="${1:-${RENDER_DATABASE_URL:-}}"
GCP_DB_URL="${2:-${GCP_DATABASE_URL:-}}"

if [ -z "$RENDER_DB_URL" ] || [ -z "$GCP_DB_URL" ]; then
  echo "Error: Missing database connection URLs."
  echo ""
  echo "Usage:"
  echo "  $0 <RENDER_DATABASE_URL> <GCP_DATABASE_URL>"
  echo ""
  echo "Or using environment variables:"
  echo "  export RENDER_DATABASE_URL='postgresql://user:pass@render-host/dbname'"
  echo "  export GCP_DATABASE_URL='postgresql://user:pass@gcp-vm-ip/dbname'"
  echo "  $0"
  exit 1
fi

# Standardize legacy postgres:// to postgresql://
RENDER_DB_URL="${RENDER_DB_URL/postgres:\/\//postgresql:\/\/}"
GCP_DB_URL="${GCP_DB_URL/postgres:\/\//postgresql:\/\/}"

echo "[INFO] Starting database migration from Render to GCP PostgreSQL..."

if ! command -v pg_dump &> /dev/null || ! command -v pg_restore &> /dev/null; then
  echo "[INFO] pg_dump or pg_restore not found locally. Running via postgres:16-alpine container..."

  docker run --rm \
    -e RENDER_URL="$RENDER_DB_URL" \
    -e GCP_URL="$GCP_DB_URL" \
    postgres:16-alpine \
    sh -c 'pg_dump -d "$RENDER_URL" -F c -b | pg_restore -d "$GCP_URL" --clean --if-exists --no-owner --no-acl'
else
  pg_dump -d "$RENDER_DB_URL" -F c -b | pg_restore -d "$GCP_DB_URL" --clean --if-exists --no-owner --no-acl
fi

echo "[INFO] Database migration completed successfully."
