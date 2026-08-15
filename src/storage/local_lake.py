from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


class LocalDataLake:
    """Filesystem data lake writer with Parquet and JSON fallback for portability."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def write_bronze_weather(
        self,
        records: list[dict[str, Any]],
        partition_date: date,
        execution_id: str,
    ) -> Path:
        target = (
            self.base_dir
            / "bronze"
            / "weather"
            / f"year={partition_date.year:04d}"
            / f"month={partition_date.month:02d}"
            / f"day={partition_date.day:02d}"
        )
        target.mkdir(parents=True, exist_ok=True)
        enriched = [
            {
                **record,
                "ingestion_timestamp": datetime.utcnow().isoformat(),
                "source": "open_meteo",
                "pipeline_execution_id": execution_id,
            }
            for record in records
        ]
        path = target / f"weather_{execution_id}.parquet"
        try:
            pd.DataFrame(enriched).to_parquet(path, index=False)
        except Exception:
            path = path.with_suffix(".jsonl")
            with path.open("w", encoding="utf-8") as file:
                for record in enriched:
                    file.write(json.dumps(record) + "\n")
        return path

    def write_quarantine(self, records: list[dict[str, Any]], execution_id: str) -> Path | None:
        if not records:
            return None
        target = self.base_dir / "quarantine" / "weather"
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"rejected_{execution_id}.jsonl"
        with path.open("w", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record, default=str) + "\n")
        return path
