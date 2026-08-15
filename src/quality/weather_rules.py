from __future__ import annotations

from datetime import datetime
from typing import Any


def validate_weather_record(record: dict[str, Any], execution_id: str) -> tuple[bool, dict[str, Any] | None]:
    reasons: list[str] = []
    if not record.get("timestamp"):
        reasons.append("timestamp_is_required")
    if not record.get("city"):
        reasons.append("city_is_required")
    _between(record, "latitude", -90, 90, reasons)
    _between(record, "longitude", -180, 180, reasons)
    _between(record, "relative_humidity_2m", 0, 100, reasons, allow_null=True)
    _minimum(record, "precipitation_mm", 0, reasons, allow_null=True)
    _minimum(record, "wind_speed_kmh", 0, reasons, allow_null=True)
    _between(record, "temperature_2m", -20, 60, reasons, allow_null=True)
    if not reasons:
        return True, None
    return False, {
        "record": record,
        "reason": ",".join(reasons),
        "validation_timestamp": datetime.utcnow().isoformat(),
        "pipeline_execution_id": execution_id,
    }


def split_valid_invalid(
    records: list[dict[str, Any]], execution_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for record in records:
        key = (
            record.get("city"),
            record.get("timestamp"),
            record.get("latitude"),
            record.get("longitude"),
        )
        is_valid, rejected = validate_weather_record(record, execution_id)
        if key in seen:
            is_valid = False
            rejected = {
                "record": record,
                "reason": "duplicate_record",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "pipeline_execution_id": execution_id,
            }
        if is_valid:
            seen.add(key)
            valid.append(record)
        elif rejected:
            invalid.append(rejected)
    return valid, invalid


def _between(
    record: dict[str, Any],
    field: str,
    minimum: float,
    maximum: float,
    reasons: list[str],
    allow_null: bool = False,
) -> None:
    value = record.get(field)
    if value is None and allow_null:
        return
    if value is None or not minimum <= float(value) <= maximum:
        reasons.append(f"{field}_out_of_range")


def _minimum(
    record: dict[str, Any],
    field: str,
    minimum: float,
    reasons: list[str],
    allow_null: bool = False,
) -> None:
    value = record.get(field)
    if value is None and allow_null:
        return
    if value is None or float(value) < minimum:
        reasons.append(f"{field}_below_minimum")
