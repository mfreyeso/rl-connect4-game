.PHONY: setup run train typecheck

setup:
	uv venv
	uv sync

run:
	uv run python -m connect4.main

train:
	uv run python -m connect4.train

typecheck:
	uv run ty check .
