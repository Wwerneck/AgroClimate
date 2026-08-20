from __future__ import annotations

from typing import Any

SOURCE = "ibge_pam"


def normalize_sidra_pam_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        records.append(
            {
                "territory_code": row.get("D1C"),
                "territory_name": row.get("D1N"),
                "metric_code": row.get("D2C"),
                "metric_name": row.get("D2N"),
                "product_code": row.get("D3C"),
                "product_name": row.get("D3N"),
                "year": row.get("D4C"),
                "value": _parse_number(row.get("V")),
                "unit": row.get("MN"),
                "source": SOURCE,
            }
        )
    return records


def _parse_number(value: Any) -> float | None:
    if value in (None, "-", "..."):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None
