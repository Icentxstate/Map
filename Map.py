import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster
from branca.colormap import LinearColormap

# تنظیمات صفحه
st.set_page_config(page_title="داشبورد کیفیت آب", layout="wide")
st.title("💧 داشبورد تعاملی کیفیت آب")

# بارگذاری فایل CSV
uploaded_file = st.sidebar.file_uploader("📂 بارگذاری فایل CSV", type=["csv"])

if uploaded_file:
    # خواندن فایل CSV
    df = pd.read_csv(uploaded_file, encoding='utf-8')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])

    required_cols = {'Latitude', 'Longitude', 'Date', 'Site ID', 'Site Name'}
    if not required_cols.issubset(df.columns):
        st.error(f"❌ فایل باید شامل ستون‌های زیر باشد: {required_cols}")
    else:
        # انتخاب پارامتر
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        param = st.sidebar.selectbox("🎯 انتخاب پارامتر برای نمایش", numeric_cols)

        # انتخاب تاریخ
        unique_dates = df['Date'].dropna().dt.date.unique()
        selected_date = st.sidebar.selectbox("📅 انتخاب تاریخ", sorted(unique_dates))

        # فیلتر داده‌ها بر اساس تاریخ انتخاب‌شده
        df_filtered = df[df['Date'].dt.date == selected_date]

        if df_filtered.empty:
            st.warning("هیچ داده‌ای برای تاریخ انتخاب‌شده موجود نیست.")
        else:
            # محاسبه حداقل و حداکثر مقدار پارامتر
            vmin = df_filtered[param].min()
            vmax = df_filtered[param].max()

            # ایجاد نقشه
            m = folium.Map(control_scale=True)
            marker_cluster = MarkerCluster().add_to(m)

            # تعریف colormap
            colormap = LinearColormap(colors=['blue', 'green', 'yellow', 'red'], vmin=vmin, vmax=vmax)
            colormap.caption = f"{param} Scale"

            # افزودن نشانگرها به نقشه
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

            # تنظیم نمای نقشه برای نمایش تمام نشانگرها
            sw = df_filtered[['Latitude', 'Longitude']].min().values.tolist()
            ne = df_filtered[['Latitude', 'Longitude']].max().values.tolist()
            m.fit_bounds([sw, ne])

            # افزودن colormap به نقشه
            m.add_child(colormap)

            # نمایش نقشه در Streamlit
            st.subheader(f"🗺️ نقشه {param} در تاریخ {selected_date}")
            st_data = st_folium(m, width=1000, height=600)

            # نمایش جدول داده‌ها
            st.subheader("📋 جدول داده‌ها")
            st.dataframe(df_filtered[['Site ID', 'Site Name', 'Date', param, 'Latitude', 'Longitude']])

            # نمودار سری زمانی برای ایستگاه انتخاب‌شده
            st.subheader("📈 نمودار سری زمانی")
            sites = df_filtered['Site Name'].unique().tolist()
            selected_site = st.selectbox("انتخاب ایستگاه برای مشاهده نمودار زمانی", sites)

            site_df = df[df['Site Name'] == selected_site].sort_values('Date')

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(site_df['Date'], site_df[param], marker='o', linestyle='-')
            ax.set_title(f"{param} در طول زمان در ایستگاه {selected_site}")
            ax.set_ylabel(param)
            ax.set_xlabel("تاریخ")
            ax.grid(True)
            st.pyplot(fig)

else:
    st.info("📌 لطفاً یک فایل CSV بارگذاری کنید تا شروع کنیم.")
