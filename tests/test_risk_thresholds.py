from src.config.risk_thresholds import load_risk_thresholds


def test_load_risk_thresholds_reads_config_file(tmp_path):
    config = tmp_path / "risk_thresholds.yml"
    config.write_text(
        "\n".join(
            [
                "drought:",
                "  precipitation_7d_max_mm: 10",
                "  consecutive_dry_days_min: 3",
                "  avg_temperature_7d_min_c: 28",
                "heat:",
                "  max_temperature_c: 37",
                "heavy_rain:",
                "  daily_precipitation_mm: 80",
                "quality:",
                "  min_temperature_c: -10",
                "  max_temperature_c: 55",
            ]
        ),
        encoding="utf-8",
    )

    thresholds = load_risk_thresholds(config)

    assert thresholds.drought.precipitation_7d_max_mm == 10
    assert thresholds.drought.consecutive_dry_days_min == 3
    assert thresholds.heat.max_temperature_c == 37
    assert thresholds.heavy_rain.daily_precipitation_mm == 80
    assert thresholds.quality.min_temperature_c == -10
    assert thresholds.quality.max_temperature_c == 55
