# Exercise 01 — repartition vs coalesce

## Objective

Understand, with real measurements (not just theory), the practical difference between `repartition()` and `coalesce()`:

- `repartition(n)` — always triggers a **full shuffle**, can increase or decrease the number of partitions, produces well-balanced partitions.
- `coalesce(n)` — by default **avoids a full shuffle** by merging partitions that already live close together, can only **decrease** the number of partitions, and can produce unbalanced ones.

You'll validate this by running the same job three ways (baseline / repartition / coalesce) and comparing the numbers, not just trusting the docs.

## Dataset

[NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) (Yellow Taxi), Parquet. Download enough monthly files to land around 1.5–2GB total and drop them in `data/` (already gitignored):

```
data/
├── yellow_tripdata_2023-01.parquet
├── yellow_tripdata_2023-02.parquet
├── ...
```

Having multiple files is intentional — it means Spark starts with one partition per file, giving you a real (not artificial) starting partition count to compare against.

## Script

Starter file: [`scripts/01_repartition_coalesce.py`](../scripts/01_repartition_coalesce.py) — it's a dummy: just reads the data and prints the partition count so you can confirm the setup works. Fill in the `TODO`s as you go through Parts A-E.

Run it (from `docker/` — the container mounts the repo root, so `scripts/` and `data/` are visible at `/app`):

```bash
docker compose up -d spark-master spark-worker
docker compose run --rm spark-submit spark-submit --master spark://spark-master:7077 /app/scripts/01_repartition_coalesce.py
```

## Setup

- Spark session with the UI enabled (`http://localhost:4040`) — you'll use it to read shuffle read/write bytes and stage durations.
- Read the whole `data/` folder as a single DataFrame: `spark.read.parquet("data/")`.
- Record the baseline: `df.rdd.getNumPartitions()`.

## Part A — Baseline (no repartition / no coalesce)

Run an aggregation that forces a shuffle regardless of what you do later, e.g. average fare and trip count grouped by pickup location and day. Write the result to `data/out/baseline/` as Parquet.

Record for this run:
- Partitions going in (`getNumPartitions()` after read)
- Number of output files (`ls data/out/baseline/ | grep parquet | wc -l`)
- Wall-clock duration
- Shuffle read/write bytes (Spark UI → Stages, for the shuffle stage of the groupBy)

## Part B — with `repartition(n)`

Same aggregation and write, but call `.repartition(n)` right after reading, before the `groupBy`. Try at least two values of `n`: one much larger than the baseline partition count, one much smaller.

For each `n`, record the same metrics as Part A, plus:
- `df.explain(True)` — confirm there's an `Exchange` node in the physical plan.

## Part C — with `coalesce(n)`

Same aggregation and write, but call `.coalesce(n)` instead of `.repartition(n)` at the same point (n must be ≤ the baseline partition count — coalesce can't increase partitions).

Record the same metrics, plus:
- `df.explain(True)` — confirm there's **no** `Exchange` node for the coalesce step.
- Try calling `.coalesce(n)` with `n` *larger* than the current partition count and confirm via `getNumPartitions()` that nothing changes (documented no-op).

## Part D — measuring skew

For both the `repartition` and `coalesce` runs, check how evenly rows are spread across partitions:

```python
from pyspark.sql.functions import spark_partition_id

df.withColumn("pid", spark_partition_id()) \
  .groupBy("pid") \
  .count() \
  .orderBy("pid") \
  .show(100)
```

Compare min/max/stddev of row counts per partition between the two.

## Part E — comparison table

Fill this in with your actual numbers:

| Scenario | Partitions in | Partitions out | Output files | Duration | Shuffle read/write | Partition skew (min/max rows) |
|---|---|---|---|---|---|---|
| Baseline | | | | | | |
| repartition(small n) | | | | | | |
| repartition(large n) | | | | | | |
| coalesce(n) | | | | | | |
| coalesce(n > current) | | | | | | |

## Questions to answer

1. Which scenarios showed an `Exchange` in the plan, and which didn't? Does that match the shuffle bytes you measured?
2. Which produced more balanced partitions — repartition or coalesce? Why?
3. Despite the skew risk, when would you still prefer `coalesce` over `repartition` (hint: think about cost of the operation itself, not just the output)?
4. How does the number of partitions at write time relate to the number of output files?
5. What actually happened when you called `coalesce(n)` with `n` larger than the current partition count?
