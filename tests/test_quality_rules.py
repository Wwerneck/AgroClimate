from src.quality.weather_rules import split_valid_invalid, validate_weather_record


def test_validate_weather_record_accepts_valid_record():
    record = {
        "timestamp": "2026-08-15T00:00",
        "city": "Sorriso",
        "latitude": -12.5,
        "longitude": -55.7,
        "relative_humidity_2m": 70,
        "precipitation_mm": 0,
        "wind_speed_kmh": 5,
        "temperature_2m": 25,
    }

    is_valid, rejected = validate_weather_record(record, "exec")

    assert is_valid is True
    assert rejected is None


def test_split_valid_invalid_quarantines_duplicates():
    record = {
        "timestamp": "2026-08-15T00:00",
        "city": "Sorriso",
        "latitude": -12.5,
        "longitude": -55.7,
    }

    valid, invalid = split_valid_invalid([record, record], "exec")

    assert len(valid) == 1
    assert invalid[0]["reason"] == "duplicate_record"
