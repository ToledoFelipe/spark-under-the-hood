"""
Exercise 01 - repartition vs coalesce

Usage (see exercises/01-repartition-vs-coalesce.md):
    python scripts/01_repartition_coalesce.py --scenario baseline
    python scripts/01_repartition_coalesce.py --scenario repartition --partitions 8
    python scripts/01_repartition_coalesce.py --scenario coalesce --partitions 4

Each invocation is its own process/SparkSession — that's deliberate, so scenarios
don't share driver-side state (see the isolation discussion in the exercise doc).
Results (duration, output file count/sizes) print at the end of each run; copy them
into the comparison table in the exercise doc by hand.
"""

import argparse
import os
import time

from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, lit, spark_partition_id, to_date


def partition_report(df, name):
    print(f"\n--- {name}: {df.rdd.getNumPartitions()} partitions ---")
    df.withColumn("pid", spark_partition_id()) \
      .groupBy("pid") \
      .count() \
      .orderBy("pid") \
      .show(20)


DATA_PATH1 = "/app/data/yellow_tripdata_*.parquet"
DATA_PATH2 = "/app/data/green_tripdata_*.parquet"
OUT_DIR = "/app/data/out"
MASTER_URL = os.environ.get("SPARK_MASTER_URL", "spark://spark-master:7077")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["baseline", "repartition", "coalesce"], default="baseline")
    parser.add_argument("--partitions", type=int, default=8, help="n for repartition/coalesce (ignored for baseline)")
    return parser.parse_args()


def report_output_files(path):
    files = [f for f in os.listdir(path) if f.endswith(".parquet")]
    sizes = [os.path.getsize(os.path.join(path, f)) for f in files]
    total_mb = sum(sizes) / 1024 / 1024
    avg_mb = total_mb / len(sizes) if sizes else 0
    print(f"Output files: {len(files)}, total {total_mb:.1f}MB, avg {avg_mb:.1f}MB/file")


def main():
    args = parse_args()
    spark = SparkSession.builder.appName(f"exercise-01-{args.scenario}").master(MASTER_URL).getOrCreate()

    spark.conf.set("spark.sql.adaptive.enabled", "false")
    
    df1 = (
        spark.read.parquet(DATA_PATH1)
            .withColumn("source_file", lit("yellow_tripdata_2026-01.parquet"))
            .withColumnRenamed("tpep_pickup_datetime", "pep_pickup_datetime")
            .withColumnRenamed("tpep_dropoff_datetime", "pep_dropoff_datetime")
            .drop("Airport_fee")
        )

    print(f"Partitions after read: {df1.rdd.getNumPartitions()}")
    print(f"Row count: {df1.count()}")
    # print(df1.columns)
    # df.show()

# ['VendorID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'passenger_count', 'trip_distance', 'RatecodeID', 'store_and_fwd_flag', 'PULocationID', 'DOLocationID', 'payment_type', 'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount', 'improvement_surcharge', 'total_amount', 'congestion_surcharge', 'Airport_fee', 'cbd_congestion_fee']

# ['VendorID', 'lpep_pickup_datetime', 'lpep_dropoff_datetime', 'store_and_fwd_flag', 'RatecodeID', 'PULocationID', 'DOLocationID', 'passenger_count', 'trip_distance', 'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount',  'improvement_surcharge', 'total_amount', 'payment_type',  'congestion_surcharge', 'cbd_congestion_fee']

    df2 = (
        spark.read.parquet(DATA_PATH2)
            .withColumn("source_file", lit("green_tripdata_2026-01.parquet"))
            .withColumnRenamed("lpep_pickup_datetime", "pep_pickup_datetime")
            .withColumnRenamed("lpep_dropoff_datetime", "pep_dropoff_datetime")
            .drop("ehail_fee", "trip_type")
        )

    print(f"Partitions after read: {df2.rdd.getNumPartitions()}")
    print(f"Row count: {df2.count()}")

    df3 = df1.unionByName(df2, allowMissingColumns=False)

    print(f"Row count after union: {df3.count()}")
    print(f"Partitions after union: {df3.rdd.getNumPartitions()}")

    partition_report(df1, "df1")
    partition_report(df2, "df2")
    partition_report(df3, "df3")

    # Part A/B/C - baseline has no-op here; repartition/coalesce applied per --scenario
    if args.scenario == "repartition":
        df3 = df3.repartition(args.partitions)
    elif args.scenario == "coalesce":
        df3 = df3.coalesce(args.partitions)

    partition_report(df3, f"df3 after {args.scenario}")

    agg = (
        df3.withColumn("pickup_date", to_date("pep_pickup_datetime"))
           .groupBy("PULocationID", "pickup_date")
           .agg(avg("fare_amount").alias("avg_fare"), count("*").alias("trip_count"))
    )

    out_path = f"{OUT_DIR}/{args.scenario}"
    start = time.time()
    agg.write.mode("overwrite").parquet(out_path)
    elapsed = time.time() - start

    print(f"\n=== scenario={args.scenario} partitions={args.partitions} ===")
    print(f"Write duration: {elapsed:.2f}s")
    report_output_files(out_path)

    spark.stop()


if __name__ == "__main__":
    main()
