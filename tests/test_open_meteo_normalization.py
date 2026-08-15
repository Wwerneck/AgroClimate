from src.ingestion.locations import Location
from src.ingestion.weather_ingestion import normalize_open_meteo_payload


def test_normalize_open_meteo_payload_maps_hourly_columns():
    location = Location("Sorriso", "MT", -12.5, -55.7, "Centro-Oeste")
    payload = {
        "latitude": -12.5,
        "longitude": -55.7,
        "hourly": {
            "time": ["2026-08-15T00:00"],
            "temperature_2m": [25.4],
            "relative_humidity_2m": [70],
            "precipitation": [1.2],
            "rain": [1.2],
            "wind_speed_10m": [9.5],
        },
    }

    records = normalize_open_meteo_payload(location, payload)

    assert records[0]["city"] == "Sorriso"
    assert records[0]["temperature_2m"] == 25.4
    assert records[0]["precipitation_mm"] == 1.2
    assert records[0]["wind_speed_kmh"] == 9.5
