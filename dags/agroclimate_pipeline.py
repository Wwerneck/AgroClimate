from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task

from src.config.settings import get_settings
from src.ingestion.agriculture_ingestion import run_agriculture_ingestion
from src.ingestion.weather_ingestion import run_weather_ingestion
from src.processing.agriculture_bronze_to_silver import agriculture_bronze_to_silver_local
from src.processing.agriculture_silver_to_gold import agriculture_silver_to_gold_local
from src.processing.bronze_to_silver import run as bronze_to_silver
from src.processing.silver_to_gold import run as silver_to_gold
from src.quality.lake_checks import (
    validate_bronze_weather,
    validate_gold_agriculture,
    validate_gold_weather,
    validate_silver_weather,
)
from src.utils.logging import configure_logging
from src.warehouse.load_postgres import load_gold_to_postgres


@dag(
    dag_id="agroclimate_pipeline",
    description="Ingests Open-Meteo data and builds Bronze, Silver, Gold and PostgreSQL warehouse layers.",
    start_date=datetime(2026, 8, 1),
    schedule="@daily",
    catchup=False,
    default_args={
        "owner": "data-engineering",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "execution_timeout": timedelta(minutes=45),
    },
    tags=["agroclimate", "weather", "spark", "postgres"],
)
def agroclimate_pipeline():
    @task
    def extract_weather(**context):
        settings = get_settings()
        configure_logging(settings.log_level)
        return run_weather_ingestion(settings, context["run_id"])

    @task
    def extract_agriculture(**context):
        settings = get_settings()
        configure_logging(settings.log_level)
        return run_agriculture_ingestion(settings, context["run_id"])

    @task
    def validate_raw():
        settings = get_settings()
        return validate_bronze_weather(settings.bronze_dir / "weather")

    @task
    def process_bronze_to_silver():
        settings = get_settings()
        bronze_to_silver(settings.bronze_dir / "weather", settings.silver_dir)
        return {"status": "ok"}

    @task
    def silver_quality_checks():
        settings = get_settings()
        return validate_silver_weather(settings.silver_dir / "weather")

    @task
    def process_silver_to_gold():
        settings = get_settings()
        silver_to_gold(settings.silver_dir, settings.gold_dir)
        return {"status": "ok"}

    @task
    def process_agriculture_bronze_to_silver():
        settings = get_settings()
        records = agriculture_bronze_to_silver_local(settings.bronze_dir / "agriculture", settings.silver_dir)
        return {"records_silver": records}

    @task
    def process_agriculture_silver_to_gold():
        settings = get_settings()
        records = agriculture_silver_to_gold_local(settings.silver_dir, settings.gold_dir)
        return {"records_gold": records}

    @task
    def gold_quality_checks():
        settings = get_settings()
        return validate_gold_weather(settings.gold_dir / "weather_daily")

    @task
    def agriculture_gold_quality_checks():
        settings = get_settings()
        return validate_gold_agriculture(settings.gold_dir / "agriculture_summary")

    @task
    def load_postgresql():
        settings = get_settings()
        return {"records_loaded": load_gold_to_postgres(Path(settings.gold_dir), settings)}

    extracted = extract_weather()
    agriculture_extracted = extract_agriculture()
    raw_validated = validate_raw()
    silver = process_bronze_to_silver()
    extracted >> raw_validated >> silver >> silver_quality_checks()
    gold = process_silver_to_gold()
    agriculture_silver = process_agriculture_bronze_to_silver()
    agriculture_gold = process_agriculture_silver_to_gold()
    agriculture_validated = agriculture_gold_quality_checks()
    agriculture_extracted >> agriculture_silver >> agriculture_gold >> agriculture_validated
    silver >> gold >> gold_quality_checks()
    [gold, agriculture_validated] >> load_postgresql()


agroclimate_pipeline()
