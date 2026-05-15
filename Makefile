.PHONY: install run test lint typecheck check init-db docker-up docker-down docker-logs docker-build

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

docker-build:
	docker compose build

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f api
