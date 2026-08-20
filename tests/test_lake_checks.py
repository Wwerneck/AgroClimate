import pandas as pd
import pytest

from src.quality.lake_checks import validate_gold_weather, validate_silver_weather
from src.utils.exceptions import DataValidationError


def test_validate_silver_weather_accepts_valid_dataset(tmp_path):
    path = tmp_path / "silver" / "weather"
    path.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "timestamp": "2026-08-15T00:00",
                "city": "Sorriso",
                "state": "MT",
                "latitude": -12.5,
                "longitude": -55.7,
                "temperature_2m": 25,
                "relative_humidity_2m": 70,
                "precipitation_mm": 0,
                "wind_speed_kmh": 5,
                "weather_record_id": "record-1",
                "event_timestamp": pd.Timestamp("2026-08-15T00:00"),
                "event_date": pd.Timestamp("2026-08-15").date(),
                "year": 2026,
                "month": 8,
            }
        ]
    ).to_parquet(path / "part.parquet", index=False)

    result = validate_silver_weather(path)

    assert result == {"status": "ok", "records_checked": 1}


def test_validate_silver_weather_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "silver" / "weather"
    path.mkdir(parents=True)
    row = {
        "timestamp": "2026-08-15T00:00",
        "city": "Sorriso",
        "state": "MT",
        "latitude": -12.5,
        "longitude": -55.7,
        "temperature_2m": 25,
        "relative_humidity_2m": 70,
        "precipitation_mm": 0,
        "wind_speed_kmh": 5,
        "weather_record_id": "record-1",
        "event_timestamp": pd.Timestamp("2026-08-15T00:00"),
        "event_date": pd.Timestamp("2026-08-15").date(),
        "year": 2026,
        "month": 8,
    }
    pd.DataFrame([row, row]).to_parquet(path / "part.parquet", index=False)

    with pytest.raises(DataValidationError, match="duplicate weather_record_id"):
        validate_silver_weather(path)


def test_validate_gold_weather_rejects_missing_dashboard_columns(tmp_path):
    path = tmp_path / "gold" / "weather_daily"
    path.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "event_date": pd.Timestamp("2026-08-15").date(),
                "city": "Sorriso",
                "state": "MT",
                "region": "Centro-Oeste",
                "latitude": -12.5,
                "longitude": -55.7,
                "source": "open_meteo",
                "avg_temperature": 25,
                "max_temperature": 30,
                "min_temperature": 20,
                "total_precipitation": 0,
                "avg_humidity": 70,
                "days_without_rain": 1,
                "drought_risk": "normal",
                "heat_risk": "normal",
                "heavy_rain_risk": "normal",
            }
        ]
    ).to_parquet(path / "part.parquet", index=False)

    with pytest.raises(DataValidationError, match="thermal_amplitude"):
        validate_gold_weather(path)
