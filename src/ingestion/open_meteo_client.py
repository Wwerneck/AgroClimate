from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any

from src.ingestion.locations import Location
from src.utils.exceptions import APIConnectionError

LOGGER = logging.getLogger("agroclimate.ingestion")


class OpenMeteoClient:
    """Client for Open-Meteo archive API with retry and timeout handling."""

    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    hourly_variables = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "rain",
        "wind_speed_10m",
        "wind_direction_10m",
        "surface_pressure",
        "soil_temperature_0_to_7cm",
        "soil_moisture_0_to_7cm",
        "shortwave_radiation",
        "et0_fao_evapotranspiration",
    ]
    daily_variables = ["temperature_2m_max", "temperature_2m_min"]

    def __init__(self, timeout: float, retries: int, backoff_seconds: float) -> None:
        self.timeout = timeout
        self.retries = retries
        self.backoff_seconds = backoff_seconds

    def fetch_weather(self, location: Location, start_date: date, end_date: date) -> dict[str, Any]:
        try:
            import httpx
        except ModuleNotFoundError as exc:
            raise APIConnectionError("httpx is required to fetch Open-Meteo data") from exc

        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": ",".join(self.hourly_variables),
            "daily": ",".join(self.daily_variables),
            "timezone": "America/Sao_Paulo",
        }
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(self.BASE_URL, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    LOGGER.info(
                        "received weather payload city=%s status=%s",
                        location.city,
                        response.status_code,
                    )
                    return payload
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                LOGGER.warning("api request failed city=%s attempt=%s error=%s", location.city, attempt, exc)
                if attempt < self.retries:
                    time.sleep(self.backoff_seconds * attempt)
        raise APIConnectionError(f"Open-Meteo request failed for {location.city}: {last_error}")
