from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg

from src.config.settings import Settings
from src.utils.exceptions import DatabaseLoadError


def load_gold_to_postgres(gold_path: Path, settings: Settings) -> int:
    """Load gold daily weather Parquet files into PostgreSQL using idempotent upserts."""
    try:
        frame = pd.read_parquet(gold_path / "weather_daily")
        with psycopg.connect(settings.postgres_dsn) as conn:
            with conn.cursor() as cur:
                loaded = 0
                for row in frame.to_dict("records"):
                    _upsert_dimensions(cur, row)
                    _upsert_fact(cur, row)
                    loaded += 1
            conn.commit()
        return loaded
    except Exception as exc:
        raise DatabaseLoadError(f"Failed to load gold data into PostgreSQL: {exc}") from exc


def _date_id(value: Any) -> int:
    parsed = pd.to_datetime(value).date() if not isinstance(value, date) else value
    return int(parsed.strftime("%Y%m%d"))


def _upsert_dimensions(cur: psycopg.Cursor, row: dict[str, Any]) -> None:
    event_date = pd.to_datetime(row["event_date"]).date()
    cur.execute(
        """
        INSERT INTO dim_date (date_id, full_date, day, day_of_week, week, month, month_name, quarter, year, is_weekend)
        VALUES (%s, %s, %s, %s, %s, %s, TO_CHAR(%s::date, 'Month'), EXTRACT(QUARTER FROM %s::date), %s, %s)
        ON CONFLICT (date_id) DO NOTHING
        """,
        (
            _date_id(event_date),
            event_date,
            event_date.day,
            event_date.isoweekday(),
            event_date.isocalendar().week,
            event_date.month,
            event_date,
            event_date,
            event_date.year,
            event_date.isoweekday() >= 6,
        ),
    )
    cur.execute(
        """
        INSERT INTO dim_location (city, state, region, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (city, state) DO UPDATE
        SET region = EXCLUDED.region, latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude
        """,
        (row["city"], row["state"], row["region"], row["latitude"], row["longitude"]),
    )
    cur.execute(
        """
        INSERT INTO dim_source (source_name, source_type)
        VALUES (%s, %s)
        ON CONFLICT (source_name) DO NOTHING
        """,
        (row.get("source", "open_meteo"), "weather_api"),
    )


def _upsert_fact(cur: psycopg.Cursor, row: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO fact_weather_daily (
            date_id, location_id, source_id, avg_temperature, max_temperature, min_temperature,
            total_precipitation, avg_humidity, avg_wind_speed, max_wind_speed, solar_radiation,
            evapotranspiration, days_without_rain, drought_risk, heat_risk, heavy_rain_risk
        )
        SELECT %s, l.location_id, s.source_id, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        FROM dim_location l CROSS JOIN dim_source s
        WHERE l.city = %s AND l.state = %s AND s.source_name = %s
        ON CONFLICT (date_id, location_id, source_id) DO UPDATE SET
            avg_temperature = EXCLUDED.avg_temperature,
            max_temperature = EXCLUDED.max_temperature,
            min_temperature = EXCLUDED.min_temperature,
            total_precipitation = EXCLUDED.total_precipitation,
            avg_humidity = EXCLUDED.avg_humidity,
            avg_wind_speed = EXCLUDED.avg_wind_speed,
            max_wind_speed = EXCLUDED.max_wind_speed,
            solar_radiation = EXCLUDED.solar_radiation,
            evapotranspiration = EXCLUDED.evapotranspiration,
            days_without_rain = EXCLUDED.days_without_rain,
            drought_risk = EXCLUDED.drought_risk,
            heat_risk = EXCLUDED.heat_risk,
            heavy_rain_risk = EXCLUDED.heavy_rain_risk
        """,
        (
            _date_id(row["event_date"]),
            row.get("avg_temperature"),
            row.get("max_temperature"),
            row.get("min_temperature"),
            row.get("total_precipitation"),
            row.get("avg_humidity"),
            row.get("avg_wind_speed"),
            row.get("max_wind_speed"),
            row.get("solar_radiation"),
            row.get("evapotranspiration"),
            row.get("days_without_rain"),
            row.get("drought_risk"),
            row.get("heat_risk"),
            row.get("heavy_rain_risk"),
            row["city"],
            row["state"],
            row.get("source", "open_meteo"),
        ),
    )
