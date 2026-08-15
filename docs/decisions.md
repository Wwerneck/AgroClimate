# Architecture Decisions

## Parquet

Parquet is used for the data lake because it is columnar, compressed and well supported by Spark.

## Spark

Spark handles Bronze to Silver and Silver to Gold transformations with DataFrames, avoiding unnecessary `collect` or `toPandas` calls.

## PostgreSQL

PostgreSQL provides a familiar analytical warehouse for recruiters and local execution through Docker.

## Bronze, Silver and Gold

The medallion pattern separates raw ingestion, standardized records and aggregated analytical outputs.

## Idempotency

Weather records use a deterministic hash of city, timestamp, latitude and longitude. Warehouse loads use `INSERT ... ON CONFLICT`.

## Partitions and Small Files

Silver and Gold are partitioned by year, month and state. The code uses `repartition` and `coalesce` to reduce small file pressure while preserving useful partition pruning.

## Climate Risk Rules

Risk flags are exploratory rule-based indicators. They are not agronomic prescriptions and should be validated with domain experts before operational use.

