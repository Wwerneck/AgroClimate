INSERT INTO dim_source (source_name, source_type)
VALUES ('open_meteo', 'weather_api')
ON CONFLICT (source_name) DO NOTHING;

