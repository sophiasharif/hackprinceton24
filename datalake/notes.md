# DataLake Notes

## Useful Resources

- [Getting Started with Delta Lake](https://delta.io/learn/getting-started/)
- [python examples](https://github.com/delta-io/delta/tree/master/examples/python)
- the code in test.py is copied from [this file](https://github.com/delta-io/delta/blob/master/examples/python/image_storage.py)

## To run

- had to install java
- ran `pip install pyspark` and `pip install delta-spark`, but hopefully the pip freeze in requirements.txt works

## useful stuff we could do

Query data with spark sql:

```
dfDelta.createOrReplaceTempView("flowers")

# Example 1: Count the number of images per flower type
spark.sql("SELECT flowerType, COUNT(*) as count FROM flowers GROUP BY flowerType").show()

# Example 2: Display all images of a specific flower type
spark.sql("SELECT * FROM flowers WHERE flowerType = 'daisy'").show()
```

load a saved table from another script (if we want to create a frontend that show data analytics)

```
# Load the Delta table
df = spark.read.format("delta").load("/tmp/delta-table")
df.show()
```

## Instructions on how to use

- add new image to `images` directory
- run `python update_data_frame.py` to add it to the delta lake
- run `python add_metadata` to generate metadata for the image and update the delta lake
