from src.processing.ids import weather_record_id


def test_weather_record_id_is_deterministic():
    first = weather_record_id("Sorriso", "2026-08-15", -12.5, -55.7)
    second = weather_record_id("Sorriso", "2026-08-15", -12.5, -55.7)

    assert first == second
    assert len(first) == 64
