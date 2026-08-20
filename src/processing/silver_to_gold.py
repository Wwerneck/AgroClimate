from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from src.config.risk_thresholds import load_risk_thresholds


def transform_silver_to_gold(df: DataFrame) -> DataFrame:
    """Aggregate hourly silver weather into daily analytical records."""
    thresholds = load_risk_thresholds()
    daily = df.groupBy("event_date", "city", "state", "region", "latitude", "longitude", "source").agg(
        F.avg("temperature_2m").alias("avg_temperature"),
        F.max("temperature_2m").alias("max_temperature"),
        F.min("temperature_2m").alias("min_temperature"),
        F.sum("precipitation_mm").alias("total_precipitation"),
        F.avg("relative_humidity_2m").alias("avg_humidity"),
        F.avg("wind_speed_kmh").alias("avg_wind_speed"),
        F.max("wind_speed_kmh").alias("max_wind_speed"),
        F.sum("shortwave_radiation").alias("solar_radiation"),
        F.sum("evapotranspiration").alias("evapotranspiration"),
    )
    city_window = Window.partitionBy("city", "state").orderBy("event_date").rowsBetween(-6, 0)
    city_window_30 = Window.partitionBy("city", "state").orderBy("event_date").rowsBetween(-29, 0)
    enriched = (
        daily.withColumn(
            "is_dry_day",
            F.when(F.coalesce(F.col("total_precipitation"), F.lit(0)) < 1, 1).otherwise(0),
        )
        .withColumn("days_without_rain", F.sum("is_dry_day").over(city_window))
        .withColumn("precipitation_accumulated_7d", F.sum("total_precipitation").over(city_window))
        .withColumn("precipitation_accumulated_30d", F.sum("total_precipitation").over(city_window_30))
        .withColumn("avg_temperature_7d", F.avg("avg_temperature").over(city_window))
        .withColumn("avg_temperature_30d", F.avg("avg_temperature").over(city_window_30))
        .withColumn("thermal_amplitude", F.col("max_temperature") - F.col("min_temperature"))
        .withColumn(
            "drought_risk",
            F.when(
                (F.col("precipitation_accumulated_7d") <= thresholds.drought.precipitation_7d_max_mm)
                & (F.col("days_without_rain") >= thresholds.drought.consecutive_dry_days_min)
                & (F.col("avg_temperature_7d") >= thresholds.drought.avg_temperature_7d_min_c),
                "high",
            ).otherwise("normal"),
        )
        .withColumn(
            "heat_risk",
            F.when(F.col("max_temperature") >= thresholds.heat.max_temperature_c, "high").otherwise("normal"),
        )
        .withColumn(
            "heavy_rain_risk",
            F.when(F.col("total_precipitation") >= thresholds.heavy_rain.daily_precipitation_mm, "high").otherwise(
                "normal"
            ),
        )
        .withColumn("year", F.year("event_date"))
        .withColumn("month", F.month("event_date"))
    )
    return enriched


def run(silver_path: Path, gold_path: Path, spark: SparkSession | None = None) -> None:
    active_spark = spark or SparkSession.builder.appName("agroclimate-silver-to-gold").getOrCreate()
    active_spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    df = active_spark.read.parquet(str(silver_path / "weather"))
    gold = transform_silver_to_gold(df)
    (
        gold.coalesce(4)
        .write.mode("overwrite")
        .partitionBy("year", "month", "state")
        .parquet(str(gold_path / "weather_daily"))
    )
