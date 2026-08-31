.PHONY: setup run train typecheck test web db-up db-down datastore-up datastore-index deploy-cloudrun

setup:
	uv venv
	uv sync

run:
	DB_BACKEND="postgres" DATABASE_URL="postgresql://connect4_user:connect4_pass@localhost:5432/connect4_db" uv run python -m connect4.main

web:
	docker compose up -d db
	DB_BACKEND="postgres" DATABASE_URL="postgresql://connect4_user:connect4_pass@localhost:5432/connect4_db" uv run uvicorn connect4.api:app --reload --port 8000

web-datastore:
	docker compose up -d datastore-emulator
	DB_BACKEND="datastore" DATASTORE_EMULATOR_HOST="localhost:8081" GCP_PROJECT="connect4-dev" uv run uvicorn connect4.api:app --reload --port 8000

db-up:
	docker compose up -d db

datastore-up:
	docker compose up -d datastore-emulator

datastore-index:
	./scripts/deploy_datastore_index.sh "$(PROJECT_ID)" "$(DATASTORE_DATABASE)"

db-down:
	docker compose down

train:
	uv run python -m connect4.train --episodes $(episodes)

typecheck:
	uv run ty check .

test:
	uv run python -m pytest tests -v

deploy-cloudrun:
	./scripts/deploy_cloud_run.sh "$(PROJECT_ID)" "$(REGION)" "$(DB_BACKEND)" "$(DATABASE_URL)" "$(DATASTORE_DATABASE)"
