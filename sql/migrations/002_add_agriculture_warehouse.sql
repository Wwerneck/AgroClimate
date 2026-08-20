CREATE TABLE IF NOT EXISTS dim_crop (
    crop_id BIGSERIAL PRIMARY KEY,
    crop_code TEXT NOT NULL UNIQUE,
    crop_name TEXT NOT NULL
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

CREATE INDEX IF NOT EXISTS idx_fact_agriculture_year_state ON fact_agriculture_production(year, state_code);
CREATE INDEX IF NOT EXISTS idx_fact_agriculture_crop ON fact_agriculture_production(crop_id);
