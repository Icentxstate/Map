import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Water Quality Dashboard", layout="wide")
st.title("💧 Water Quality Dashboard")

uploaded_file = st.sidebar.file_uploader("📂 Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding='latin1')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])

    required_cols = {'Latitude', 'Longitude', 'Date', 'Site ID', 'Site Name'}
    if not required_cols.issubset(df.columns):
        st.error(f"❌ Your file must contain: {required_cols}")
    else:
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        param = st.sidebar.selectbox("🎯 Parameter to map & plot", numeric_cols)

        # Colormap
        def get_color(val, vmin, vmax):
            norm = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
            norm = max(0, min(1, norm))
            return f'rgba({int(255*norm)}, {int(128*(1-norm))}, {int(255*(1-norm))}, 0.9)'

        vmin, vmax = df[param].min(), df[param].max()

        # --- Tabs Layout ---
        tabs = st.tabs(["📍 Map", "📊 Table", "📈 Time Series"])

        # -------- MAP TAB --------
        with tabs[0]:
            avg_lat = df['Latitude'].mean()
            avg_lon = df['Longitude'].mean()
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=8, control_scale=True)
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in df.iterrows():
                val = row[param]
                color = get_color(val, vmin, vmax)
                popup_html = f"""
                <b>Site:</b> {row['Site Name']}<br>
                <b>Date:</b> {row['Date'].date()}<br>
                <b>{param}:</b> {val}<br>
                <b>Location:</b> ({row['Latitude']:.4f}, {row['Longitude']:.4f})
                """
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_opacity=0.9,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(marker_cluster)

            st.subheader(f"🗺️ Map of {param}")
            st_folium(m, width=1000, height=600)

        # -------- TABLE TAB --------
        with tabs[1]:
            st.subheader("📋 Raw Data Table")
            st.dataframe(df[[ 'Site ID', 'Site Name', 'Date', param, 'Latitude', 'Longitude']])

        # -------- TIME SERIES TAB --------
        with tabs[2]:
            st.subheader("📈 Time Series Plot")
            sites = df['Site Name'].unique().tolist()
            selected_site = st.selectbox("Select Site to View Time Series", sites)

            site_df = df[df['Site Name'] == selected_site].sort_values('Date')

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(site_df['Date'], site_df[param], marker='o', linestyle='-')
            ax.set_title(f"{param} over Time at {selected_site}")
            ax.set_ylabel(param)
            ax.set_xlabel("Date")
            ax.grid(True)
            st.pyplot(fig)

else:
    st.info("📌 Please upload a CSV file to begin.")


---------------------------------------------------------------------------
def set_background(image_file):
    import base64
    with open(image_file, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-repeat: no-repeat;
            background-position: bottom right;
            background-size: 150px;
            background-attachment: fixed;
            opacity: 0.15;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("meadows_logo.png")
-------------------------------------------------------------------------------
def add_legend(m, param, vmin, vmax):
    from branca.element import Template, MacroElement
    template = f"""
    <!DOCTYPE html>
    <div style="position: fixed;
                bottom: 50px; left: 50px; width: 180px; height: 80px;
                background-color: white;
                z-index:9999; font-size:14px;
                border:2px solid grey;
                padding: 10px;">
        <b>{param} Scale</b><br>
        <i style="background: rgba(255,128,255,0.9); width: 20px; height: 10px; float: left; margin-right: 8px;"></i> Low<br>
        <i style="background: rgba(255,255,128,0.9); width: 20px; height: 10px; float: left; margin-right: 8px;"></i> Medium<br>
        <i style="background: rgba(255,0,0,0.9); width: 20px; height: 10px; float: left; margin-right: 8px;"></i> High
    </div>
    """
    macro = MacroElement()
    macro._template = Template(template)
    m.get_root().add_child(macro)
-----------------------------------------------------------------------------------------
# --- Date Filter ---
start_date = df['Date'].min()
end_date = df['Date'].max()
date_range = st.sidebar.date_input("📅 Filter by Date", [start_date, end_date])

if len(date_range) == 2:
    df = df[(df['Date'] >= pd.to_datetime(date_range[0])) & (df['Date'] <= pd.to_datetime(date_range[1]))]

# --- Parameter Range Filter ---
param_min = float(df[param].min())
param_max = float(df[param].max())
selected_range = st.sidebar.slider(f"🔍 {param} Range Filter", param_min, param_max, (param_min, param_max))
df = df[(df[param] >= selected_range[0]) & (df[param] <= selected_range[1])]
----------------------------------------------------------------------------------------------
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Filtered Data", csv, f"filtered_{param}.csv", "text/csv")



