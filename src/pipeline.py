from __future__ import annotations

from src.config.settings import get_settings
from src.ingestion.weather_ingestion import run_weather_ingestion
from src.utils.logging import configure_logging, new_execution_id


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    execution_id = new_execution_id()
    run_weather_ingestion(settings, execution_id)


if __name__ == "__main__":
    main()
