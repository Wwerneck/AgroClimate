CREATE INDEX IF NOT EXISTS idx_fact_weather_daily_date ON fact_weather_daily(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_weather_daily_location ON fact_weather_daily(location_id);
CREATE INDEX IF NOT EXISTS idx_dim_location_state ON dim_location(state);
CREATE INDEX IF NOT EXISTS idx_dim_date_year_month ON dim_date(year, month);
CREATE INDEX IF NOT EXISTS idx_fact_agriculture_year_state ON fact_agriculture_production(year, state_code);
CREATE INDEX IF NOT EXISTS idx_fact_agriculture_crop ON fact_agriculture_production(crop_id);
