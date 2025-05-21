import streamlit as st
import pandas as pd
import folium
from folium import CircleMarker, Circle
from folium.plugins import MarkerCluster
from branca.colormap import linear
from streamlit_folium import st_folium
import plotly.express as px

# ---------- Page Config ----------
st.set_page_config(page_title="Water Quality Dashboard", layout="wide")

# ---------- Theme Toggle ----------
theme = st.sidebar.radio("🎨 Theme", ["Light", "Dark"])

if theme == "Dark":
    bg_color = "#2b2b2b"
    text_color = "#f0f0f0"
    card_bg = "#3b3b3b"
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
    st.error("❌ Could not load INPUT_1.csv. Make sure it exists and is formatted correctly.")
    st.stop()

# ---------- Sidebar Controls ----------
st.sidebar.markdown("## ⚙️ Controls")
numeric_cols = df.select_dtypes(include='number').columns.tolist()
param = st.sidebar.selectbox("🧪 Select Parameter", numeric_cols)

all_sites = df['Site Name'].unique().tolist()
search_text = st.sidebar.text_input("🔍 Search Site", "")
filtered_sites = [s for s in all_sites if search_text.lower() in s.lower()]

# ---------- Summary Info ----------
total_sites = df['Site ID'].nunique()
date_range = f"{df['Date'].min().date()} → {df['Date'].max().date()}"
selected_param_name = param

st.markdown(f"""
<div class="card-container">
    <div class="card">
        <h2>{total_sites}</h2>
        <p>Total Sites</p>
    </div>
    <div class="card">
        <h2>{date_range}</h2>
        <p>Date Range</p>
    </div>
    <div class="card">
        <h2>{selected_param_name}</h2>
        <p>Selected Parameter</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- Map ----------
st.subheader("🗺️ Average Value Map by Site")

# Calculate average by site
grouped = df.groupby('Site Name')
avg_df = grouped[param].mean().reset_index()
avg_df = avg_df.merge(df[['Site Name', 'Latitude', 'Longitude']].drop_duplicates(), on='Site Name')

vmin = avg_df[param].min()
vmax = avg_df[param].max()
if pd.isna(vmin) or pd.isna(vmax) or vmin == vmax:
    st.warning(f"⚠️ Cannot render colormap for parameter: {param}")
    st.stop()

colormap = linear.YlOrRd_09.scale(vmin, vmax)
colormap.caption = f"{param} Average Scale"

m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=8, control_scale=True)
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

    # Shadow circle
    Circle(location=[lat, lon],
           radius=1000,
           color=color,
           fill=True,
           fill_opacity=0.2).add_to(marker_cluster)

    # Marker on top
    CircleMarker(location=[lat, lon],
                 radius=8,
                 color=color,
                 fill=True,
                 fill_opacity=0.9,
                 popup=folium.Popup(popup_content, max_width=300)).add_to(marker_cluster)

m.add_child(colormap)
clicked = st_folium(m, width=1100, height=500)

# ---------- Handle Map Click Selection ----------
clicked_site = None
if clicked and clicked.get("last_object_clicked"):
    lat = clicked["last_object_clicked"]["lat"]
    lon = clicked["last_object_clicked"]["lng"]
    df['distance'] = ((df['Latitude'] - lat)**2 + (df['Longitude'] - lon)**2)**0.5
    clicked_site = df.loc[df['distance'].idxmin()]['Site Name']

selected_site = st.sidebar.selectbox(
    "📍 Select Site", filtered_sites,
    index=filtered_sites.index(clicked_site) if clicked_site in filtered_sites else 0
)

# ---------- Analysis Tabs ----------
st.subheader("📊 Parameter Analysis – Trends & Averages")

site_df = df[df['Site Name'] == selected_site].copy()
site_df['Month'] = site_df['Date'].dt.to_period('M')
site_df['Year'] = site_df['Date'].dt.year

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📈 Time Series", "📆 Monthly Avg", "📅 Yearly Avg"])

with tab1:
    fig1 = px.line(site_df, x='Date', y=param, title=f'{param} Over Time at {selected_site}')
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    monthly = site_df.groupby('Month')[param].mean().reset_index()
    monthly['Month'] = monthly['Month'].astype(str)
    fig2 = px.bar(monthly, x='Month', y=param, title=f'Monthly Average of {param}')
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    yearly = site_df.groupby('Year')[param].mean().reset_index()
    fig3 = px.bar(yearly, x='Year', y=param, title=f'Yearly Average of {param}')
    st.plotly_chart(fig3, use_container_width=True)

# ---------- Download Button ----------
st.download_button(
    label="💾 Download This Site's Data",
    data=site_df.to_csv(index=False).encode('utf-8'),
    file_name=f"{selected_site.replace(' ', '_')}_data.csv",
    mime="text/csv"
)
