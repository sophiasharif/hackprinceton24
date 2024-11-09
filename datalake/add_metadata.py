'''
add_metadata.py: adds metadata to images missing it in a Delta table, does not do anything to images with metadata

- Filters images without metadata (e.g., missing description).
- Retrieves and prepares metadata for each image.
- Uses Delta merge to update records with new metadata while preserving existing data.
- Displays the updated Delta table contents after the merge.
'''

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable
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

# Read the Delta table
df = spark.read.format("delta").load(DELTA_PATH)

# Filter images without metadata (e.g., empty "description")
images_to_update = df.filter(col("description") == "")
print("Images to update:")
images_to_update.show()

# Collect filenames to update
image_rows = images_to_update.select("filename").collect()
image_filenames = [row.filename for row in image_rows]

# Retrieve metadata for each image
image_metadata = {}
for filename in image_filenames:
    metadata = get_metadata(filename)
    image_metadata[filename] = metadata
    print(f"Metadata for {filename}: {metadata}")

# Prepare metadata DataFrame
metadata_tuples = [
    (
        filename,
        metadata['is_recyclable'],
        metadata['is_compostable'],
        metadata['is_metal'],
        metadata['brand'],
        metadata['description']
    )
    for filename, metadata in image_metadata.items()
]

metadata_df = spark.createDataFrame(metadata_tuples, [
    "filename", "is_recyclable", "is_compostable", "is_metal", "brand", "description"
])

# Perform merge operation to update Delta table
deltaTable = DeltaTable.forPath(spark, DELTA_PATH)

deltaTable.alias("old").merge(
    metadata_df.alias("new"),
    "old.filename = new.filename"
).whenMatchedUpdate(set={
    "description": "new.description",
    "is_recyclable": "new.is_recyclable",
    "is_compostable": "new.is_compostable",
    "is_metal": "new.is_metal",
    "brand": "new.brand"
}).execute()

# Show the updated DataFrame
updated_df = spark.read.format("delta").load(DELTA_PATH)
print("Updated Delta table:")
updated_df.show()
