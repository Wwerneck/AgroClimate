import logging
import sys
from uuid import uuid4


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=("%(asctime)s level=%(levelname)s pipeline=%(name)s " "task=%(funcName)s message=%(message)s"),
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def new_execution_id() -> str:
    return str(uuid4())
