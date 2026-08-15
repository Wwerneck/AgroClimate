from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from time import perf_counter
from typing import Any

from src.config.settings import Settings
from src.ingestion.locations import Location, load_locations
from src.ingestion.open_meteo_client import OpenMeteoClient
from src.monitoring.metadata import MetadataStore
from src.storage.local_lake import LocalDataLake

LOGGER = logging.getLogger("agroclimate.ingestion")
PIPELINE_NAME = "weather_ingestion"
SOURCE = "open_meteo"


def _next_date(last_ingested_date: str | None, initial_date: str) -> date:
    if last_ingested_date:
        return date.fromisoformat(last_ingested_date) + timedelta(days=1)
    return date.fromisoformat(initial_date)


def normalize_open_meteo_payload(location: Location, payload: dict[str, Any]) -> list[dict[str, Any]]:
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    records: list[dict[str, Any]] = []
    for index, timestamp in enumerate(times):
        record = {
            "timestamp": timestamp,
            "city": location.city,
            "state": location.state,
            "region": location.region,
            "latitude": payload.get("latitude", location.latitude),
            "longitude": payload.get("longitude", location.longitude),
            "temperature_2m": _get(hourly, "temperature_2m", index),
            "relative_humidity_2m": _get(hourly, "relative_humidity_2m", index),
            "precipitation_mm": _get(hourly, "precipitation", index),
            "rain_mm": _get(hourly, "rain", index),
            "wind_speed_kmh": _get(hourly, "wind_speed_10m", index),
            "wind_direction_10m": _get(hourly, "wind_direction_10m", index),
            "surface_pressure_hpa": _get(hourly, "surface_pressure", index),
            "soil_temperature_0_to_7cm": _get(hourly, "soil_temperature_0_to_7cm", index),
            "soil_moisture_0_to_7cm": _get(hourly, "soil_moisture_0_to_7cm", index),
            "shortwave_radiation": _get(hourly, "shortwave_radiation", index),
            "evapotranspiration": _get(hourly, "et0_fao_evapotranspiration", index),
        }
        records.append(record)
    return records


def _get(values: dict[str, list[Any]], key: str, index: int) -> Any:
    column = values.get(key) or []
    return column[index] if index < len(column) else None


def run_weather_ingestion(settings: Settings, execution_id: str) -> dict[str, Any]:
    started = perf_counter()
    metadata_store = MetadataStore(settings.metadata_dir)
    metadata = metadata_store.load(PIPELINE_NAME, SOURCE)
    start_date = _next_date(metadata.last_ingested_date, settings.initial_ingestion_date)
    end_date = datetime.now().date()
    if start_date > end_date:
        LOGGER.info("no new dates to ingest start_date=%s end_date=%s", start_date, end_date)
        return {"records_extracted": 0, "last_ingested_date": metadata.last_ingested_date}

    client = OpenMeteoClient(settings.api_timeout, settings.api_retries, settings.api_retry_backoff_seconds)
    lake = LocalDataLake(settings.data_dir)
    all_records: list[dict[str, Any]] = []

    for location in load_locations():
        payload = client.fetch_weather(location, start_date, end_date)
        all_records.extend(normalize_open_meteo_payload(location, payload))

    lake.write_bronze_weather(all_records, end_date, execution_id)
    elapsed = perf_counter() - started
    metadata_store.record_success(PIPELINE_NAME, SOURCE, end_date, len(all_records), elapsed)
    metadata_store.append_run(
        execution_id,
        {
            "started_at": datetime.utcnow().isoformat(),
            "finished_at": datetime.utcnow().isoformat(),
            "duration_seconds": elapsed,
            "records_extracted": len(all_records),
            "status": "success",
        },
    )
    LOGGER.info("ingestion completed records=%s elapsed=%.2f", len(all_records), elapsed)
    return {"records_extracted": len(all_records), "last_ingested_date": end_date.isoformat()}
