from src.ingestion.sidra_normalization import normalize_sidra_pam_rows


def test_normalize_sidra_pam_rows_maps_ibge_fields():
    rows = [
        {
            "D1C": "51",
            "D1N": "Mato Grosso",
            "D2C": "214",
            "D2N": "Quantidade produzida",
            "D3C": "2713",
            "D3N": "Soja",
            "D4C": "2023",
            "D4N": "2023",
            "V": "456.7",
            "MN": "Toneladas",
        }
    ]

    records = normalize_sidra_pam_rows(rows)

    assert records == [
        {
            "year": "2023",
            "territory_code": "51",
            "territory_name": "Mato Grosso",
            "metric_code": "214",
            "metric_name": "Quantidade produzida",
            "product_code": "2713",
            "product_name": "Soja",
            "value": 456.7,
            "unit": "Toneladas",
            "source": "ibge_pam",
        }
    ]
