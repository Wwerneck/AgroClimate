from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.processing.parquet_io import read_parquet_files

AGRICULTURE_METRIC_CODES = ["112", "214", "215", "216"]


def transform_agriculture_bronze_to_silver(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    if "source" in frame.columns and "data_source" not in frame.columns:
        frame = frame.assign(data_source=frame["source"])
    silver = frame[
        [
            "year",
            "territory_code",
            "territory_name",
            "metric_code",
            "metric_name",
            "product_code",
            "product_name",
            "value",
            "unit",
            "data_source",
            "ingestion_timestamp",
            "pipeline_execution_id",
        ]
    ].copy()
    silver["year"] = pd.to_numeric(silver["year"], errors="coerce").astype("Int64")
    silver["value"] = pd.to_numeric(silver["value"], errors="coerce")
    text_columns = [
        "territory_code",
        "territory_name",
        "metric_code",
        "metric_name",
        "product_code",
        "product_name",
        "unit",
        "data_source",
    ]
    for column in text_columns:
        silver[column] = silver[column].astype("string").str.strip()
    silver = silver.dropna(subset=["year", "territory_code", "metric_code", "product_code"])
    silver = silver[
        silver["year"].between(1974, 2100)
        & silver["metric_code"].isin(AGRICULTURE_METRIC_CODES)
        & silver["product_name"].ne("")
    ]
    return silver.drop_duplicates(subset=["year", "territory_code", "metric_code", "product_code"], keep="last")


def agriculture_bronze_to_silver_local(bronze_path: Path, silver_path: Path) -> int:
    frame = read_parquet_files(bronze_path)
    silver = transform_agriculture_bronze_to_silver(frame)
    target = silver_path / "agriculture"
    target.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(target / "silver_agriculture.parquet", index=False)
    return len(silver)
