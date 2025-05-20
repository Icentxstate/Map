import streamlit as st
import pandas as pd
import folium
from folium import IFrame
from streamlit_folium import st_folium
import plotly.express as px

# Load data
df = pd.read_csv("INPUT_1.csv")
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude'])

# Select parameter
numeric_cols = df.select_dtypes(include='number').columns.tolist()
param = st.sidebar.selectbox("Select Parameter", numeric_cols)

# Create map
m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()],
               zoom_start=10, control_scale=True)

# Add markers
for site_id in df['Site ID'].unique():
    site_data = df[df['Site ID'] == site_id]
    lat = site_data['Latitude'].iloc[0]
    lon = site_data['Longitude'].iloc[0]
    site_name = site_data['Site Name'].iloc[0]

    # Compute statistics
    mean_val = site_data[param].mean()
    median_val = site_data[param].median()
    std_val = site_data[param].std()

    # Time series plot
    fig = px.line(site_data, x='Date', y=param, title=f'{param} Over Time at {site_name}')
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    fig_html = fig.to_html(include_plotlyjs='cdn')

    # HTML content for popup
    html_content = f"""
    <h4>{site_name}</h4>
    <p><strong>Mean:</strong> {mean_val:.2f}</p>
    <p><strong>Median:</strong> {median_val:.2f}</p>
    <p><strong>Standard Deviation:</strong> {std_val:.2f}</p>
    {fig_html}
    """

    iframe = IFrame(html=html_content, width=550, height=400)
    popup = folium.Popup(iframe, max_width=550)

    # Add circle and marker
    folium.Circle(
        location=[lat, lon],
        radius=1000,
        color='blue',
        fill=True,
        fill_opacity=0.1
    ).add_to(m)

    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=0.7,
        popup=popup
    ).add_to(m)

# Display map
st_folium(m, width=1000, height=600)
