from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from delta import configure_spark_with_delta_pip
import os
from openai import OpenAI


DELTA_PATH = "../delta-table"
IMAGE_PATH = "../images"

builder = (
    SparkSession.builder
    .appName("image_metadata_processing")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()

df = spark.read.format("delta").load(DELTA_PATH)

# filter for images without metadata (e.g., missing "description" or "classification" fields)
images_to_update = df.filter(col("description") == "test")
images_to_update.show()

image_filenames = images_to_update.select("filename").collect()
image_paths = [os.path.join(IMAGE_PATH, row.filename) for row in image_filenames]
print(image_paths)




