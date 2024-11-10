# app.py

from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
import pandas as pd
import pyspark.sql.functions as fn
from pyspark.sql.functions import col, when
import dash
from dash import dcc, html
import plotly.express as px
import plotly.io as pio
from dash.dependencies import Input, Output

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

# External stylesheets for dark theme and fonts
external_stylesheets = [
    'https://cdnjs.cloudflare.com/ajax/libs/bootswatch/4.5.2/cyborg/bootstrap.min.css',
    'https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap'
]

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Define the app layout
app.layout = html.Div(
    children=[
        html.H1('Trash Composition Analysis', style={'fontSize': '36px', 'fontWeight': 'bold', 'marginTop': '40px'}),
        html.Div([
            dcc.Graph(id='trash-composition-graph')
        ], style={'margin': '50px'}),
        html.Div([
            dcc.Graph(id='waste-composition-brand')
        ], style={'margin': '50px'}),
        html.Div([
            dcc.Graph(id='most-wasteful-brands')
        ], style={'margin': '50px'}),
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # Update every 30 seconds
            n_intervals=0
        )
    ]
)

@app.callback(
    [Output('trash-composition-graph', 'figure'),
     Output('waste-composition-brand', 'figure'),
     Output('most-wasteful-brands', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n_intervals):
    # Load the Delta table
    df = spark.read.format("delta").load(DELTA_PATH)
    
    # Data preprocessing
    df = df.fillna({'is_compostable': False, 'is_recyclable': False})  # Fill nulls
    df = df.withColumn('brand', when(col('brand') == '', 'Other').otherwise(col('brand')))
    
    # Don't double-count items that are both compostable and recyclable
    df = df.withColumn('is_compostable', fn.when(col('is_recyclable'), False).otherwise(col('is_compostable')))
    
    # Create 'is_trash' column
    df = df.withColumn('is_trash', ~(col('is_compostable') | col('is_recyclable')))
    
    # Truncate 'time' to the hour
    df = df.withColumn('hour', fn.hour(col('time')))
    
    # ====== Area Chart Data Preparation ======
    
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
    
    # ====== Bar Graph Data Preparation ======
    
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
    
    # ====== Most Wasteful Brands Data Preparation ======
    
    # Group by 'brand' and compute total waste counts
    waste_by_brand = df.groupBy('brand').agg(
        fn.count('*').alias('total_waste_count')
    )
    
    # Convert to Pandas DataFrame
    waste_by_brand_df = waste_by_brand.toPandas()
    
    # Sort by 'total_waste_count' in descending order to get most wasteful brands
    waste_by_brand_df = waste_by_brand_df.sort_values(by='total_waste_count', ascending=False)
    
    # Select top N most wasteful brands
    top_n = 10  # You can change this number as needed
    top_wasteful_brands = waste_by_brand_df.head(top_n)
    
    # ====== Create Figures ======
    
    # Use Plotly's dark theme
    pio.templates.default = "plotly_dark"
    
    # Create the area chart
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
    
    fig_area.update_layout(
        xaxis=dict(tickmode='linear'),
        legend_title_text='Category',
        font=dict(family='Roboto, sans-serif'),
        plot_bgcolor='#2c2c2e',
        paper_bgcolor='#2c2c2e'
    )
    
    # Create the stacked bar chart
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
    )
    
    fig_bar.update_layout(
        legend_title_text='Category',
        xaxis={'categoryorder': 'total descending'},
        font=dict(family='Roboto, sans-serif'),
        plot_bgcolor='#2c2c2e',
        paper_bgcolor='#2c2c2e'
    )
    
    # Add total waste count as annotations
    for i, total in enumerate(pandas_df_brand['total_count']):
        fig_bar.add_annotation(
            x=pandas_df_brand['brand'][i],
            y=100,
            text=f"Total: {total}",
            showarrow=False,
            yshift=10,
            font=dict(color='white')
        )
    
    # Create the bar chart for most wasteful brands
    fig_most_wasteful = px.bar(
        top_wasteful_brands,
        x='brand',
        y='total_waste_count',
        labels={
            'brand': 'Brand',
            'total_waste_count': 'Total Waste Items'
        },
        title='Top Most Wasteful (and Most Consumed) Brands'
    )
    
    fig_most_wasteful.update_layout(
        xaxis_title='Brand',
        yaxis_title='Total Waste Produced',
        xaxis_tickangle=45,
        font=dict(family='Roboto, sans-serif'),
        plot_bgcolor='#2c2c2e',
        paper_bgcolor='#2c2c2e'
    )
    
    return fig_area, fig_bar, fig_most_wasteful

if __name__ == '__main__':
    app.run_server(debug=True)
