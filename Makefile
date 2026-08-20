.PHONY: setup up down test lint format pipeline load-warehouse status clean

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

load-warehouse:
	python -c "from src.config.settings import get_settings; from src.warehouse.load_postgres import load_gold_to_postgres; s=get_settings(); print(load_gold_to_postgres(s.gold_dir, s))"

status:
	python scripts/show_status.py

clean:
	powershell -NoProfile -Command "Remove-Item -Recurse -Force data/bronze,data/silver,data/gold,data/quarantine,data/metadata -ErrorAction SilentlyContinue"
