"""
Exercise 01 - repartition vs coalesce
Dummy entry point, just enough to confirm the setup works.
Fill in each TODO as you work through exercises/01-repartition-vs-coalesce.md.
"""

import os

from pyspark.sql import SparkSession

DATA_PATH = "/app/data"
MASTER_URL = os.environ.get("SPARK_MASTER_URL", "spark://spark-master:7077")


def main():
    spark = SparkSession.builder.appName("exercise-01-repartition-coalesce").master(MASTER_URL).getOrCreate()

    df = spark.read.parquet(DATA_PATH)
    print(f"Partitions after read: {df.rdd.getNumPartitions()}")
    print(f"Row count: {df.count()}")

    # TODO Part A - baseline: groupBy + write, no repartition/coalesce
    # TODO Part B - same, with .repartition(n) before the groupBy
    # TODO Part C - same, with .coalesce(n) before the groupBy
    # TODO Part D - spark_partition_id() skew check
    # TODO Part E - fill in the comparison table in the exercise doc

    spark.stop()


if __name__ == "__main__":
    main()
