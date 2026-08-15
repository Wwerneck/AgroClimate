# Architecture

AgroClimate uses a layered data architecture:

1. Open-Meteo API is ingested with a Python client.
2. Raw-like weather records are written to the Bronze data lake.
3. PySpark standardizes and validates data into Silver.
4. PySpark aggregates daily analytical metrics into Gold.
5. PostgreSQL stores a dimensional star schema for analytics and dashboards.
6. Airflow orchestrates the pipeline.

Bronze is partitioned by event ingestion date. Silver and Gold are partitioned by year, month and state to support common analytical filters without generating one partition per city or hour.

