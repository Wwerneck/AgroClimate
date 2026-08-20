from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.exceptions import DataValidationError

BRONZE_REQUIRED_COLUMNS = {
    "timestamp",
    "city",
    "state",
    "latitude",
    "longitude",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation_mm",
    "wind_speed_kmh",
}

SILVER_REQUIRED_COLUMNS = BRONZE_REQUIRED_COLUMNS | {
    "weather_record_id",
    "event_timestamp",
    "event_date",
    "year",
    "month",
}

GOLD_REQUIRED_COLUMNS = {
    "event_date",
    "city",
    "state",
    "region",
    "latitude",
    "longitude",
    "source",
    "avg_temperature",
    "max_temperature",
    "min_temperature",
    "total_precipitation",
    "avg_humidity",
    "days_without_rain",
    "precipitation_accumulated_7d",
    "precipitation_accumulated_30d",
    "avg_temperature_7d",
    "avg_temperature_30d",
    "thermal_amplitude",
    "drought_risk",
    "heat_risk",
    "heavy_rain_risk",
}

AGRICULTURE_GOLD_REQUIRED_COLUMNS = {
    "year",
    "territory_code",
    "territory_name",
    "product_code",
    "product_name",
    "produced_quantity",
    "production_value",
    "harvested_area",
    "reported_yield_kg_ha",
    "reported_yield_t_ha",
    "calculated_yield_t_ha",
}


def validate_bronze_weather(path: Path) -> dict[str, int | str]:
    frame = _read_parquet_dataset(path, "bronze weather")
    _require_columns(frame, BRONZE_REQUIRED_COLUMNS, "bronze weather")
    _require_non_null(frame, ["timestamp", "city", "state", "latitude", "longitude"], "bronze weather")
    _validate_weather_ranges(frame, "bronze weather")
    return {"status": "ok", "records_checked": len(frame)}


def validate_silver_weather(path: Path) -> dict[str, int | str]:
    frame = _read_parquet_dataset(path, "silver weather")
    _require_columns(frame, SILVER_REQUIRED_COLUMNS, "silver weather")
    _require_non_null(
        frame,
        ["weather_record_id", "event_timestamp", "event_date", "city", "state", "latitude", "longitude"],
        "silver weather",
    )
    _validate_weather_ranges(frame, "silver weather")
    if frame["weather_record_id"].duplicated().any():
        raise DataValidationError("silver weather contains duplicate weather_record_id values")
    return {"status": "ok", "records_checked": len(frame)}


def validate_gold_weather(path: Path) -> dict[str, int | str]:
    frame = _read_parquet_dataset(path, "gold weather")
    _require_columns(frame, GOLD_REQUIRED_COLUMNS, "gold weather")
    _require_non_null(frame, ["event_date", "city", "state", "latitude", "longitude"], "gold weather")
    _validate_gold_ranges(frame)
    return {"status": "ok", "records_checked": len(frame)}


def validate_gold_agriculture(path: Path) -> dict[str, int | str]:
    frame = _read_parquet_dataset(path, "gold agriculture")
    _require_columns(frame, AGRICULTURE_GOLD_REQUIRED_COLUMNS, "gold agriculture")
    _require_non_null(
        frame, ["year", "territory_code", "territory_name", "product_code", "product_name"], "gold agriculture"
    )
    checks = [
        ("produced_quantity", frame["produced_quantity"].isna() | frame["produced_quantity"].ge(0)),
        ("production_value", frame["production_value"].isna() | frame["production_value"].ge(0)),
        ("harvested_area", frame["harvested_area"].isna() | frame["harvested_area"].ge(0)),
        ("reported_yield_kg_ha", frame["reported_yield_kg_ha"].isna() | frame["reported_yield_kg_ha"].ge(0)),
    ]
    failed = [column for column, mask in checks if not mask.all()]
    if failed:
        raise DataValidationError(f"gold agriculture contains out-of-range values: {', '.join(failed)}")
    return {"status": "ok", "records_checked": len(frame)}


def _read_parquet_dataset(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise DataValidationError(f"{label} path does not exist: {path}")
    frame = pd.read_parquet(path)
    if frame.empty:
        raise DataValidationError(f"{label} dataset is empty: {path}")
    return frame


def _require_columns(frame: pd.DataFrame, required_columns: set[str], label: str) -> None:
    missing = sorted(required_columns - set(frame.columns))
    if missing:
        raise DataValidationError(f"{label} is missing required columns: {', '.join(missing)}")


def _require_non_null(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    null_columns = [column for column in columns if frame[column].isna().any()]
    if null_columns:
        raise DataValidationError(f"{label} contains nulls in required columns: {', '.join(null_columns)}")


def _validate_weather_ranges(frame: pd.DataFrame, label: str) -> None:
    checks = [
        ("latitude", frame["latitude"].between(-90, 90)),
        ("longitude", frame["longitude"].between(-180, 180)),
        ("relative_humidity_2m", frame["relative_humidity_2m"].isna() | frame["relative_humidity_2m"].between(0, 100)),
        ("precipitation_mm", frame["precipitation_mm"].isna() | frame["precipitation_mm"].ge(0)),
        ("wind_speed_kmh", frame["wind_speed_kmh"].isna() | frame["wind_speed_kmh"].ge(0)),
        ("temperature_2m", frame["temperature_2m"].isna() | frame["temperature_2m"].between(-20, 60)),
    ]
    failed = [column for column, mask in checks if not mask.all()]
    if failed:
        raise DataValidationError(f"{label} contains out-of-range values: {', '.join(failed)}")


def _validate_gold_ranges(frame: pd.DataFrame) -> None:
    checks = [
        ("latitude", frame["latitude"].between(-90, 90)),
        ("longitude", frame["longitude"].between(-180, 180)),
        ("avg_humidity", frame["avg_humidity"].isna() | frame["avg_humidity"].between(0, 100)),
        ("total_precipitation", frame["total_precipitation"].isna() | frame["total_precipitation"].ge(0)),
        ("days_without_rain", frame["days_without_rain"].isna() | frame["days_without_rain"].ge(0)),
        ("avg_temperature", frame["avg_temperature"].isna() | frame["avg_temperature"].between(-20, 60)),
        ("max_temperature", frame["max_temperature"].isna() | frame["max_temperature"].between(-20, 60)),
        ("min_temperature", frame["min_temperature"].isna() | frame["min_temperature"].between(-20, 60)),
    ]
    failed = [column for column, mask in checks if not mask.all()]
    if failed:
        raise DataValidationError(f"gold weather contains out-of-range values: {', '.join(failed)}")
