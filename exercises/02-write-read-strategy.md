# Exercise 02 — write/read strategy: finding the ideal file size

## Objective

Find, with measurements, the "ideal" output file size for this dataset, and quantify how much read/write performance actually changes between a bad partitioning strategy and a good one. Builds directly on [exercise 01](01-repartition-vs-coalesce.md) — here the partition count is not the end goal, output file size is.

The trade-off you're measuring:

- **Too many small files** — write is fast per-task, but read-back pays per-file overhead (task scheduling, file open/close, metadata listing) that dominates over actual I/O.
- **Too few huge files** — fewer tasks than available cores, so read-back can't parallelize; a handful of executors carry the whole scan while the rest sit idle.
- Somewhere in between is a file size where per-file overhead is negligible **and** parallelism is good. That's what you're looking for.

## Dataset

Same as exercise 01: NYC TLC Yellow Taxi Parquet files in `data/`.

## Setup

- Note the total on-disk size of your input: `du -sh data/*.parquet` (sum it up).
- Spark UI at `http://localhost:4040` for task counts and stage durations.
- Use a fresh `SparkSession` (or at least clear caches) between scenarios so read timings aren't skewed by cached data.

## Part A — too many small files

Write the dataset with a high partition count, e.g. `df.repartition(200).write.parquet("data/out/many_small/")`.

Record:
- Number of output files
- Avg / min / max file size (`ls -la data/out/many_small/*.parquet`)
- Write duration

## Part B — too few huge files

Write with a very low partition count, e.g. `df.coalesce(2).write.parquet("data/out/few_huge/")`.

Record the same metrics.

## Part C — the "ideal" size

Pick a target file size — **128MB** is the common rule of thumb for Parquet with Spark (matches the default HDFS/object-store block size Spark plans splits around). Compute the partition count:

```
n = total_input_size_bytes / target_file_size_bytes   # e.g. 128 * 1024 * 1024
```

Write with `df.repartition(n).write.parquet("data/out/target_size/")` and record the same metrics. Check how close the actual avg file size landed to 128MB.

## Part D — write-time knob instead of repartition

Instead of controlling file count via `repartition`, let Spark control file *size* directly at write time:

```python
df.write.option("maxRecordsPerFile", N).parquet("data/out/max_records/")
```

Pick `N` so the resulting file sizes land near your 128MB target (estimate from avg row size in Part A). Record the same metrics, and compare: does this produce more consistent file sizes than repartitioning by count did?

## Part E — read-back benchmark

For **each** of the four datasets written above (`many_small`, `few_huge`, `target_size`, `max_records`), in a fresh session:

1. Full scan + count: `spark.read.parquet(path).count()` — record duration and number of tasks (Spark UI).
2. Filtered query representative of real use, e.g. filter by a date range + aggregate — record duration and number of tasks.

## Part F — comparison table

| Scenario | Files | Avg file size | Write duration | Read (count) duration | Read (filtered) duration | Tasks launched |
|---|---|---|---|---|---|---|
| many_small | | | | | | |
| few_huge | | | | | | |
| target_size | | | | | | |
| max_records | | | | | | |

## Questions to answer

1. How much slower (in %) was `many_small` vs `target_size` on read-back? Was the gap bigger for the full scan or the filtered query, and why?
2. How much slower was `few_huge` vs `target_size`? Look at the task count in the Spark UI — how many cores were actually busy during that stage?
3. Did `maxRecordsPerFile` produce more uniform file sizes than repartitioning by a fixed count? Why might that be, given the data isn't uniformly distributed across partitions to begin with?
4. Based on your numbers, what's the actual "cliff" — is there a file size below which read performance clearly degrades, or does it degrade gradually?
5. Would the ideal file size change for a dataset 10x bigger, or 10x smaller? What does that tell you about using a fixed number of partitions vs a target byte size as your write strategy?
