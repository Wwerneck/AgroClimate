import pandas as pd

from src.processing.agriculture_bronze_to_silver import agriculture_bronze_to_silver_local
from src.processing.agriculture_silver_to_gold import agriculture_silver_to_gold_local


def test_agriculture_local_processing_builds_gold_summary(tmp_path):
    bronze_path = tmp_path / "bronze" / "agriculture"
    silver_path = tmp_path / "silver"
    gold_path = tmp_path / "gold"
    bronze_path.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "year": "2024",
                "territory_code": "51",
                "territory_name": "Mato Grosso",
                "metric_code": "214",
                "metric_name": "Quantidade produzida",
                "product_code": "2713",
                "product_name": "Soja",
                "value": 1000,
                "unit": "Toneladas",
                "data_source": "ibge_pam",
                "ingestion_timestamp": "2026-08-20T00:00:00",
                "pipeline_execution_id": "exec",
            },
            {
                "year": "2024",
                "territory_code": "51",
                "territory_name": "Mato Grosso",
                "metric_code": "215",
                "metric_name": "Valor da producao",
                "product_code": "2713",
                "product_name": "Soja",
                "value": 3000,
                "unit": "Mil Reais",
                "data_source": "ibge_pam",
                "ingestion_timestamp": "2026-08-20T00:00:00",
                "pipeline_execution_id": "exec",
            },
            {
                "year": "2024",
                "territory_code": "51",
                "territory_name": "Mato Grosso",
                "metric_code": "216",
                "metric_name": "Area colhida",
                "product_code": "2713",
                "product_name": "Soja",
                "value": 250,
                "unit": "Hectares",
                "data_source": "ibge_pam",
                "ingestion_timestamp": "2026-08-20T00:00:00",
                "pipeline_execution_id": "exec",
            },
            {
                "year": "2024",
                "territory_code": "51",
                "territory_name": "Mato Grosso",
                "metric_code": "112",
                "metric_name": "Rendimento medio",
                "product_code": "2713",
                "product_name": "Soja",
                "value": 4000,
                "unit": "Quilogramas por Hectare",
                "data_source": "ibge_pam",
                "ingestion_timestamp": "2026-08-20T00:00:00",
                "pipeline_execution_id": "exec",
            },
        ]
    ).to_parquet(bronze_path / "part.parquet", index=False)

    assert agriculture_bronze_to_silver_local(bronze_path, silver_path) == 4
    assert agriculture_silver_to_gold_local(silver_path, gold_path) == 1

    gold = pd.read_parquet(gold_path / "agriculture_summary")
    assert gold.loc[0, "produced_quantity"] == 1000
    assert gold.loc[0, "harvested_area"] == 250
    assert gold.loc[0, "production_value"] == 3000
    assert gold.loc[0, "reported_yield_t_ha"] == 4
    assert gold.loc[0, "calculated_yield_t_ha"] == 4
