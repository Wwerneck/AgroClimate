from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.config.risk_thresholds import load_risk_thresholds


def transform_bronze_to_silver(df: DataFrame) -> DataFrame:
    """Clean, type and deduplicate raw weather records."""
    thresholds = load_risk_thresholds()
    record_id = F.sha2(
        F.concat_ws(
            "|",
            F.col("city"),
            F.col("timestamp"),
            F.col("latitude").cast("string"),
            F.col("longitude").cast("string"),
        ),
        256,
    )
    typed = (
        df.withColumn("weather_record_id", record_id)
        .withColumn("event_timestamp", F.to_timestamp("timestamp"))
        .withColumn("event_date", F.to_date("event_timestamp"))
        .withColumn("latitude", F.col("latitude").cast("double"))
        .withColumn("longitude", F.col("longitude").cast("double"))
        .withColumn("temperature_2m", F.col("temperature_2m").cast("double"))
        .withColumn("relative_humidity_2m", F.col("relative_humidity_2m").cast("double"))
        .withColumn("precipitation_mm", F.col("precipitation_mm").cast("double"))
        .withColumn("rain_mm", F.col("rain_mm").cast("double"))
        .withColumn("wind_speed_kmh", F.col("wind_speed_kmh").cast("double"))
        .withColumn("shortwave_radiation", F.col("shortwave_radiation").cast("double"))
        .withColumn("evapotranspiration", F.col("evapotranspiration").cast("double"))
        .withColumn("year", F.year("event_date"))
        .withColumn("month", F.month("event_date"))
    )
    valid = typed.filter(
        (F.col("event_timestamp").isNotNull())
        & (F.length(F.trim(F.col("city"))) > 0)
        & (F.col("latitude").between(-90, 90))
        & (F.col("longitude").between(-180, 180))
        & (
            F.col("relative_humidity_2m").isNull()
            | F.col("relative_humidity_2m").between(
                thresholds.quality.min_humidity_pct, thresholds.quality.max_humidity_pct
            )
        )
        & (F.col("precipitation_mm").isNull() | (F.col("precipitation_mm") >= thresholds.quality.min_precipitation_mm))
        & (F.col("wind_speed_kmh").isNull() | (F.col("wind_speed_kmh") >= thresholds.quality.min_wind_speed_kmh))
        & (
            F.col("temperature_2m").isNull()
            | F.col("temperature_2m").between(
                thresholds.quality.min_temperature_c, thresholds.quality.max_temperature_c
            )
        )
    )
    return valid.dropDuplicates(["weather_record_id"])


def run(bronze_path: Path, silver_path: Path, spark: SparkSession | None = None) -> None:
    active_spark = spark or SparkSession.builder.appName("agroclimate-bronze-to-silver").getOrCreate()
    active_spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    df = active_spark.read.parquet(str(bronze_path))
    silver = transform_bronze_to_silver(df)
    (
        silver.repartition("year", "month", "state")
        .write.mode("overwrite")
        .partitionBy("year", "month", "state")
        .parquet(str(silver_path / "weather"))
    )
