# Exercises

Hands-on roadmap to reinforce Spark internals concepts. Each exercise is a spec, not a solution — the goal is to write the code yourself and validate your own results.

| # | Exercise | Concept |
|---|---|---|
| 1 | [repartition vs coalesce](01-repartition-vs-coalesce.md) | Partitioning, shuffle |
| 2 | [write/read strategy](02-write-read-strategy.md) | Output file size, read parallelism |
| 3 | [memory leaks](03-memory-leak.md) | Caching lifecycle, driver vs executor memory |

More exercises will be added here as the roadmap grows (joins & broadcast, caching/persistence, lazy evaluation, file formats, skew handling, ...).
