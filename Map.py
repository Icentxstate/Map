import streamlit as st
import pandas as pd
import folium
from folium import IFrame
from streamlit_folium import st_folium
import plotly.express as px
import base64
import io

# Set page configuration
st.set_page_config(page_title="Interactive Water Quality Map", layout="wide")
st.title("💧 Interactive Water Quality Map with Chart Popups")

# Load CSV data
try:
    df = pd.read_csv("INPUT_1.csv")
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])
    st.success("Data loaded successfully.")
except FileNotFoundError:
    st.error("INPUT_1.csv not found. Please ensure the file is in the app directory.")
    st.stop()

# Select parameter
numeric_cols = df.select_dtypes(include='number').columns.tolist()
param = st.sidebar.selectbox("🎯 Select Parameter", numeric_cols)

# Create Folium map
m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()],
               zoom_start=10, control_scale=True)

# Add markers to the map
for site_id in df['Site ID'].unique():
    site_data = df[df['Site ID'] == site_id]
    lat = site_data['Latitude'].iloc[0]
    lon = site_data['Longitude'].iloc[0]
    site_name = site_data['Site Name'].iloc[0]

    # Time Series Chart
    fig_time = px.line(site_data, x='Date', y=param, title=f'{param} Over Time at {site_name}')
    fig_time.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    fig_time_html = fig_time.to_html(include_plotlyjs='cdn')

    # Monthly Average Chart
    site_data['Month'] = site_data['Date'].dt.to_period('M')
    monthly_avg = site_data.groupby('Month')[param].mean().reset_index()
    monthly_avg['Month'] = monthly_avg['Month'].astype(str)
    fig_month = px.bar(monthly_avg, x='Month', y=param, title=f'Monthly Average of {param} at {site_name}')
    fig_month.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    fig_month_html = fig_month.to_html(include_plotlyjs=False)

    # Yearly Average Chart
    site_data['Year'] = site_data['Date'].dt.year
    yearly_avg = site_data.groupby('Year')[param].mean().reset_index()
    fig_year = px.bar(yearly_avg, x='Year', y=param, title=f'Yearly Average of {param} at {site_name}')
    fig_year.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    fig_year_html = fig_year.to_html(include_plotlyjs=False)

    # Combine charts into tabs using HTML
    html_content = f"""
    <html>
    <head>
    <style>
    .tab {{
      overflow: hidden;
      border: 1px solid #ccc;
      background-color: #f1f1f1;
    }}
    .tab button {{
      background-color: inherit;
      float: left;
      border: none;
      outline: none;
      cursor: pointer;
      padding: 10px 16px;
      transition: 0.3s;
      font-size: 14px;
    }}
    .tab button:hover {{
      background-color: #ddd;
    }}
    .tab button.active {{
      background-color: #ccc;
    }}
    .tabcontent {{
      display: none;
      padding: 6px 12px;
      border: 1px solid #ccc;
      border-top: none;
    }}
    </style>
    </head>
    <body>

    <h4>{site_name}</h4>

    <div class="tab">
      <button class="tablinks" onclick="openTab(event, 'Time')" id="defaultOpen">Time Series</button>
      <button class="tablinks" onclick="openTab(event, 'Monthly')">Monthly Average</button>
      <button class="tablinks" onclick="openTab(event, 'Yearly')">Yearly Average</button>
    </div>

    <div id="Time" class="tabcontent">
      {fig_time_html}
    </div>

    <div id="Monthly" class="tabcontent">
      {fig_month_html}
    </div>

    <div id="Yearly" class="tabcontent">
      {fig_year_html}
    </div>

    <script>
    function openTab(evt, tabName) {{
      var i, tabcontent, tablinks;
      tabcontent = document.getElementsByClassName("tabcontent");
      for (i = 0; i < tabcontent.length; i++) {{
        tabcontent[i].style.display = "none";
      }}
      tablinks = document.getElementsByClassName("tablinks");
      for (i = 0; i < tablinks.length; i++) {{
        tablinks[i].className = tablinks[i].className.replace(" active", "");
      }}
      document.getElementById(tabName).style.display = "block";
      evt.currentTarget.className += " active";
    }}
    document.getElementById("defaultOpen").click();
    </script>

    </body>
    </html>
    """

    iframe = IFrame(html=html_content, width=550, height=400)
    popup = folium.Popup(iframe, max_width=550)

    # Add circle with 1 km radius
    folium.Circle(
        location=[lat, lon],
        radius=1000,
        color='blue',
        fill=True,
        fill_opacity=0.1
    ).add_to(m)

    # Add marker with popup
    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=0.7,
        popup=popup
    ).add_to(m)

# Display map in Streamlit
st_folium(m, width=1000, height=600)
