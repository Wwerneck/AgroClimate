from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_pipeline_status(metadata_dir: Path) -> dict[str, Any]:
    metadata_files = sorted(path for path in metadata_dir.glob("*.json") if path.name != "etl_pipeline_runs.json")
    pipelines = []
    for path in metadata_files:
        pipelines.append(json.loads(path.read_text(encoding="utf-8")))

    runs_path = metadata_dir / "etl_pipeline_runs.jsonl"
    recent_runs = []
    if runs_path.exists():
        lines = runs_path.read_text(encoding="utf-8").splitlines()
        recent_runs = [json.loads(line) for line in lines[-5:] if line.strip()]

    return {
        "pipelines": pipelines,
        "recent_runs": recent_runs,
        "pipeline_count": len(pipelines),
        "recent_run_count": len(recent_runs),
    }
