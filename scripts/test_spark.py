"""
Smoke test run by the spark-submit service on `docker compose up`.
Confirms the cluster (master + worker + driver) is wired up correctly.
Also runnable directly with `python` (not just spark-submit) for debugging —
see SETUP.md, "Debugging with Attach to Running Container".
"""

import os

from pyspark.sql import SparkSession

MASTER_URL = os.environ.get("SPARK_MASTER_URL", "spark://spark-master:7077")

spark = SparkSession.builder.appName("smoke-test").master(MASTER_URL).getOrCreate()

df = spark.createDataFrame(
    [(1, "master"), (2, "worker"), (3, "driver")],
    ["id", "role"],
)
df.show()
print(f"Partitions: {df.rdd.getNumPartitions()}")
print(f"Executors available: {len(spark.sparkContext._jsc.sc().statusTracker().getExecutorInfos())}")

spark.stop()
