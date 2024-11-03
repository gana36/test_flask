import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import numpy as np

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# For GitHub Pages deployment
server = app.server

# Load data
df = pd.read_csv("https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/global_terror.csv")

# Convert numeric columns
for col in df.select_dtypes(include=['int64', 'float64']).columns:
    df[col] = df[col].astype(float)

# Mapbox token
token = 'YOUR_MAPBOX_TOKEN'

# App layout
app.layout = html.Div([
    html.H1("Terrorism Analysis Dashboard",
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
    
    # Filters
    html.Div([
        html.Div([
            html.Label("Select Region(s)"),
            dcc.Dropdown(
                id='region-dropdown',
                options=[{'label': i, 'value': i} for i in sorted(df['region_txt'].unique())],
                multi=True,
                placeholder="Select Regions"
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),
        
        html.Div([
            html.Label("Select Country(s)"),
            dcc.Dropdown(
                id='country-dropdown',
                options=[],
                multi=True,
                placeholder="Select Countries"
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),
        
        html.Div([
            html.Label("Select Attack Type(s)"),
            dcc.Dropdown(
                id='attack-type-dropdown',
                options=[{'label': i, 'value': i} for i in sorted(df['attacktype1_txt'].unique())],
                multi=True,
                placeholder="Select Attack Types"
            )
        ], style={'width': '30%', 'display': 'inline-block'})
    ], style={'marginBottom': '20px'}),
    
    html.Div([
        html.Label("Select Year Range"),
        dcc.RangeSlider(
            id='year-slider',
            min=df['iyear'].min(),
            max=df['iyear'].max(),
            value=[df['iyear'].min(), df['iyear'].max()],
            marks={str(year): str(year) for year in range(int(df['iyear'].min()), 
                                                        int(df['iyear'].max())+1, 5)},
            step=1
        )
    ], style={'marginBottom': '30px'}),
    
    # Graph and Stats containers
    dcc.Loading(
        id="loading-1",
        type="default",
        children=html.Div(id='graph-container')
    ),
    html.Div(id='statistics-container', style={'marginTop': '30px'})
])

# Callbacks
@app.callback(
    Output('country-dropdown', 'options'),
    Input('region-dropdown', 'value')
)
def update_country_dropdown(selected_regions):
    if not selected_regions:
        return [{'label': i, 'value': i} for i in sorted(df['country_txt'].unique())]
    filtered_countries = df[df['region_txt'].isin(selected_regions)]['country_txt'].unique()
    return [{'label': i, 'value': i} for i in sorted(filtered_countries)]

@app.callback(
    [Output('graph-container', 'children'),
     Output('statistics-container', 'children')],
    [Input('region-dropdown', 'value'),
     Input('country-dropdown', 'value'),
     Input('attack-type-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_visualizations(regions, countries, attack_types, years):
    # Filter data
    filtered_df = df.copy()
    
    if years:
        filtered_df = filtered_df[filtered_df['iyear'].between(years[0], years[1])]
    if regions:
        filtered_df = filtered_df[filtered_df['region_txt'].isin(regions)]
    if countries:
        filtered_df = filtered_df[filtered_df['country_txt'].isin(countries)]
    if attack_types:
        filtered_df = filtered_df[filtered_df['attacktype1_txt'].isin(attack_types)]
    
    # Create map
    fig = px.scatter_mapbox(
        filtered_df,
        lat='latitude',
        lon='longitude',
        hover_data=['region_txt', 'country_txt', 'provstate', 'city',
                   'attacktype1_txt', 'nkill', 'iyear'],
        zoom=1,
        color='attacktype1_txt',
        height=650,
        title='Global Terrorism Incidents'
    )
    
    fig.update_layout(
        mapbox_style='carto-positron',
        mapbox_accesstoken=token,
        autosize=True,
        margin=dict(l=0, r=0, b=25, t=40)
    )
    
    # Calculate statistics
    total_incidents = len(filtered_df)
    total_casualties = filtered_df['nkill'].sum()
    most_affected_country = filtered_df['country_txt'].value_counts().index[0]
    most_common_attack = filtered_df['attacktype1_txt'].value_counts().index[0]
    
    statistics = html.Div([
        html.H3("Key Statistics", style={'textAlign': 'center'}),
        html.Div([
            html.Div([
                html.H4("Total Incidents"),
                html.P(f"{total_incidents:,}")
            ], className='stat-box'),
            html.Div([
                html.H4("Total Casualties"),
                html.P(f"{total_casualties:,.0f}")
            ], className='stat-box'),
            html.Div([
                html.H4("Most Affected Country"),
                html.P(most_affected_country)
            ], className='stat-box'),
            html.Div([
                html.H4("Most Common Attack Type"),
                html.P(most_common_attack)
            ], className='stat-box')
        ], style={'display': 'flex', 'justifyContent': 'space-around'})
    ])
    
    return dcc.Graph(figure=fig), statistics

if __name__ == '__main__':
    app.run_server(debug=True)
