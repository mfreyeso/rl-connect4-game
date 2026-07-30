#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_vm_all_in_one.sh
# Description: Automated provisioning and deployment of Connect 4 Web App & Postgres
#              on a single GCP Compute Engine e2-micro VM in us-central1.
# Usage:
#   ./scripts/deploy_vm_all_in_one.sh [PROJECT_ID] [ZONE]
# Example:
#   ./scripts/deploy_vm_all_in_one.sh my-gcp-project-123 us-central1-a
# ==============================================================================

set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || true)}"
ZONE="${2:-us-central1-a}"
INSTANCE_NAME="connect4-vm"
MACHINE_TYPE="e2-micro"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP Project ID is required."
  echo "Usage: $0 <PROJECT_ID> [ZONE]"
  exit 1
fi

echo "[INFO] Deploying Connect 4 to GCP Compute Engine instance: $INSTANCE_NAME"
echo "[INFO] Target Project: $PROJECT_ID | Zone: $ZONE | Machine Type: $MACHINE_TYPE"

# 1. Enable Compute Engine API
echo "[STEP 1/3] Enabling Compute Engine API..."
gcloud services enable compute.googleapis.com --project="$PROJECT_ID"

# 2. Create Firewall Rules (Port 80, 443, 8000)
echo "[STEP 2/3] Configuring firewall rules..."
if ! gcloud compute firewall-rules describe allow-connect4-web --project="$PROJECT_ID" &>/dev/null; then
  gcloud compute firewall-rules create allow-connect4-web \
    --project="$PROJECT_ID" \
    --allow=tcp:80,tcp:443,tcp:8000 \
    --target-tags=connect4-server \
    --description="Allow web traffic to Connect 4 application"
fi

# 3. Create Compute Engine Instance (Always Free Tier)
echo "[STEP 3/3] Creating Compute Engine Instance ($INSTANCE_NAME)..."
EXISTING_ZONE=""
for check_z in "$ZONE" us-central1-a us-central1-b us-central1-c us-central1-f us-east1-b us-east1-c us-east1-d us-west1-a us-west1-b us-west1-c; do
  if gcloud compute instances describe "$INSTANCE_NAME" --zone="$check_z" --project="$PROJECT_ID" &>/dev/null; then
    EXISTING_ZONE="$check_z"
    break
  fi
done

if [ -n "$EXISTING_ZONE" ]; then
  ZONE="$EXISTING_ZONE"
  echo "[INFO] Instance '$INSTANCE_NAME' already exists in zone '$ZONE'."
else
  CREATED=false
  CANDIDATE_ZONES=("$ZONE" us-central1-a us-central1-b us-central1-c us-central1-f us-east1-b us-east1-c us-east1-d us-west1-a us-west1-b us-west1-c)
  
  # Deduplicate candidate zones while preserving preferred zone first
  UNIQUE_ZONES=()
  for z in "${CANDIDATE_ZONES[@]}"; do
    if [[ ! " ${UNIQUE_ZONES[*]-} " =~ " ${z} " ]]; then
      UNIQUE_ZONES+=("$z")
    fi
  done

  for try_zone in "${UNIQUE_ZONES[@]}"; do
    echo "[INFO] Attempting VM creation in zone: $try_zone..."
    if gcloud compute instances create "$INSTANCE_NAME" \
      --project="$PROJECT_ID" \
      --zone="$try_zone" \
      --machine-type="$MACHINE_TYPE" \
      --tags=connect4-server,http-server,https-server \
      --image-family=ubuntu-2404-lts-amd64 \
      --image-project=ubuntu-os-cloud \
      --boot-disk-size=30GB \
      --boot-disk-type=pd-standard \
      --metadata=startup-script='#!/bin/bash
        apt-get update
        apt-get install -y ca-certificates curl gnupg git
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        systemctl enable docker
        systemctl start docker
      ' 2>/tmp/gcloud_create.log; then
        ZONE="$try_zone"
        CREATED=true
        echo "[INFO] VM created successfully in zone '$ZONE'."
        break
    else
      if grep -q "ZONE_RESOURCE_POOL_EXHAUSTED" /tmp/gcloud_create.log; then
        echo "[WARN] Zone '$try_zone' resource pool exhausted for e2-micro. Trying next zone..."
      else
        cat /tmp/gcloud_create.log
        echo "[ERROR] VM creation failed in zone '$try_zone'."
      fi
    fi
  done

  if [ "$CREATED" = false ]; then
    echo "[ERROR] Could not create e2-micro instance in any GCP Free Tier zone due to resource pool exhaustion."
    echo "[TIP] You can try machine-type 'e2-small' (minimal cost ~$12/mo) or try again later."
    exit 1
  fi

  echo "[INFO] Waiting 30 seconds for VM startup and Docker initialization..."
  sleep 30
fi

# Get Instance External IP
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "[SUCCESS] VM Provisioning complete."
echo "[INFO] Public URL: http://$EXTERNAL_IP:8000"
echo ""
echo "Deployment Instructions:"
echo "1. Connect via SSH:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
echo ""
echo "2. Clone repository and start containers:"
echo "   git clone <REPOSITORY_URL> connect4-game"
echo "   cd connect4-game"
echo "   sudo docker compose up -d --build"
echo ""
echo "3. Run database migration (if applicable):"
echo "   ./scripts/migrate_render_to_gcp.sh '<RENDER_DB_URL>' 'postgresql://connect4_user:connect4_pass@127.0.0.1:5432/connect4_db'"
