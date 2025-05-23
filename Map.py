import streamlit as st
import pandas as pd
import folium
from folium import CircleMarker, Circle
from folium.plugins import MarkerCluster
from branca.colormap import linear
from streamlit_folium import st_folium
import plotly.express as px
import geopandas as gpd
import zipfile
import os

# ---------- Page Config ----------
st.set_page_config(page_title="Water Quality Dashboard", layout="wide")

# ---------- Theme Toggle ----------
theme = st.sidebar.radio("Theme", ["Light", "Dark", "Green-Blue"])

if theme == "Dark":
    bg_color = "#2b2b2b"
    text_color = "#f0f0f0"
    card_bg = "#3b3b3b"
elif theme == "Green-Blue":
    bg_color = "#e0f7fa"
    text_color = "#004d40"
    card_bg = "#b2dfdb"
else:
    bg_color = "#f7f9fa"
    text_color = "#222"
    card_bg = "#ffffff"

st.markdown(f"""
    <style>
    body, .stApp {{
        background-color: {bg_color};
        color: {text_color};
        font-family: 'Segoe UI', sans-serif;
    }}
    .card-container {{
        display: flex;
        justify-content: space-around;
        margin-bottom: 30px;
    }}
    .card {{
        background-color: {card_bg};
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        text-align: center;
        flex: 1;
        margin: 0 10px;
    }}
    .card h2 {{
        color: #1f77b4;
        font-size: 28px;
        margin-bottom: 5px;
    }}
    .card p {{
        font-size: 15px;
        color: #888;
    }}
    </style>
""", unsafe_allow_html=True)

# ---------- Load Data ----------
try:
    df = pd.read_csv("INPUT_1.csv")
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])
except:
    st.error("Could not load INPUT_1.csv. Make sure it exists and is formatted correctly.")
    st.stop()

# ---------- Sidebar Controls ----------
st.sidebar.markdown("## Controls")
numeric_cols = [col for col in df.select_dtypes(include='number').columns if col != 'Site ID']
param = st.sidebar.selectbox("Select Parameter", numeric_cols)
shp_zip = st.sidebar.file_uploader("Upload Watershed Shapefile (.zip)", type=["zip"])

all_sites = df['Site Name'].unique().tolist()

# ---------- Map ----------
st.subheader("Average Value Map by Site")
grouped = df.groupby('Site Name')
avg_df = grouped[param].mean().reset_index()
avg_df = avg_df.merge(df[['Site Name', 'Latitude', 'Longitude']].drop_duplicates(), on='Site Name')

vmin = avg_df[param].min()
vmax = avg_df[param].max()
if pd.isna(vmin) or pd.isna(vmax) or vmin == vmax:
    st.warning(f"Cannot render colormap for parameter: {param}")
    st.stop()

colormap = linear.YlGnBu_09.scale(vmin, vmax)
colormap.caption = f"{param} Average Scale"

m = folium.Map(zoom_start=8, control_scale=True)
bounds = [[df['Latitude'].min(), df['Longitude'].min()],
          [df['Latitude'].max(), df['Longitude'].max()]]
m.fit_bounds(bounds)

marker_cluster = MarkerCluster().add_to(m)

for _, row in avg_df.iterrows():
    val = row[param]
    site_name = row['Site Name']
    site_data = df[df['Site Name'] == site_name]
    lat = row['Latitude']
    lon = row['Longitude']

    try:
        color = colormap(val)
    except ValueError:
        color = "gray"

    popup_content = f"""
    <b>Site:</b> {site_name}<br>
    <b>Latitude:</b> {lat:.4f}<br>
    <b>Longitude:</b> {lon:.4f}<br>
    <b>Start Date:</b> {site_data['Date'].min().date()}<br>
    <b>End Date:</b> {site_data['Date'].max().date()}<br>
    <b>Avg {param}:</b> {val:.2f}
    """

    Circle(location=[lat, lon], radius=200, color=color, fill=True, fill_opacity=0.1).add_to(m)
    CircleMarker(location=[lat, lon], radius=8, color=color, fill=True, fill_opacity=0.9,
                 popup=folium.Popup(popup_content, max_width=300)).add_to(marker_cluster)

# ---------- بارگذاری فایل ZIP ----------
shp_zip = st.sidebar.file_uploader("📁 Upload Watershed Shapefile (.zip)", type=["zip"])

if shp_zip is not None:
    with zipfile.ZipFile(shp_zip, "r") as zf:
        extract_path = "/tmp/shapefile"
        zf.extractall(extract_path)

    # پیدا کردن فایل .shp
    shp_files = [f for f in os.listdir(extract_path) if f.endswith(".shp")]
    if not shp_files:
        st.error("⚠️ No .shp file found inside the ZIP.")
    else:
        shp_path = os.path.join(extract_path, shp_files[0])
        try:
            gdf = gpd.read_file(shp_path)
            geojson_data = gdf.to_json()
            folium.GeoJson(
                geojson_data,
                name="Watershed Shapefile",
                style_function=lambda feature: {
                    "fillColor": "#b2dfdb",
                    "color": "#00695c",
                    "weight": 2,
                    "fillOpacity": 0.2,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=[col for col in gdf.columns if gdf[col].dtype == object][:3],
                    aliases=["Attr1", "Attr2", "Attr3"],
                    labels=True
                )
            ).add_to(m)
        except Exception as e:
            st.error(f"❌ Failed to read shapefile: {e}")

# ---------- Add Watershed Shapefile Layer ----------
if shp_zip is not None:
    with zipfile.ZipFile(shp_zip, "r") as zf:
        zf.extractall("/tmp/shapefile")
    shp_files = [f for f in os.listdir("/tmp/shapefile") if f.endswith(".shp")]
    if not shp_files:
        st.error("No .shp file found in the ZIP.")
    else:
        gdf = gpd.read_file(os.path.join("/tmp/shapefile", shp_files[0]))
        geojson_data = gdf.to_json()
        folium.GeoJson(
            geojson_data,
            name="Watershed Shapefile",
            style_function=lambda feature: {
                "fillColor": "#b2dfdb",
                "color": "#00695c",
                "weight": 2,
                "fillOpacity": 0.2,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[col for col in gdf.columns if gdf[col].dtype == object][:3],
                aliases=["Attr1", "Attr2", "Attr3"],
                labels=True
            )
        ).add_to(m)

m.add_child(colormap)
clicked = st_folium(m, use_container_width=True)
