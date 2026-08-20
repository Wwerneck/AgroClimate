from pathlib import Path


def test_weather_fact_schema_contains_dashboard_metrics():
    schema_sql = Path("sql/schema.sql").read_text(encoding="utf-8")
    migration_sql = Path("sql/migrations/001_add_gold_rolling_metrics.sql").read_text(encoding="utf-8")
    expected_columns = [
        "precipitation_accumulated_7d",
        "precipitation_accumulated_30d",
        "avg_temperature_7d",
        "avg_temperature_30d",
        "thermal_amplitude",
    ]

    for column in expected_columns:
        assert column in schema_sql
        assert column in migration_sql


def test_agriculture_schema_contains_crop_and_fact_tables():
    schema_sql = Path("sql/schema.sql").read_text(encoding="utf-8")
    migration_sql = Path("sql/migrations/002_add_agriculture_warehouse.sql").read_text(encoding="utf-8")

    for table in ["dim_crop", "fact_agriculture_production"]:
        assert table in schema_sql
        assert table in migration_sql
