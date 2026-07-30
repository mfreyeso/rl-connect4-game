.PHONY: setup run train typecheck test web db-up db-down deploy-cloudrun

setup:
	uv venv
	uv sync

run:
	uv run python -m connect4.main

web:
	docker compose up -d db
	DATABASE_URL="postgresql://connect4_user:connect4_pass@localhost:5433/connect4_db" uv run uvicorn connect4.api:app --reload --port 8000

db-up:
	docker compose up -d db

db-down:
	docker compose down

train:
	uv run python -m connect4.train --episodes $(episodes)

typecheck:
	uv run ty check .

test:
	uv run python -m pytest tests -v

deploy-cloudrun:
	./scripts/deploy_cloud_run.sh "$(PROJECT_ID)" "$(REGION)" "$(DATABASE_URL)"

