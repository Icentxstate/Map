import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from folium import CircleMarker, Map, Circle
import datetime

# ---- Theme Toggle ----
theme = st.sidebar.radio("🎨 Theme", ["Light", "Dark"])

if theme == "Dark":
    bg_color = "#2b2b2b"
    text_color = "#f0f0f0"
    card_bg = "#3b3b3b"
else:
    bg_color = "#f7f9fa"
    text_color = "#222"
    card_bg = "#ffffff"

# ---- Inject Custom CSS for Font + Cards ----
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

#-------------------df-------------
# ---- Show Summary Cards ----
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

# ---------- Page Config ----------
st.set_page_config(page_title="Water Quality Dashboard", layout="wide")

# ---------- Load Data ----------
df = pd.read_csv("INPUT_1.csv")
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude'])

# ---------- Select Parameter ----------
numeric_cols = df.select_dtypes(include='number').columns.tolist()
param = st.sidebar.selectbox("🔬 Select Parameter", numeric_cols)

# ---------- Summary Cards ----------
st.markdown("""
    <style>
    .card-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 30px;
    }
    .card {
        flex: 1;
        background-color: #f7f9fa;
        padding: 20px;
        margin: 0 10px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .card h2 {
        font-size: 28px;
        margin-bottom: 5px;
        color: #1f77b4;
    }
    .card p {
        font-size: 16px;
        color: #555;
    }
    </style>
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
            <h2>{selected_param}</h2>
            <p>Parameter</p>
        </div>
    </div>
""".format(
    total_sites=df['Site ID'].nunique(),
    date_range=f"{df['Date'].min().date()} → {df['Date'].max().date()}",
    selected_param=param
), unsafe_allow_html=True)

# ---------- Map Section ----------
st.subheader("🗺️ Monitoring Sites Map")

m = Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=8, control_scale=True)

for _, row in df.iterrows():
    Circle(location=[row['Latitude'], row['Longitude']],
           radius=1000,
           color='blue',
           fill=True,
           fill_opacity=0.1).add_to(m)

    CircleMarker(location=[row['Latitude'], row['Longitude']],
                 radius=6,
                 color='crimson',
                 fill=True,
                 fill_opacity=0.9,
                 popup=row['Site Name']).add_to(m)

st_folium(m, width=1100, height=500, returned_objects=[])

# ---------- Time Series Chart ----------
st.subheader("📈 Time Series of Selected Parameter")

selected_site = st.selectbox("Select Site for Trend", df['Site Name'].unique())
site_data = df[df['Site Name'] == selected_site].sort_values('Date')

fig = px.line(site_data, x='Date', y=param, title=f'{param} Trend at {selected_site}')
fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)
st.plotly_chart(fig, use_container_width=True)
import streamlit as st
import pandas as pd
import folium
from folium import CircleMarker, Circle
from folium.plugins import MarkerCluster
from branca.colormap import linear
from streamlit_folium import st_folium
import plotly.express as px

# ---------- Setup ----------
st.set_page_config(layout="wide", page_title="Water Quality Pro Dashboard")
st.title("💧 Water Quality Dashboard – Advanced View")

# ---------- Load Data ----------
df = pd.read_csv("INPUT_1.csv")
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude'])

# ---------- Sidebar Controls ----------
st.sidebar.markdown("## ⚙️ Controls")
with st.sidebar.expander("📦 Site & Filter", expanded=True):
    search_text = st.text_input("🔍 Search Site", "")
    filtered_sites = [s for s in all_sites if search_text.lower() in s.lower()]
    selected_site = st.selectbox("📌 Select Site", filtered_sites)

with st.sidebar.expander("🎯 Parameter Selection", expanded=True):
    param = st.selectbox("🧪 Select Parameter", numeric_cols)

with st.sidebar.expander("🎨 Theme", expanded=True):
    theme = st.radio("", ["Light", "Dark"])

numeric_cols = df.select_dtypes(include='number').columns.tolist()
param = st.sidebar.selectbox("🧪 Select Parameter", numeric_cols)
selected_site = st.sidebar.selectbox("📍 Select Site", df['Site Name'].unique())

# ---------- Gradient Color Map ----------
vmin, vmax = df[param].min(), df[param].max()
colormap = linear.YlOrRd_09.scale(vmin, vmax)
colormap.caption = f'{param} Scale'

# ---------- Map Construction ----------
st.subheader("🗺️ Interactive Parameter Map")

m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()],
               zoom_start=8, control_scale=True)

marker_cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    val = row[param]
    color = colormap(val)
    
    # Add radius and marker
    Circle(location=[row['Latitude'], row['Longitude']],
           radius=1000,
           color='blue',
           fill=True,
           fill_opacity=0.1).add_to(m)

    CircleMarker(location=[row['Latitude'], row['Longitude']],
                 radius=7,
                 color=color,
                 fill=True,
                 fill_opacity=0.9,
                 popup=folium.Popup(f"""
                     <b>Site:</b> {row['Site Name']}<br>
                     <b>Date:</b> {row['Date'].date()}<br>
                     <b>{param}:</b> {val:.2f}
                 """, max_width=300)).add_to(marker_cluster)

m.add_child(colormap)
st_folium(m, width=1100, height=500, returned_objects=[])

# ---------- Tabbed Graphs ----------
st.subheader("📊 Parameter Analysis – Trends & Averages")

site_df = df[df['Site Name'] == selected_site].copy()
site_df['Month'] = site_df['Date'].dt.to_period('M')
site_df['Year'] = site_df['Date'].dt.year

tab1, tab2, tab3 = st.tabs(["📈 Time Series", "📆 Monthly Avg", "📅 Yearly Avg"])

with tab1:
    fig1 = px.line(site_df, x='Date', y=param, title=f'{param} Over Time')
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    monthly = site_df.groupby('Month')[param].mean().reset_index()
    monthly['Month'] = monthly['Month'].astype(str)
    fig2 = px.bar(monthly, x='Month', y=param, title=f'Monthly Avg of {param}')
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    yearly = site_df.groupby('Year')[param].mean().reset_index()
    fig3 = px.bar(yearly, x='Year', y=param, title=f'Yearly Avg of {param}')
    st.plotly_chart(fig3, use_container_width=True)

# --- Searchable Site List ---
all_sites = df['Site Name'].unique().tolist()
search_text = st.sidebar.text_input("🔎 Search Site", "")

filtered_sites = [s for s in all_sites if search_text.lower() in s.lower()]
selected_site = st.sidebar.selectbox("📍 Select Site", filtered_sites)
# --- Download Filtered Site Data ---
site_filtered = df[df['Site Name'] == selected_site]

st.download_button(
    label="💾 Download This Site's Data",
    data=site_filtered.to_csv(index=False).encode('utf-8'),
    file_name=f"{selected_site.replace(' ', '_')}_data.csv",
    mime="text/csv"
)

