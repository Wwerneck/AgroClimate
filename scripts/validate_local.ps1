param(
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"

Write-Host "== AgroClimate local validation =="

Write-Host "1. Python quality checks"
.venv\Scripts\python -m pytest
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m black --check src tests dags dashboard

Write-Host "2. Local ingestion and Parquet fallback"
.venv\Scripts\python -m src.pipeline
.venv\Scripts\python -c "from src.config.settings import get_settings; from src.processing.local_fallback import bronze_to_silver_local, silver_to_gold_local; s=get_settings(); print('silver', bronze_to_silver_local(s.bronze_dir / 'weather', s.silver_dir)); print('gold', silver_to_gold_local(s.silver_dir, s.gold_dir))"

if (-not $SkipDocker) {
    Write-Host "3. Docker Compose"
    docker compose up -d
}

Write-Host "Validation finished."

