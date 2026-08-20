from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg

from src.config.settings import Settings
from src.utils.exceptions import DatabaseLoadError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = PROJECT_ROOT / "sql"


def load_gold_to_postgres(gold_path: Path, settings: Settings) -> int:
    """Load gold daily weather Parquet files into PostgreSQL using idempotent upserts."""
    try:
        frame = pd.read_parquet(gold_path / "weather_daily")
        with psycopg.connect(settings.postgres_dsn) as conn:
            _ensure_warehouse_schema(conn)
            with conn.cursor() as cur:
                loaded = _load_weather_daily(cur, frame)
                loaded += _load_agriculture_summary(cur, gold_path)
            conn.commit()
        return loaded
    except Exception as exc:
        raise DatabaseLoadError(f"Failed to load gold data into PostgreSQL: {exc}") from exc


def _date_id(value: Any) -> int:
    parsed = pd.to_datetime(value).date() if not isinstance(value, date) else value
    return int(parsed.strftime("%Y%m%d"))


def _ensure_warehouse_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        for sql_file in _schema_sql_files():
            cur.execute(sql_file.read_text(encoding="utf-8"))


def _schema_sql_files() -> list[Path]:
    migration_files = sorted((SQL_DIR / "migrations").glob("*.sql")) if (SQL_DIR / "migrations").exists() else []
    return [SQL_DIR / "schema.sql", *migration_files, SQL_DIR / "indexes.sql"]


