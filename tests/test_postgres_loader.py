import sys
from datetime import date
from types import SimpleNamespace

import pandas as pd

sys.modules.setdefault("psycopg", SimpleNamespace(Cursor=object))

from src.warehouse.load_postgres import (  # noqa: E402
    _load_weather_daily,
    _schema_sql_files,
    _upsert_agriculture_fact,
    _upsert_fact,
)


def test_schema_sql_files_apply_schema_then_migrations_then_indexes():
    files = [path.name for path in _schema_sql_files()]

    assert files[0] == "schema.sql"
    assert "001_add_gold_rolling_metrics.sql" in files
    assert "002_add_agriculture_warehouse.sql" in files
    assert files[-1] == "indexes.sql"


class FakeCursor:
    def __init__(self):
        self.sql = ""
        self.params = ()
        self.executemany_sql = ""
        self.executemany_params = []
        self.statements = []

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params or ()
        self.statements.append(sql)

    def executemany(self, sql, params):
        self.executemany_sql = sql
        self.executemany_params = params


def test_upsert_fact_loads_gold_rolling_metrics():
    cursor = FakeCursor()
    row = {
        "event_date": date(2026, 8, 15),
        "avg_temperature": 29.4,
        "max_temperature": 35.1,
        "min_temperature": 22.3,
        "total_precipitation": 4.2,
        "avg_humidity": 66.5,
        "avg_wind_speed": 12.1,
        "max_wind_speed": 28.4,
        "solar_radiation": 810.0,
        "evapotranspiration": 5.6,
        "days_without_rain": 3,
        "precipitation_accumulated_7d": 12.3,
        "precipitation_accumulated_30d": 92.4,
        "avg_temperature_7d": 28.7,
        "avg_temperature_30d": 27.9,
        "thermal_amplitude": 12.8,
        "drought_risk": "normal",
        "heat_risk": "high",
        "heavy_rain_risk": "normal",
        "city": "Sorriso",
        "state": "MT",
        "source": "open_meteo",
    }

    _upsert_fact(cursor, row)

    assert "precipitation_accumulated_7d" in cursor.sql
    assert "precipitation_accumulated_30d" in cursor.sql
    assert "avg_temperature_7d" in cursor.sql
    assert "avg_temperature_30d" in cursor.sql
    assert "thermal_amplitude" in cursor.sql
    assert 12.3 in cursor.params
    assert 92.4 in cursor.params
    assert 28.7 in cursor.params
    assert 27.9 in cursor.params
    assert 12.8 in cursor.params


def test_upsert_agriculture_fact_loads_crop_and_production_metrics():
    cursor = FakeCursor()
    row = {
        "year": 2024,
        "territory_code": "51",
        "territory_name": "Mato Grosso",
        "product_code": "2713",
        "product_name": "Soja",
        "produced_quantity": 1000,
        "production_value": 3000,
        "harvested_area": 250,
        "reported_yield_kg_ha": 4000,
        "reported_yield_t_ha": 4,
        "calculated_yield_t_ha": 4,
        "source": "ibge_pam",
    }

    _upsert_agriculture_fact(cursor, row)

    assert "fact_agriculture_production" in cursor.sql
    assert "reported_yield_t_ha" in cursor.sql
    assert "calculated_yield_t_ha" in cursor.sql
    assert 1000 in cursor.params
    assert 3000 in cursor.params


def test_load_weather_daily_uses_staging_and_set_based_merges():
    cursor = FakeCursor()
    frame = pd.DataFrame(
        [
            {
                "event_date": date(2026, 8, 15),
                "avg_temperature": 29.4,
                "max_temperature": 35.1,
                "min_temperature": 22.3,
                "total_precipitation": 4.2,
                "avg_humidity": 66.5,
                "avg_wind_speed": 12.1,
                "max_wind_speed": 28.4,
                "solar_radiation": 810.0,
                "evapotranspiration": 5.6,
                "days_without_rain": 3,
                "precipitation_accumulated_7d": 12.3,
                "precipitation_accumulated_30d": 92.4,
                "avg_temperature_7d": 28.7,
                "avg_temperature_30d": 27.9,
                "thermal_amplitude": 12.8,
                "drought_risk": "normal",
                "heat_risk": "high",
                "heavy_rain_risk": "normal",
                "city": "Sorriso",
                "state": "MT",
                "region": "Centro-Oeste",
                "latitude": -12.5,
                "longitude": -55.7,
                "source": "open_meteo",
            }
        ]
    )

    loaded = _load_weather_daily(cursor, frame)

    assert loaded == 1
    assert "CREATE TEMP TABLE staging_weather_daily" in cursor.statements[0]
    assert "INSERT INTO staging_weather_daily" in cursor.executemany_sql
    assert len(cursor.executemany_params) == 1
    assert any("INSERT INTO dim_date" in statement for statement in cursor.statements)
    assert any("INSERT INTO fact_weather_daily" in statement for statement in cursor.statements)
