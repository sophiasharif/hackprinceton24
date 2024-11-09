from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from delta import configure_spark_with_delta_pip
from gpt import get_metadata
import os

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
images_to_update = df.filter(col("description") == "")
images_to_update.show()

image_rows = images_to_update.select("filename").collect()
image_filenames = [row.filename for row in image_rows]

image_metadata = {}
image_metadata = {'image3.jpg': {'is_recyclable': True, 'is_compostable': False, 'is_metal': False, 'brand': 'Kirkland', 'description': 'empty water bottle'},
'image2.jpg': {'is_recyclable': False, 'is_compostable': False, 'is_metal': False, 'brand': 'Ruffles', 'description': 'Baked cheddar and sour cream chips'},
'image1.jpg': {'is_recyclable': False, 'is_compostable': True, 'is_metal': False, 'brand': '', 'description': 'Paper napkin wrapped in plastic'}}

# for filename in image_filenames:
#     metadata = get_metadata(filename)
#     image_metadata[filename] = metadata
#     print(f"Metadata for {filename}: {metadata}")

# update schema

metadata_tuples = [(filename, metadata['is_recyclable'], metadata['is_compostable'], 
                    metadata['is_metal'], metadata['brand'], metadata['description']) 
                   for filename, metadata in image_metadata.items()]

metadata_df = spark.createDataFrame(metadata_tuples, 
                                    ["filename", "is_recyclable", "is_compostable", "is_metal", "brand", "description"])

# Join images_to_update with metadata_df on the filename column
updated_df = images_to_update.join(metadata_df, on="filename", how="left")

# Save the updated DataFrame back to the Delta table
updated_df.write.format("delta").mode("overwrite").option("mergeSchema", "true").save(DELTA_PATH)

# Show the updated DataFrame
updated_df.show()



