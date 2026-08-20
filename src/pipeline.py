from __future__ import annotations

import logging

from src.config.settings import get_settings
from src.ingestion.agriculture_ingestion import run_agriculture_ingestion
from src.ingestion.weather_ingestion import run_weather_ingestion
from src.monitoring.metadata import MetadataStore
from src.processing.agriculture_bronze_to_silver import agriculture_bronze_to_silver_local
from src.processing.agriculture_silver_to_gold import agriculture_silver_to_gold_local
from src.processing.local_fallback import (
    bronze_to_silver_local,
    silver_to_gold_local,
)
from src.utils.logging import configure_logging, new_execution_id

LOGGER = logging.getLogger("agroclimate.pipeline")


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    execution_id = new_execution_id()
    metadata_store = MetadataStore(settings.metadata_dir)
    run_weather_ingestion(settings, execution_id)
    try:
        run_agriculture_ingestion(settings, execution_id)
        agriculture_silver_records = agriculture_bronze_to_silver_local(
            settings.bronze_dir / "agriculture", settings.silver_dir
        )
        metadata_store.append_dataset_metric(execution_id, "agriculture", "silver", agriculture_silver_records)
        agriculture_gold_records = agriculture_silver_to_gold_local(settings.silver_dir, settings.gold_dir)
        metadata_store.append_dataset_metric(execution_id, "agriculture", "gold", agriculture_gold_records)
    except Exception as exc:
        if settings.strict_pipeline:
            raise
        LOGGER.warning("agriculture ingestion skipped error=%s", exc)
    try:
        from src.processing.bronze_to_silver import run as bronze_to_silver
        from src.processing.silver_to_gold import run as silver_to_gold

        bronze_to_silver(settings.bronze_dir / "weather", settings.silver_dir)
        silver_to_gold(settings.silver_dir, settings.gold_dir)
    except Exception as exc:
        if settings.strict_pipeline:
            raise
        LOGGER.warning("spark processing failed; using local pandas fallback error=%s", exc)
        weather_silver_records = bronze_to_silver_local(settings.bronze_dir / "weather", settings.silver_dir)
        metadata_store.append_dataset_metric(execution_id, "weather", "silver", weather_silver_records)
        weather_gold_records = silver_to_gold_local(settings.silver_dir, settings.gold_dir)
        metadata_store.append_dataset_metric(execution_id, "weather", "gold", weather_gold_records)


if __name__ == "__main__":
    main()
