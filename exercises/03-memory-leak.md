# Exercise 03 — memory leaks: understanding and avoiding them

## Objective

Reproduce, on purpose, the two most common ways a Spark application leaks memory — and fix each one. "Leak" here doesn't mean a JVM bug, it means memory that keeps growing across iterations because *something* (Spark itself, or your own driver code) is holding a reference you assumed would be released.

## Background — the gotcha worth internalizing

If you call `.cache()` on a DataFrame inside a loop and never call `.unpersist()`, the cached data is **not** freed just because your Python variable goes out of scope or gets overwritten next iteration. Spark's `SparkContext` keeps its own registry of persisted RDDs, independent of whatever Python references you hold. It only lets go when you explicitly `.unpersist()` it, or the context stops, or memory pressure forces an LRU eviction. This exercise makes that visible instead of theoretical.

## Dataset

Reuse the NYC TLC Yellow Taxi Parquet files from `data/` (exercises 01/02).

## Setup

To make leaks reproducible in minutes instead of requiring huge data, temporarily cap memory in `docker-compose.yml` for this exercise:

```yaml
spark-submit:
  command: >
    spark-submit --master spark://spark-master:7077
    --driver-memory 1g
    --executor-memory 1g
    /app/your_script.py
```

You'll monitor two things while each scenario runs:
- **Spark UI** — Storage tab (`:4040`, cached blocks and their total size) and Executors tab (Storage Memory column).
- **Container memory** — `docker stats spark-submit spark-worker --no-stream`, sampled at regular checkpoints.

## Part A — baseline (no leak)

Loop 20 times. Each iteration: read the data, apply a transformation (e.g. filter by a different date range each time), force execution with `.count()`, and **don't** keep any reference or cache anything.

Record container memory (both `spark-submit` and `spark-worker`) at iterations 0, 5, 10, 15, 20. It should stay roughly flat.

## Part B — executor-side leak (caching without unpersisting)

Loop 20 times. Each iteration: derive a new DataFrame from the source with some transform, `.cache()` it, and force materialization with `.count()`. Do **not** call `.unpersist()` on it or on any previous iteration's cached DataFrame.

Record:
- Spark UI Storage tab: number of cached entries and total size, at the same checkpoints as Part A.
- Container memory at the same checkpoints.
- What happens around the point where cached data approaches the `--executor-memory` cap you set — does it error out, evict, or spill?

## Part C — driver-side leak (accumulating collected results)

Loop 20 times. Each iteration: run an aggregation that returns a non-trivial result set, `.collect()` it (or `.toPandas()`), and **append** the result to a Python list defined outside the loop instead of processing and discarding it.

Record `spark-submit` container memory at the same checkpoints. This one grows even though nothing was cached in Spark — the growth is plain Python-side, on the driver process.

## Part D — fix both

Rewrite Part B and Part C so memory stays flat:

- **Executor-side fix**: call `.unpersist()` on each cached DataFrame before the next iteration creates a new one (or drop down to caching only what you still need, and clear it explicitly with `spark.catalog.clearCache()` if scope makes per-object cleanup awkward).
- **Driver-side fix**: don't accumulate full results on the driver — either aggregate to a small summary before collecting, or write each iteration's output to disk (`.write.parquet(...)`) instead of holding it in a growing Python list.

Re-run both fixed versions and record the same checkpoints.

## Part E — comparison table

| Scenario | Mem @0 | Mem @5 | Mem @10 | Mem @15 | Mem @20 | Flat or growing? |
|---|---|---|---|---|---|---|
| A — baseline | | | | | | |
| B — cache leak | | | | | | |
| C — driver collect leak | | | | | | |
| D1 — cache fixed | | | | | | |
| D2 — driver fixed | | | | | | |

## Bonus — lineage growth (a different kind of "leak")

Iterative code that repeatedly transforms a DataFrame in a loop *without* caching or collecting can still blow up the driver — not through data volume, but because the logical plan (lineage) keeps growing each iteration, making query planning increasingly expensive until you hit a `StackOverflowError` or very slow `.explain()`/optimizer time. Reproduce it with ~50-100 chained iterations of `df = df.withColumn(...)` on the same `df`, then fix it with periodic `df.checkpoint()` (needs `spark.sparkContext.setCheckpointDir(...)`) and compare planning time before/after.

## Questions to answer

1. In Part B, did the Spark UI Storage tab show growth even in iterations where you never touched the Python variable from a prior iteration? What does that tell you about what actually owns a cached DataFrame's lifetime?
2. What was the actual failure mode when cached data exceeded `--executor-memory` — error, silent eviction, or disk spill? Why does that matter for correctness vs just performance?
3. Why did the Part C leak show up on `spark-submit`'s container memory and not on `spark-worker`'s?
4. After the fixes in Part D, which one was simpler to get right — remembering to `.unpersist()` at the right point, or restructuring the code to never accumulate on the driver in the first place? Which approach would you trust more in a larger, less controlled codebase?
5. What's the practical difference between the caching leak (Part B) and the lineage growth issue (Bonus) — same symptom (driver/executor gets slower or dies over time), different root cause?
