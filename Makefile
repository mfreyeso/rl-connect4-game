.PHONY: setup run train typecheck test web

setup:
	uv venv
	uv sync

run:
	uv run python -m connect4.main

web:
	uv run uvicorn connect4.api:app --reload --port 8000

train:
	uv run python -m connect4.train --episodes $(episodes)

typecheck:
	uv run ty check .

test:
	export PYTHONPATH=$(PWD)
	uv run pytest tests -v
