from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

# Define the path to the Delta table
DELTA_PATH = "../delta-table"

# Initialize Spark session with Delta Lake support
builder = (
    SparkSession.builder
    .appName("delta_table_query")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Load the Delta table
df = spark.read.format("delta").load(DELTA_PATH)

# Example query: Show all records
df.show()

# Example query: Filter based on filename or modification time
# Replace "image1.jpg" with the actual filename you want to query
filtered_df = df.filter(df.filename == "image1.png")
filtered_df.show()

# Another example: Select only certain columns
selected_df = df.select("filename", "modificationTime")
selected_df.show()

# If you want to use SQL-like syntax, register the Delta table as a temporary view
df.createOrReplaceTempView("images")

# Example SQL query
sql_query = spark.sql("SELECT * FROM images WHERE modificationTime > '2024-01-01'")
sql_query.show()

# Stop the Spark session after querying
spark.stop()
