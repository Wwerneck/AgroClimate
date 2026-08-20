from __future__ import annotations

from pathlib import Path

import pandas as pd

AGRICULTURE_METRICS = {
    "214": "produced_quantity",
    "215": "production_value",
    "216": "harvested_area",
    "112": "reported_yield_kg_ha",
}


def transform_agriculture_silver_to_gold(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    filtered = frame[frame["metric_code"].astype(str).isin(AGRICULTURE_METRICS)].copy()
    filtered["metric_slug"] = filtered["metric_code"].astype(str).map(AGRICULTURE_METRICS)
    index_columns = ["year", "territory_code", "territory_name", "product_code", "product_name"]
    gold = (
        filtered.pivot_table(index=index_columns, columns="metric_slug", values="value", aggfunc="sum")
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for column in AGRICULTURE_METRICS.values():
        if column not in gold:
            gold[column] = pd.NA
    gold["calculated_yield_t_ha"] = gold["produced_quantity"] / gold["harvested_area"]
    gold["reported_yield_t_ha"] = gold["reported_yield_kg_ha"] / 1000
    gold["source"] = "ibge_pam"
    return gold


def agriculture_silver_to_gold_local(silver_path: Path, gold_path: Path) -> int:
    frame = pd.read_parquet(silver_path / "agriculture")
    gold = transform_agriculture_silver_to_gold(frame)
    target = gold_path / "agriculture_summary"
    target.mkdir(parents=True, exist_ok=True)
    gold.to_parquet(target / "gold_agriculture_summary.parquet", index=False)
    return len(gold)
