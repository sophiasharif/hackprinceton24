# update_data_frame_with_array.py

import pyspark.sql.functions as fn
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

DELTA_PATH = "../delta-table"
JSON_FILE_PATH = "notional_data.json"

# Set up SparkSession with Delta Lake configurations
builder = (
    SparkSession.builder
    .appName("incremental_data_load")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Convert the array of dictionaries to a Spark DataFrame
new_data_df = spark.read.option("multiLine", "true").json(JSON_FILE_PATH)

# Convert the `time` field to a timestamp
new_data_df = new_data_df.withColumn("time", fn.to_timestamp("time"))

print("New data schema:")
new_data_df.printSchema()

# Ensure that the schema matches the Delta table schema
# If there are additional columns in the Delta table, add them with default values
# new_data_df = new_data_df.withColumn("additional_column", fn.lit(None).cast("desired_data_type"))
# Repeat for other columns as necessary

# Attempt to load existing Delta table and avoid duplications

try:
    existing_df = spark.read.format("delta").load(DELTA_PATH)
    print("Existing Delta table schema:")
    existing_df.printSchema()
    # Use a left_anti join to find new records not in the existing Delta table
    new_data_df = new_data_df.join(existing_df, on="filename", how="left_anti")

    # Append new data to the Delta table
    new_data_df.write.format("delta").mode("append").option("mergeSchema", "true").save(DELTA_PATH)
except Exception as e:
    print("Delta table not found. Creating a new one.")
    # Overwrite and create new Delta table with initial data
    new_data_df.write.format("delta").mode("overwrite").option("mergeSchema", "true").save(DELTA_PATH)
