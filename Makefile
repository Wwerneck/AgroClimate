.PHONY: setup up down test lint format pipeline clean

setup:
	python -m venv .venv
	.venv\Scripts\pip install -r requirements.txt

up:
	docker compose up -d

down:
	docker compose down

test:
	pytest

lint:
	ruff check .

format:
	black src tests dags dashboard

pipeline:
	python -m src.pipeline

clean:
	powershell -NoProfile -Command "Remove-Item -Recurse -Force data/bronze,data/silver,data/gold,data/quarantine,data/metadata -ErrorAction SilentlyContinue"

