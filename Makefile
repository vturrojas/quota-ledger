.DEFAULT_GOAL := help

# Load environment variables from .env if present
-include .env
export

.PHONY: help venv install fmt lint test run up down dbshell

help:
	@echo "Targets:"
	@echo "  make venv      - create .venv"
	@echo "  make install   - install deps (editable + dev)"
	@echo "  make fmt       - auto-format (ruff)"
	@echo "  make lint      - lint + formatting check"
	@echo "  make test      - run tests"
	@echo "  make up        - start postgres (docker compose)"
	@echo "  make down      - stop postgres (docker compose)"
	@echo "  make dbshell   - open psql in the db container"
	@echo "  make run       - run API (uvicorn)"

venv:
	python3 -m venv .venv

install:
	. .venv/bin/activate && pip install -U pip && pip install -e ".[dev]"

fmt:
	. .venv/bin/activate && ruff format . && ruff check . --fix

lint:
	. .venv/bin/activate && ruff check . && ruff format --check .

test:
	. .venv/bin/activate && pytest

run:
	. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port $${PORT:-8000}

up:
	docker compose up -d

down:
	docker compose down

dbshell:
	docker exec -it quota-ledger-db-1 psql -U app -d app
