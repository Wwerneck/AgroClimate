ALTER TABLE fact_weather_daily
    ADD COLUMN IF NOT EXISTS precipitation_accumulated_7d NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS precipitation_accumulated_30d NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS avg_temperature_7d NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS avg_temperature_30d NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS thermal_amplitude NUMERIC(6,2);
