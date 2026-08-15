import hashlib
from typing import Any


def weather_record_id(city: Any, timestamp: Any, latitude: Any, longitude: Any) -> str:
    raw = f"{city}|{timestamp}|{latitude}|{longitude}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
