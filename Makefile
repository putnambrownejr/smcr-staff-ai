.PHONY: install run test lint typecheck check init-db

install:
	python -m pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

init-db:
	python -m app.db.init_db

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy app tests

check: lint typecheck test
