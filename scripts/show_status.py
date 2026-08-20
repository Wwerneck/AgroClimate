from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import get_settings  # noqa: E402
from src.monitoring.pipeline_status import summarize_pipeline_status  # noqa: E402


def main() -> None:
    settings = get_settings()
    print(json.dumps(summarize_pipeline_status(settings.metadata_dir), indent=2))


if __name__ == "__main__":
    main()
