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

# extract the filename from the file path & modification time
new_images_df = new_images_df.withColumn("filename", fn.element_at(fn.split(new_images_df.path, "/"), -1))
new_images_df = new_images_df.withColumn("description", fn.lit("test"))
new_images_df = new_images_df.select("filename", "modificationTime", "description")

try:
    existing_df = spark.read.format("delta").load(DELTA_PATH)
    new_images_df = new_images_df.join(existing_df, on="filename", how="left_anti")
except Exception as e:
    print("Delta table not found. Loading all images as new.")


new_images_df.write.format("delta").mode("overwrite").option("mergeSchema", "true").save(DELTA_PATH)

# read table 
df = spark.read.format("delta").load(DELTA_PATH)

print("Delta table schema:")
df.printSchema()

print("Delta table contents:")
df.show()

