import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster
from branca.colormap import LinearColormap

# Set page configuration
st.set_page_config(page_title="Water Quality Dashboard", layout="wide")
st.title("💧 Interactive Water Quality Dashboard")

# Upload CSV file
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV File", type=["csv"])

if uploaded_file:
    # Read CSV file
    df = pd.read_csv(uploaded_file, encoding='utf-8')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])

    required_cols = {'Latitude', 'Longitude', 'Date', 'Site ID', 'Site Name'}
    if not required_cols.issubset(df.columns):
        st.error(f"❌ The file must contain the following columns: {required_cols}")
    else:
        # Select parameter
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        param = st.sidebar.selectbox("🎯 Select Parameter to Display", numeric_cols)

        # Select date
        unique_dates = df['Date'].dropna().dt.date.unique()
        selected_date = st.sidebar.selectbox("📅 Select Date", sorted(unique_dates))

        # Filter data by selected date
        df_filtered = df[df['Date'].dt.date == selected_date]

        if df_filtered.empty:
            st.warning("No data available for the selected date.")
        else:
            # Calculate min and max values for the parameter
            vmin = df_filtered[param].min()
            vmax = df_filtered[param].max()

            # Create map
            avg_lat = df_filtered['Latitude'].mean()
            avg_lon = df_filtered['Longitude'].mean()
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=8, control_scale=True)
            marker_cluster = MarkerCluster().add_to(m)

            # Define colormap
            colormap = LinearColormap(colors=['blue', 'green', 'yellow', 'red'], vmin=vmin, vmax=vmax)
            colormap.caption = f"{param} Scale"

            # Add markers to map
            for _, row in df_filtered.iterrows():
                val = row[param]
                color = colormap(val)
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

            # Add colormap to map
            m.add_child(colormap)

            # Display map in Streamlit
            st.subheader(f"🗺️ Map of {param} on {selected_date}")
            st_data = st_folium(m, width=1000, height=600)

            # Display data table
            st.subheader("📋 Data Table")
            st.dataframe(df_filtered[['Site ID', 'Site Name', 'Date', param, 'Latitude', 'Longitude']])

            # Time series plot for selected site
            st.subheader("📈 Time Series Plot")
            sites = df_filtered['Site Name'].unique().tolist()
            selected_site = st.selectbox("Select Site for Time Series Plot", sites)

            site_df = df[df['Site Name'] == selected_site].sort_values('Date')

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(site_df['Date'], site_df[param], marker='o', linestyle='-')
            ax.set_title(f"{param} Over Time at {selected_site}")
            ax.set_ylabel(param)
            ax.set_xlabel("Date")
            ax.grid(True)
            st.pyplot(fig)

else:
    st.info("📌 Please upload a CSV file to get started.")
