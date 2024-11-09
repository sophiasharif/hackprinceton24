from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from delta import configure_spark_with_delta_pip
import os

DELTA_PATH = "../delta-table"


builder = (
    SparkSession.builder
    .appName("image_metadata_processing")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()

df = spark.read.format("delta").load(DELTA_PATH)

# filter for images without metadata (e.g., missing "description" or "classification" fields)
images_without_metadata = df.filter(df["description"].isNull())

images_without_metadata.show()
