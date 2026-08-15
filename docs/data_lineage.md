# Data Lineage

```text
Open-Meteo API
  -> raw hourly weather payload
  -> data/bronze/weather
  -> data/silver/weather
  -> data/gold/weather_daily
  -> dim_date, dim_location, dim_source, fact_weather_daily
```

The record grain changes from hourly observations in Bronze/Silver to daily city-level aggregates in Gold and the warehouse fact table.

