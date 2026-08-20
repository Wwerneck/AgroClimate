from __future__ import annotations

from datetime import datetime
from time import perf_counter

from src.config.settings import Settings
from src.ingestion.agriculture_products import load_agriculture_products
from src.ingestion.ibge_sidra_client import SidraClient
from src.ingestion.sidra_normalization import normalize_sidra_pam_rows
from src.monitoring.metadata import MetadataStore
from src.storage.local_lake import LocalDataLake

PIPELINE_NAME = "agriculture_ingestion"
SOURCE = "ibge_pam"


def run_agriculture_ingestion(settings: Settings, execution_id: str) -> dict[str, object]:
    started = perf_counter()
    products = [product.product_code for product in load_agriculture_products() if product.source == SOURCE]
    client = SidraClient(settings.api_timeout)
    records = normalize_sidra_pam_rows(client.fetch_pam_temporary_crops(products))
    lake = LocalDataLake(settings.data_dir)
    output_path = lake.write_bronze_agriculture(records, datetime.utcnow().date(), execution_id)
    elapsed = perf_counter() - started
    MetadataStore(settings.metadata_dir).record_success(
        PIPELINE_NAME,
        SOURCE,
        datetime.utcnow().date(),
        len(records),
        elapsed,
    )
    return {"records_extracted": len(records), "output_path": str(output_path)}
