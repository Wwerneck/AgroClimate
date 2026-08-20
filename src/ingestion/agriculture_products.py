from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_PATH = PROJECT_ROOT / "src" / "config" / "agriculture_products.csv"


@dataclass(frozen=True)
class AgricultureProduct:
    source: str
    source_table: str
    product_code: str
    product_name: str
    crop_type: str


def load_agriculture_products(path: Path = PRODUCTS_PATH) -> list[AgricultureProduct]:
    with path.open(encoding="utf-8") as file:
        return [AgricultureProduct(**row) for row in csv.DictReader(file)]
