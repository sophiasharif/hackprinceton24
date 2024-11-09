# app.py

from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
import pandas as pd
import pyspark.sql.functions as fn
from pyspark.sql.functions import col
import dash
from dash import dcc, html
import plotly.express as px

# Define the path to the Delta table
DELTA_PATH = "../delta-table"

# Initialize Spark session with Delta Lake support
builder = (
    SparkSession.builder
    .appName("TrashCompositionApp")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Load the Delta table
df = spark.read.format("delta").load(DELTA_PATH)

# Fill nulls in 'is_compostable' and 'is_recyclable' with False
df = df.fillna({'is_compostable': False, 'is_recyclable': False})

# Create 'is_trash' column for items that are neither compostable nor recyclable
df = df.withColumn('is_trash', ~(col('is_compostable') | col('is_recyclable')))

# Truncate 'time' to the hour for grouping
df = df.withColumn('datetime_hour', fn.date_trunc('hour', df['time']))

# Group by 'datetime_hour' and compute counts
grouped_df = df.groupBy('datetime_hour').agg(
    fn.count('*').alias('total_count'),
    fn.sum(col('is_compostable').cast('int')).alias('compostable_count'),
    fn.sum(col('is_recyclable').cast('int')).alias('recyclable_count'),
    fn.sum(col('is_trash').cast('int')).alias('trash_count')
)

# Calculate percentages
grouped_df = grouped_df.withColumn('compostable_pct', (col('compostable_count') / col('total_count')) * 100)
grouped_df = grouped_df.withColumn('recyclable_pct', (col('recyclable_count') / col('total_count')) * 100)
grouped_df = grouped_df.withColumn('trash_pct', (col('trash_count') / col('total_count')) * 100)

# Order by 'datetime_hour'
grouped_df = grouped_df.orderBy('datetime_hour')

# Convert to Pandas DataFrame for plotting
pandas_df = grouped_df.toPandas()

# Melt the DataFrame for plotting
melted_df = pandas_df.melt(
    id_vars=['datetime_hour'],
    value_vars=['compostable_pct', 'recyclable_pct', 'trash_pct'],
    var_name='Category',
    value_name='Percentage'
)

# Map category names for better readability
category_mapping = {
    'compostable_pct': 'Compostable',
    'recyclable_pct': 'Recyclable',
    'trash_pct': 'Trash'
}
melted_df['Category'] = melted_df['Category'].map(category_mapping)

# Create the Dash app
app = dash.Dash(__name__)

# Create the area chart using Plotly
fig = px.area(
    melted_df,
    x='datetime_hour',
    y='Percentage',
    color='Category',
    labels={
        'datetime_hour': 'Time of Day',
        'Percentage': 'Percentage (%)',
        'Category': 'Category'
    },
    title='Trash Composition Over Time'
)

# Update figure layout for better readability
fig.update_layout(
    xaxis=dict(tickformat='%Y-%m-%d %H:%M'),
    legend_title_text='Category'
)

# Define the app layout
app.layout = html.Div(children=[
    html.H1(children='Trash Composition Over Time'),
    dcc.Graph(
        id='trash-composition-graph',
        figure=fig
    )
])

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
