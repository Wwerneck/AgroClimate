-- Chuva acumulada por estado
SELECT l.state, SUM(f.total_precipitation) AS accumulated_precipitation_mm
FROM fact_weather_daily f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.state
ORDER BY accumulated_precipitation_mm DESC;

-- Temperatura media mensal
SELECT d.year, d.month, ROUND(AVG(f.avg_temperature), 2) AS monthly_avg_temperature
FROM fact_weather_daily f
JOIN dim_date d ON d.date_id = f.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- Ranking das cidades mais quentes
SELECT l.city, l.state, ROUND(AVG(f.max_temperature), 2) AS avg_max_temperature
FROM fact_weather_daily f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.city, l.state
ORDER BY avg_max_temperature DESC
LIMIT 10;

-- Ranking das cidades com maior precipitacao
SELECT l.city, l.state, SUM(f.total_precipitation) AS total_precipitation
FROM fact_weather_daily f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.city, l.state
ORDER BY total_precipitation DESC
LIMIT 10;

-- Numero de dias sem chuva
SELECT l.city, l.state, SUM(CASE WHEN f.total_precipitation < 1 THEN 1 ELSE 0 END) AS dry_days
FROM fact_weather_daily f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.city, l.state
ORDER BY dry_days DESC;

