from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.processing.ids import weather_record_id
from src.processing.parquet_io import read_parquet_files


def bronze_to_silver_local(bronze_path: Path, silver_path: Path) -> int:
    """Local fallback for machines without Java/Spark; PySpark remains the production path."""
    frame = pd.read_parquet(bronze_path)
    frame["weather_record_id"] = frame.apply(
        lambda row: weather_record_id(row["city"], row["timestamp"], row["latitude"], row["longitude"]),
        axis=1,
    )
    frame["event_timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame["event_date"] = frame["event_timestamp"].dt.date
    numeric_columns = [
        "latitude",
        "longitude",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation_mm",
        "rain_mm",
        "wind_speed_kmh",
        "shortwave_radiation",
        "evapotranspiration",
    ]
    for column in numeric_columns:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    mask = (
        frame["event_timestamp"].notna()
        & frame["city"].astype(str).str.strip().ne("")
        & frame["latitude"].between(-90, 90)
        & frame["longitude"].between(-180, 180)
        & (frame["relative_humidity_2m"].isna() | frame["relative_humidity_2m"].between(0, 100))
        & (frame["precipitation_mm"].isna() | (frame["precipitation_mm"] >= 0))
        & (frame["wind_speed_kmh"].isna() | (frame["wind_speed_kmh"] >= 0))
        & (frame["temperature_2m"].isna() | frame["temperature_2m"].between(-20, 60))
    )
    silver = frame.loc[mask].drop_duplicates(subset=["weather_record_id"]).copy()
    silver["year"] = pd.to_datetime(silver["event_date"]).dt.year
    silver["month"] = pd.to_datetime(silver["event_date"]).dt.month
    target = silver_path / "weather"
    target.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(target / "silver_weather.parquet", index=False)
    return len(silver)


def silver_to_gold_local(silver_path: Path, gold_path: Path) -> int:
    """Local fallback daily aggregation for machines without Java/Spark."""
    frame = pd.read_parquet(silver_path / "weather")
    grouped = (
        frame.groupby(["event_date", "city", "state", "region", "latitude", "longitude", "source"], dropna=False)
        .agg(
            avg_temperature=("temperature_2m", "mean"),
            max_temperature=("temperature_2m", "max"),
            min_temperature=("temperature_2m", "min"),
            total_precipitation=("precipitation_mm", "sum"),
            avg_humidity=("relative_humidity_2m", "mean"),
            avg_wind_speed=("wind_speed_kmh", "mean"),
            max_wind_speed=("wind_speed_kmh", "max"),
            solar_radiation=("shortwave_radiation", "sum"),
            evapotranspiration=("evapotranspiration", "sum"),
        )
        .reset_index()
        .sort_values(["city", "state", "event_date"])
    )
    grouped["is_dry_day"] = (grouped["total_precipitation"].fillna(0) < 1).astype(int)
    city_group = grouped.groupby(["city", "state"], group_keys=False)
    grouped["days_without_rain"] = city_group["is_dry_day"].transform(lambda s: s.rolling(7, min_periods=1).sum())
    grouped["precipitation_accumulated_7d"] = city_group["total_precipitation"].transform(
        lambda s: s.rolling(7, min_periods=1).sum()
    )
    grouped["precipitation_accumulated_30d"] = city_group["total_precipitation"].transform(
        lambda s: s.rolling(30, min_periods=1).sum()
    )
    grouped["avg_temperature_7d"] = city_group["avg_temperature"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    grouped["avg_temperature_30d"] = city_group["avg_temperature"].transform(
        lambda s: s.rolling(30, min_periods=1).mean()
    )
    grouped["thermal_amplitude"] = grouped["max_temperature"] - grouped["min_temperature"]
    grouped["drought_risk"] = "normal"
    grouped.loc[
        (grouped["precipitation_accumulated_7d"] <= 5)
        & (grouped["days_without_rain"] >= 7)
        & (grouped["avg_temperature_7d"] >= 30),
        "drought_risk",
    ] = "high"
    grouped["heat_risk"] = grouped["max_temperature"].ge(35).map({True: "high", False: "normal"})
    grouped["heavy_rain_risk"] = grouped["total_precipitation"].ge(50).map({True: "high", False: "normal"})
    grouped["year"] = pd.to_datetime(grouped["event_date"]).dt.year
    grouped["month"] = pd.to_datetime(grouped["event_date"]).dt.month
    target = gold_path / "weather_daily"
    target.mkdir(parents=True, exist_ok=True)
    grouped.to_parquet(target / "gold_weather_daily.parquet", index=False)
    return len(grouped)


def _read_parquet_files(path: Path) -> pd.DataFrame:
    return read_parquet_files(path)
