import streamlit as st
import pandas as pd
import folium
import geopandas as gpd
from folium import CircleMarker, Circle
from folium.plugins import MarkerCluster
from branca.colormap import linear
from streamlit_folium import st_folium
import plotly.express as px

# ---------- Page Config ----------
st.set_page_config(page_title="Water Quality Dashboard", layout="wide")

# ---------- Theme ----------
theme = st.sidebar.radio("Theme", ["Light", "Dark", "Green-Blue"])
if theme == "Dark":
    bg_color, text_color, card_bg = "#2b2b2b", "#f0f0f0", "#3b3b3b"
elif theme == "Green-Blue":
    bg_color, text_color, card_bg = "#e0f7fa", "#004d40", "#b2dfdb"
else:
    bg_color, text_color, card_bg = "#f7f9fa", "#222", "#ffffff"

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

# ---------- Load CSV ----------
try:
    df = pd.read_csv("INPUT_1.csv")
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])
except Exception as e:
    st.error(f"❌ Could not load INPUT_1.csv: {e}")
    st.stop()

# ---------- Load Shapefile ----------
try:
    watershed_gdf = gpd.read_file("Watershed.shp")
    watershed_gdf = watershed_gdf.to_crs(epsg=4326)
except Exception as e:
    st.warning(f"⚠️ Could not load shapefile: {e}")
    watershed_gdf = None

# ---------- Sidebar ----------
st.sidebar.markdown("## Controls")
numeric_cols = [col for col in df.select_dtypes(include='number').columns if col != 'Site ID']
param = st.sidebar.selectbox("Select Parameter", numeric_cols)
all_sites = df['Site Name'].unique().tolist()

# ---------- Map ----------
st.subheader("🗺️ Average Value Map by Site")
grouped = df.groupby('Site Name')
avg_df = grouped[param].mean().reset_index()
avg_df = avg_df.merge(df[['Site Name', 'Latitude', 'Longitude']].drop_duplicates(), on='Site Name')

vmin, vmax = avg_df[param].min(), avg_df[param].max()
if pd.isna(vmin) or pd.isna(vmax) or vmin == vmax:
    st.warning(f"Cannot render colormap for parameter: {param}")
    st.stop()

colormap = linear.YlGnBu_09.scale(vmin, vmax)
colormap.caption = f"{param} Average Scale"

m = folium.Map(zoom_start=8, control_scale=True)
bounds = [[df['Latitude'].min(), df['Longitude'].min()], [df['Latitude'].max(), df['Longitude'].max()]]
m.fit_bounds(bounds)

# Add shapefile layer first
if watershed_gdf is not None:
    folium.GeoJson(
        watershed_gdf,
        name="Watershed",
        style_function=lambda x: {
            'fillColor': '#228B22',
            'color': '#004d00',
            'weight': 2,
            'fillOpacity': 0.25
        },
        highlight_function=lambda x: {
            'color': '#000000',
            'weight': 3,
            'fillOpacity': 0.35
        },
        tooltip=folium.GeoJsonTooltip(fields=[watershed_gdf.columns[0]])
    ).add_to(m)

marker_cluster = MarkerCluster().add_to(m)

# Add markers
for _, row in avg_df.iterrows():
    val, site_name, lat, lon = row[param], row['Site Name'], row['Latitude'], row['Longitude']
    site_data = df[df['Site Name'] == site_name]
    try:
        color = colormap(val)
    except:
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
                 tooltip=site_name,
                 popup=folium.Popup(popup_content, max_width=300)).add_to(marker_cluster)

m.add_child(colormap)
clicked = st_folium(m, use_container_width=True)

# ---------- Determine Clicked Site ----------
clicked_site = None
if clicked and clicked.get("last_object_clicked"):
    lat = clicked["last_object_clicked"]["lat"]
    lon = clicked["last_object_clicked"]["lng"]
    df['distance'] = ((df['Latitude'] - lat)**2 + (df['Longitude'] - lon)**2)**0.5
    clicked_site = df.loc[df['distance'].idxmin()]['Site Name']

# ---------- Site Selector ----------
selected_site = st.sidebar.selectbox("Select Site", all_sites, index=all_sites.index(clicked_site) if clicked_site in all_sites else 0)

# ---------- Data Analysis ----------
site_df = df[df['Site Name'] == selected_site].copy()
site_df['Month'] = site_df['Date'].dt.to_period('M')
site_df['Year'] = site_df['Date'].dt.year

# ---------- Summary Cards ----------
total_sites = df['Site ID'].nunique()
date_range = f"{df['Date'].min().date()} → {df['Date'].max().date()}"

st.markdown(f"""
<div class="card-container">
    <div class="card"><h2>{total_sites}</h2><p>Total Sites</p></div>
    <div class="card"><h2>{date_range}</h2><p>Date Range</p></div>
    <div class="card"><h2>{param}</h2><p>Selected Parameter</p></div>
</div>
""", unsafe_allow_html=True)

# ---------- Tabs ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Time Series", "📊 Monthly Avg", "📅 Yearly Avg", "🔁 Compare Params", "🧮 Correlation Matrix"])

with tab1:
    fig1 = px.line(site_df, x='Date', y=param, title=f'{param} Over Time at {selected_site}')
    st.plotly_chart(fig1, use_container_width=True)
    fig_box = px.box(site_df, y=param, title=f'{param} Distribution at {selected_site}')
    st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    monthly = site_df.groupby('Month')[param].mean().reset_index()
    monthly['Month'] = monthly['Month'].astype(str)
    fig2 = px.bar(monthly, x='Month', y=param, title=f'Monthly Average of {param}')
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    yearly = site_df.groupby('Year')[param].mean().reset_index()
    fig3 = px.bar(yearly, x='Year', y=param, title=f'Yearly Average of {param}')
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    other_params = [col for col in numeric_cols if col != param]
    param2 = st.selectbox("Compare With", other_params)
    scatter_df = site_df[[param, param2]].dropna()
    if scatter_df.empty:
        st.warning("Not enough data to plot.")
    else:
        fig4 = px.scatter(scatter_df, x=param2, y=param, title=f'{param} vs {param2}')
        st.plotly_chart(fig4, use_container_width=True)

with tab5:
    st.write(f"Correlation Matrix for site: {selected_site}")
    corr_df = site_df[numeric_cols].corr()
    if corr_df.isnull().all().all():
        st.warning("⚠️ No valid correlation values.")
    else:
        fig_corr = px.imshow(corr_df, text_auto=True, aspect="auto", color_continuous_scale="RdBu", zmin=-1, zmax=1)
        st.plotly_chart(fig_corr, use_container_width=True)

# ---------- Download ----------
st.download_button(
    label="📥 Download Site Data",
    data=site_df.to_csv(index=False).encode('utf-8'),
    file_name=f"{selected_site.replace(' ', '_')}_data.csv",
    mime="text/csv"
)
