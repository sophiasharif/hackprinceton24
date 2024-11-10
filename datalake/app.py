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

# Ensure that items that are both compostable and recyclable are counted as recyclable
# So we set 'is_compostable' to False if 'is_recyclable' is True
df = df.withColumn('is_compostable', fn.when(col('is_recyclable'), False).otherwise(col('is_compostable')))

# Create 'is_trash' column for items that are neither compostable nor recyclable
df = df.withColumn('is_trash', ~(col('is_compostable') | col('is_recyclable')))

# Truncate 'time' to the hour for grouping
df = df.withColumn('hour', fn.hour(col('time')))

# ====== Existing Area Chart Data Preparation ======

# Group by 'hour' and compute counts for the area chart
grouped_df_time = df.groupBy('hour').agg(
    fn.count('*').alias('total_count'),
    fn.sum(col('is_compostable').cast('int')).alias('compostable_count'),
    fn.sum(col('is_recyclable').cast('int')).alias('recyclable_count'),
    fn.sum(col('is_trash').cast('int')).alias('trash_count')
)

# Calculate percentages
grouped_df_time = grouped_df_time.withColumn('compostable_pct', (col('compostable_count') / col('total_count')) * 100)
grouped_df_time = grouped_df_time.withColumn('recyclable_pct', (col('recyclable_count') / col('total_count')) * 100)
grouped_df_time = grouped_df_time.withColumn('trash_pct', (col('trash_count') / col('total_count')) * 100)

# Order by 'hour'
grouped_df_time = grouped_df_time.orderBy('hour')

# Convert to Pandas DataFrame for plotting
pandas_df_time = grouped_df_time.toPandas()

# Melt the DataFrame for plotting
melted_df_time = pandas_df_time.melt(
    id_vars=['hour'],
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
melted_df_time['Category'] = melted_df_time['Category'].map(category_mapping)

# ====== New Bar Graph Data Preparation ======

# Group by 'brand' and compute counts
grouped_df_brand = df.groupBy('brand').agg(
    fn.count('*').alias('total_count'),
    fn.sum(col('is_compostable').cast('int')).alias('compostable_count'),
    fn.sum(col('is_recyclable').cast('int')).alias('recyclable_count'),
    fn.sum(col('is_trash').cast('int')).alias('trash_count')
)

# Calculate percentages
grouped_df_brand = grouped_df_brand.withColumn('compostable_pct', (col('compostable_count') / col('total_count')) * 100)
grouped_df_brand = grouped_df_brand.withColumn('recyclable_pct', (col('recyclable_count') / col('total_count')) * 100)
grouped_df_brand = grouped_df_brand.withColumn('trash_pct', (col('trash_count') / col('total_count')) * 100)

# Convert to Pandas DataFrame for plotting
pandas_df_brand = grouped_df_brand.toPandas()

# Melt the DataFrame for plotting
melted_df_brand = pandas_df_brand.melt(
    id_vars=['brand', 'total_count'],
    value_vars=['compostable_pct', 'recyclable_pct', 'trash_pct'],
    var_name='Category',
    value_name='Percentage'
)

# Map category names for better readability
melted_df_brand['Category'] = melted_df_brand['Category'].map(category_mapping)

# Show dataframes for debugging
print("Area Chart Data:")
print(pandas_df_time)
print(melted_df_time)
print("\nBar Graph Data:")
print(pandas_df_brand)
print(melted_df_brand)

# ====== Create the Area Chart ======

# Create the area chart using Plotly
fig_area = px.area(
    melted_df_time,
    x='hour',
    y='Percentage',
    color='Category',
    labels={
        'hour': 'Time of Day',
        'Percentage': 'Percentage (%)',
        'Category': 'Category'
    },
    title='Trash Composition Over Time'
)

# Update figure layout for better readability
fig_area.update_layout(
    xaxis=dict(tickmode='linear'),
    legend_title_text='Category'
)

# ====== Create the Bar Graph ======

# Create the stacked bar chart using Plotly
fig_bar = px.bar(
    melted_df_brand,
    x='brand',
    y='Percentage',
    color='Category',
    labels={
        'brand': 'Brand',
        'Percentage': 'Percentage (%)',
        'Category': 'Category'
    },
    title='Waste Composition by Brand',
    text='total_count'  # Display total waste count on bars
)

# Update figure layout for better readability
fig_bar.update_layout(
    legend_title_text='Category',
    xaxis={'categoryorder':'total descending'}
)

# Add total waste count as annotations
for i, total in enumerate(pandas_df_brand['total_count']):
    fig_bar.add_annotation(
        x=pandas_df_brand['brand'][i],
        y=100,
        text=f"Total: {total}",
        showarrow=False,
        yshift=10
    )

# ====== Define the Dash App Layout ======

# Create the Dash app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div(children=[
    html.H1(children='Trash Composition Analysis'),

    html.Div([
        html.H2('Trash Composition Over Time'),
        dcc.Graph(
            id='trash-composition-graph',
            figure=fig_area
        )
    ]),

    html.Div([
        html.H2('Waste Composition by Brand'),
        dcc.Graph(
            id='waste-composition-brand',
            figure=fig_bar
        )
    ])
])

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
