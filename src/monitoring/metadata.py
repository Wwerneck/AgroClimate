from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


@dataclass
class PipelineMetadata:
    pipeline_name: str
    source: str
    last_successful_execution: str | None = None
    last_ingested_date: str | None = None
    records_processed: int = 0
    status: str = "never_run"
    execution_time: float = 0.0


class MetadataStore:
    def __init__(self, metadata_dir: Path):
        self.metadata_dir = metadata_dir
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, pipeline_name: str, source: str) -> Path:
        return self.metadata_dir / f"{pipeline_name}_{source}.json"

    def load(self, pipeline_name: str, source: str) -> PipelineMetadata:
        path = self._path(pipeline_name, source)
        if not path.exists():
            return PipelineMetadata(pipeline_name=pipeline_name, source=source)
        return PipelineMetadata(**json.loads(path.read_text(encoding="utf-8")))

    def save(self, metadata: PipelineMetadata) -> None:
        path = self._path(metadata.pipeline_name, metadata.source)
        path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")

    def record_success(
        self,
        pipeline_name: str,
        source: str,
        last_ingested_date: date,
        records_processed: int,
        execution_time: float,
    ) -> None:
        self.save(
            PipelineMetadata(
                pipeline_name=pipeline_name,
                source=source,
                last_successful_execution=datetime.utcnow().isoformat(),
                last_ingested_date=last_ingested_date.isoformat(),
                records_processed=records_processed,
                status="success",
                execution_time=execution_time,
            )
        )

    def append_run(self, execution_id: str, payload: dict[str, Any]) -> None:
        path = self.metadata_dir / "etl_pipeline_runs.jsonl"
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps({"pipeline_execution_id": execution_id, **payload}) + "\n")

    def append_dataset_metric(
        self,
        execution_id: str,
        dataset: str,
        layer: str,
        records: int,
        status: str = "success",
        extra: dict[str, Any] | None = None,
    ) -> None:
        path = self.metadata_dir / "etl_dataset_metrics.jsonl"
        payload = {
            "pipeline_execution_id": execution_id,
            "dataset": dataset,
            "layer": layer,
            "records": records,
            "status": status,
            "measured_at": datetime.utcnow().isoformat(),
            **(extra or {}),
        }
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, default=str) + "\n")
