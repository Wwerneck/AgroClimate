from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class DroughtThresholds:
    precipitation_7d_max_mm: float = 5
    consecutive_dry_days_min: int = 7
    avg_temperature_7d_min_c: float = 30


@dataclass(frozen=True)
class HeatThresholds:
    max_temperature_c: float = 35


@dataclass(frozen=True)
class HeavyRainThresholds:
    daily_precipitation_mm: float = 50


@dataclass(frozen=True)
class WeatherQualityThresholds:
    min_temperature_c: float = -20
    max_temperature_c: float = 60
    min_humidity_pct: float = 0
    max_humidity_pct: float = 100
    min_precipitation_mm: float = 0
    min_wind_speed_kmh: float = 0


@dataclass(frozen=True)
class RiskThresholds:
    drought: DroughtThresholds = DroughtThresholds()
    heat: HeatThresholds = HeatThresholds()
    heavy_rain: HeavyRainThresholds = HeavyRainThresholds()
    quality: WeatherQualityThresholds = WeatherQualityThresholds()


def _coerce_number(value: str) -> float | int:
    parsed = float(value)
    return int(parsed) if parsed.is_integer() else parsed


def _parse_simple_yaml(path: Path) -> dict[str, dict[str, float | int]]:
    parsed: dict[str, dict[str, float | int]] = {}
    current_section: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not raw_line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1]
            parsed[current_section] = {}
            continue
        if current_section and ":" in line:
            key, value = line.split(":", 1)
            parsed[current_section][key.strip()] = _coerce_number(value.strip())
    return parsed


@lru_cache
def load_risk_thresholds(path: Path | None = None) -> RiskThresholds:
    config_path = path or Path(__file__).with_name("risk_thresholds.yml")
    if not config_path.exists():
        return RiskThresholds()
    values = _parse_simple_yaml(config_path)
    return RiskThresholds(
        drought=DroughtThresholds(**values.get("drought", {})),
        heat=HeatThresholds(**values.get("heat", {})),
        heavy_rain=HeavyRainThresholds(**values.get("heavy_rain", {})),
        quality=WeatherQualityThresholds(**values.get("quality", {})),
    )
