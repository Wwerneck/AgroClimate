CREATE TABLE IF NOT EXISTS dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    week INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_location (
    location_id BIGSERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    state CHAR(2) NOT NULL,
    region TEXT NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    UNIQUE (city, state)
);

CREATE TABLE IF NOT EXISTS dim_source (
    source_id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_crop (
    crop_id BIGSERIAL PRIMARY KEY,
    crop_code TEXT NOT NULL UNIQUE,
    crop_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_weather_daily (
    weather_fact_id BIGSERIAL PRIMARY KEY,
    date_id INTEGER NOT NULL REFERENCES dim_date(date_id),
    location_id BIGINT NOT NULL REFERENCES dim_location(location_id),
    source_id BIGINT NOT NULL REFERENCES dim_source(source_id),
    avg_temperature NUMERIC(6,2),
    max_temperature NUMERIC(6,2),
    min_temperature NUMERIC(6,2),
    total_precipitation NUMERIC(10,2),
    avg_humidity NUMERIC(6,2),
    avg_wind_speed NUMERIC(6,2),
    max_wind_speed NUMERIC(6,2),
    solar_radiation NUMERIC(12,2),
    evapotranspiration NUMERIC(10,2),
    days_without_rain INTEGER,
    precipitation_accumulated_7d NUMERIC(10,2),
    precipitation_accumulated_30d NUMERIC(10,2),
    avg_temperature_7d NUMERIC(6,2),
    avg_temperature_30d NUMERIC(6,2),
    thermal_amplitude NUMERIC(6,2),
    drought_risk TEXT,
    heat_risk TEXT,
    heavy_rain_risk TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (date_id, location_id, source_id)
);

CREATE TABLE IF NOT EXISTS fact_agriculture_production (
    agriculture_fact_id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    state_code TEXT NOT NULL,
    state_name TEXT NOT NULL,
    crop_id BIGINT NOT NULL REFERENCES dim_crop(crop_id),
    source_id BIGINT NOT NULL REFERENCES dim_source(source_id),
    produced_quantity NUMERIC(18,2),
    production_value NUMERIC(18,2),
    harvested_area NUMERIC(18,2),
    reported_yield_kg_ha NUMERIC(18,2),
    reported_yield_t_ha NUMERIC(18,4),
    calculated_yield_t_ha NUMERIC(18,4),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (year, state_code, crop_id, source_id)
);

CREATE TABLE IF NOT EXISTS etl_pipeline_runs (
    pipeline_execution_id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    duration_seconds NUMERIC(12,2),
    records_extracted INTEGER DEFAULT 0,
    records_silver INTEGER DEFAULT 0,
    records_gold INTEGER DEFAULT 0,
    records_rejected INTEGER DEFAULT 0,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_metadata (
    pipeline_name TEXT NOT NULL,
    source TEXT NOT NULL,
    last_successful_execution TIMESTAMPTZ,
    last_ingested_date DATE,
    records_processed INTEGER,
    status TEXT,
    execution_time NUMERIC(12,2),
    PRIMARY KEY (pipeline_name, source)
);
