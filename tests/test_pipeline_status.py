import json

from src.monitoring.pipeline_status import summarize_pipeline_status


def test_summarize_pipeline_status_reads_metadata_and_recent_runs(tmp_path):
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    (metadata_dir / "weather_ingestion_open_meteo.json").write_text(
        json.dumps({"pipeline_name": "weather_ingestion", "status": "success"}),
        encoding="utf-8",
    )
    (metadata_dir / "etl_pipeline_runs.jsonl").write_text(
        "\n".join(json.dumps({"pipeline_execution_id": str(index)}) for index in range(6)),
        encoding="utf-8",
    )

    summary = summarize_pipeline_status(metadata_dir)

    assert summary["pipeline_count"] == 1
    assert summary["recent_run_count"] == 5
    assert summary["recent_runs"][0]["pipeline_execution_id"] == "1"
