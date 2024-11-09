'''
update_data_frame.py

- Extracts basic file metadata (filename, modification time) from images.
- Adds default metadata fields (description, is_recyclable, is_compostable, is_metal, brand).
- Appends new images or creates a new Delta table with specified schema.
'''

import pyspark.sql.functions as fn
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
import shutil
from urllib import request
import os

IMAGE_PATH = "../images"
DELTA_PATH = "../delta-table"

builder = (
    SparkSession.builder
    .appName("incremental_image_load")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# load images
new_images_df = spark.read.format("binaryFile").load(IMAGE_PATH)

# Load images with essential fields only
new_images_df = spark.read.format("binaryFile").load(IMAGE_PATH)
new_images_df = new_images_df.withColumn("filename", fn.element_at(fn.split(new_images_df.path, "/"), -1))
new_images_df = new_images_df.withColumnRenamed("modificationTime", "time")
new_images_df = new_images_df.select("filename", "time")

# Add metadata columns with default values
new_images_df = new_images_df.withColumn("state", fn.lit("NJ"))
new_images_df = new_images_df.withColumn("city", fn.lit("Princeton"))
new_images_df = new_images_df.withColumn("description", fn.lit(""))
new_images_df = new_images_df.withColumn("is_recyclable", fn.lit(None).cast("boolean"))
new_images_df = new_images_df.withColumn("is_compostable", fn.lit(None).cast("boolean"))
new_images_df = new_images_df.withColumn("is_metal", fn.lit(None).cast("boolean"))
new_images_df = new_images_df.withColumn("brand", fn.lit(""))

# Attempt to load existing Delta table and avoid duplications
try:
    existing_df = spark.read.format("delta").load(DELTA_PATH)
    new_images_df = new_images_df.join(existing_df, on="filename", how="left_anti")
    # Append new images to the Delta table
    new_images_df.write.format("delta").mode("append").option("mergeSchema", "true").save(DELTA_PATH)
except Exception as e:
    print("Delta table not found. Creating a new one.")
    # Overwrite and create new Delta table with initial data
    new_images_df.write.format("delta").mode("overwrite").option("mergeSchema", "true").save(DELTA_PATH)

# ... [rest of your code, such as printing schema and contents] ...

# show schema
print("Delta table")
new_images_df.show()