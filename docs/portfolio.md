# AgroClimate Portfolio Demo

AgroClimate is a data engineering project for Brazilian agribusiness analytics. It ingests weather data, structures a
Bronze/Silver/Gold lake, validates quality gates, loads a PostgreSQL star schema and serves a Streamlit dashboard.

## Highlights

- Incremental Open-Meteo ingestion for monitored agricultural cities.
- Bronze, Silver and Gold Parquet layers with Spark processing and Pandas local fallback.
- PostgreSQL dimensional model with idempotent upserts and schema migrations.
- Airflow DAG with real quality gates for Bronze, Silver and Gold datasets.
- Streamlit dashboard with filters, climate risk summaries, map, charts and CSV export.
- CI with lint, format check and automated tests.
- IBGE PAM ingestion with Silver/Gold agriculture summaries and dashboard analytics.
- Agroclimatic score by state combining production exposure, current climate risk events and temperature.
- Domain-oriented processing modules for weather and agriculture.

## Demo Flow

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_local.ps1 -SkipDocker
streamlit run dashboard/app.py
```

With Docker available:

```powershell
docker compose up -d
python -m src.pipeline
make load-warehouse
streamlit run dashboard/app.py
```

## Data Sources

- Open-Meteo API for weather observations.
- IBGE SIDRA/PAM table 1612 for temporary crop production indicators.
- CONAB crop monitoring and harvest reports are documented as a planned source for the next integration layer.

## Current Limitations

- Docker/PostgreSQL and Airflow need to be validated on a workstation with Docker available in PATH.
- CONAB data is not yet automated because public releases are distributed mainly through report/data table pages.
