.PHONY: venv install dev lint test run

venv:
	python3 -m venv .venv

install:
	. .venv/bin/activate && pip install -U pip && pip install -e .[dev]

lint:
	. .venv/bin/activate && ruff check . && ruff format --check .

test:
	. .venv/bin/activate && pytest

run:
	. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port $${PORT:-8000}