def _load_weather_daily(cur: psycopg.Cursor, frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    rows = [_weather_staging_row(row) for row in _records(frame)]
    cur.execute("""
        CREATE TEMP TABLE staging_weather_daily (
            date_id INTEGER,
            event_date DATE,
            city TEXT,
            state TEXT,
            region TEXT,
            latitude NUMERIC,
            longitude NUMERIC,
            source TEXT,
            avg_temperature NUMERIC,
            max_temperature NUMERIC,
            min_temperature NUMERIC,
            total_precipitation NUMERIC,
            avg_humidity NUMERIC,
            avg_wind_speed NUMERIC,
            max_wind_speed NUMERIC,
            solar_radiation NUMERIC,
            evapotranspiration NUMERIC,
            days_without_rain INTEGER,
            precipitation_accumulated_7d NUMERIC,
            precipitation_accumulated_30d NUMERIC,
            avg_temperature_7d NUMERIC,
            avg_temperature_30d NUMERIC,
            thermal_amplitude NUMERIC,
            drought_risk TEXT,
            heat_risk TEXT,
            heavy_rain_risk TEXT
        ) ON COMMIT DROP
        """)
    cur.executemany(
        """
        INSERT INTO staging_weather_daily (
            date_id, event_date, city, state, region, latitude, longitude, source,
            avg_temperature, max_temperature, min_temperature, total_precipitation,
            avg_humidity, avg_wind_speed, max_wind_speed, solar_radiation,
            evapotranspiration, days_without_rain, precipitation_accumulated_7d,
            precipitation_accumulated_30d, avg_temperature_7d, avg_temperature_30d,
            thermal_amplitude, drought_risk, heat_risk, heavy_rain_risk
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        rows,
    )
    _merge_weather_dimensions(cur)
    _merge_weather_facts(cur)
    return len(rows)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    normalized = frame.astype(object).where(pd.notna(frame), None)
    return normalized.to_dict("records")


def _weather_staging_row(row: dict[str, Any]) -> tuple[Any, ...]:
    event_date = pd.to_datetime(row["event_date"]).date()
    return (
        _date_id(event_date),
        event_date,
        row["city"],
        row["state"],
        row["region"],
        row["latitude"],
        row["longitude"],
        row.get("source", "open_meteo"),
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
        row.get("precipitation_accumulated_7d"),
        row.get("precipitation_accumulated_30d"),
        row.get("avg_temperature_7d"),
        row.get("avg_temperature_30d"),
        row.get("thermal_amplitude"),
        row.get("drought_risk"),
        row.get("heat_risk"),
        row.get("heavy_rain_risk"),
    )


def _merge_weather_dimensions(cur: psycopg.Cursor) -> None:
    cur.execute("""
        INSERT INTO dim_date (date_id, full_date, day, day_of_week, week, month, month_name, quarter, year, is_weekend)
        SELECT DISTINCT
            date_id,
            event_date,
            EXTRACT(DAY FROM event_date)::INTEGER,
            EXTRACT(ISODOW FROM event_date)::INTEGER,
            EXTRACT(WEEK FROM event_date)::INTEGER,
            EXTRACT(MONTH FROM event_date)::INTEGER,
            TO_CHAR(event_date, 'Month'),
            EXTRACT(QUARTER FROM event_date)::INTEGER,
            EXTRACT(YEAR FROM event_date)::INTEGER,
            EXTRACT(ISODOW FROM event_date)::INTEGER >= 6
        FROM staging_weather_daily
        ON CONFLICT (date_id) DO NOTHING
        """)
    cur.execute("""
        INSERT INTO dim_location (city, state, region, latitude, longitude)
        SELECT DISTINCT city, state, region, latitude, longitude
        FROM staging_weather_daily
        ON CONFLICT (city, state) DO UPDATE
        SET region = EXCLUDED.region, latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude
        """)
    cur.execute("""
        INSERT INTO dim_source (source_name, source_type)
        SELECT DISTINCT source, 'weather_api'
        FROM staging_weather_daily
        ON CONFLICT (source_name) DO NOTHING
        """)


def _merge_weather_facts(cur: psycopg.Cursor) -> None:
    cur.execute("""
        INSERT INTO fact_weather_daily (
            date_id, location_id, source_id, avg_temperature, max_temperature, min_temperature,
            total_precipitation, avg_humidity, avg_wind_speed, max_wind_speed, solar_radiation,
            evapotranspiration, days_without_rain, precipitation_accumulated_7d,
            precipitation_accumulated_30d, avg_temperature_7d, avg_temperature_30d,
            thermal_amplitude, drought_risk, heat_risk, heavy_rain_risk
        )
        SELECT
            stg.date_id, l.location_id, s.source_id, stg.avg_temperature, stg.max_temperature,
            stg.min_temperature, stg.total_precipitation, stg.avg_humidity, stg.avg_wind_speed,
            stg.max_wind_speed, stg.solar_radiation, stg.evapotranspiration,
            stg.days_without_rain, stg.precipitation_accumulated_7d,
            stg.precipitation_accumulated_30d, stg.avg_temperature_7d,
            stg.avg_temperature_30d, stg.thermal_amplitude, stg.drought_risk,
            stg.heat_risk, stg.heavy_rain_risk
        FROM staging_weather_daily stg
        JOIN dim_location l ON l.city = stg.city AND l.state = stg.state
        JOIN dim_source s ON s.source_name = stg.source
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
            precipitation_accumulated_7d = EXCLUDED.precipitation_accumulated_7d,
            precipitation_accumulated_30d = EXCLUDED.precipitation_accumulated_30d,
            avg_temperature_7d = EXCLUDED.avg_temperature_7d,
            avg_temperature_30d = EXCLUDED.avg_temperature_30d,
            thermal_amplitude = EXCLUDED.thermal_amplitude,
            drought_risk = EXCLUDED.drought_risk,
            heat_risk = EXCLUDED.heat_risk,
            heavy_rain_risk = EXCLUDED.heavy_rain_risk
        """)


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
            evapotranspiration, days_without_rain, precipitation_accumulated_7d,
            precipitation_accumulated_30d, avg_temperature_7d, avg_temperature_30d,
            thermal_amplitude, drought_risk, heat_risk, heavy_rain_risk
        )
        SELECT %s, l.location_id, s.source_id, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
            precipitation_accumulated_7d = EXCLUDED.precipitation_accumulated_7d,
            precipitation_accumulated_30d = EXCLUDED.precipitation_accumulated_30d,
            avg_temperature_7d = EXCLUDED.avg_temperature_7d,
            avg_temperature_30d = EXCLUDED.avg_temperature_30d,
            thermal_amplitude = EXCLUDED.thermal_amplitude,
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
            row.get("precipitation_accumulated_7d"),
            row.get("precipitation_accumulated_30d"),
            row.get("avg_temperature_7d"),
            row.get("avg_temperature_30d"),
            row.get("thermal_amplitude"),
            row.get("drought_risk"),
            row.get("heat_risk"),
            row.get("heavy_rain_risk"),
            row["city"],
            row["state"],
            row.get("source", "open_meteo"),
        ),
    )


def _load_agriculture_summary(cur: psycopg.Cursor, gold_path: Path) -> int:
    agriculture_path = gold_path / "agriculture_summary"
    if not agriculture_path.exists():
        return 0
    frame = pd.read_parquet(agriculture_path)
    loaded = 0
    for row in frame.to_dict("records"):
        _upsert_agriculture_fact(cur, row)
        loaded += 1
    return loaded


def _upsert_agriculture_fact(cur: psycopg.Cursor, row: dict[str, Any]) -> None:
    source_name = row.get("source", "ibge_pam")
    cur.execute(
        """
        INSERT INTO dim_source (source_name, source_type)
        VALUES (%s, %s)
        ON CONFLICT (source_name) DO NOTHING
        """,
        (source_name, "agriculture_statistics"),
    )
    cur.execute(
        """
        INSERT INTO dim_crop (crop_code, crop_name)
        VALUES (%s, %s)
        ON CONFLICT (crop_code) DO UPDATE SET crop_name = EXCLUDED.crop_name
        """,
        (row["product_code"], row["product_name"]),
    )
    cur.execute(
        """
        INSERT INTO fact_agriculture_production (
            year, state_code, state_name, crop_id, source_id, produced_quantity,
            production_value, harvested_area, reported_yield_kg_ha,
            reported_yield_t_ha, calculated_yield_t_ha
        )
        SELECT %s, %s, %s, c.crop_id, s.source_id, %s, %s, %s, %s, %s, %s
        FROM dim_crop c CROSS JOIN dim_source s
        WHERE c.crop_code = %s AND s.source_name = %s
        ON CONFLICT (year, state_code, crop_id, source_id) DO UPDATE SET
            state_name = EXCLUDED.state_name,
            produced_quantity = EXCLUDED.produced_quantity,
            production_value = EXCLUDED.production_value,
            harvested_area = EXCLUDED.harvested_area,
            reported_yield_kg_ha = EXCLUDED.reported_yield_kg_ha,
            reported_yield_t_ha = EXCLUDED.reported_yield_t_ha,
            calculated_yield_t_ha = EXCLUDED.calculated_yield_t_ha
        """,
        (
            row["year"],
            row["territory_code"],
            row["territory_name"],
            row.get("produced_quantity"),
            row.get("production_value"),
            row.get("harvested_area"),
            row.get("reported_yield_kg_ha"),
            row.get("reported_yield_t_ha"),
            row.get("calculated_yield_t_ha"),
            row["product_code"],
            source_name,
        ),
    )
