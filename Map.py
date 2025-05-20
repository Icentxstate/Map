import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster
from branca.element import Template, MacroElement
import base64

# تنظیمات صفحه
st.set_page_config(page_title="داشبورد کیفیت آب", layout="wide")
st.title("💧 داشبورد تعاملی کیفیت آب")

# تابع برای افزودن پس‌زمینه لوگو
def set_background(image_file):
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

# قرار دادن لوگو (در صورت وجود فایل لوگو)
# set_background("logo.png")  # نام فایل لوگو را به دلخواه تغییر دهید

# آپلود فایل CSV
uploaded_file = st.sidebar.file_uploader("📂 بارگذاری فایل CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding='utf-8')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])

    required_cols = {'Latitude', 'Longitude', 'Date', 'Site ID', 'Site Name'}
    if not required_cols.issubset(df.columns):
        st.error(f"❌ فایل باید شامل ستون‌های زیر باشد: {required_cols}")
    else:
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        param = st.sidebar.selectbox("🎯 انتخاب پارامتر برای نمایش", numeric_cols)

        # فیلتر تاریخ
        start_date = df['Date'].min()
        end_date = df['Date'].max()
        date_range = st.sidebar.date_input("📅 فیلتر بر اساس تاریخ", [start_date, end_date])

        if len(date_range) == 2:
            df = df[(df['Date'] >= pd.to_datetime(date_range[0])) & (df['Date'] <= pd.to_datetime(date_range[1]))]

        # فیلتر محدوده پارامتر
        param_min = float(df[param].min())
        param_max = float(df[param].max())
        selected_range = st.sidebar.slider(f"🔍 محدوده {param}", param_min, param_max, (param_min, param_max))
        df = df[(df[param] >= selected_range[0]) & (df[param] <= selected_range[1])]

        # تابع رنگ‌بندی
        def get_color(val, vmin, vmax):
            norm = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
            norm = max(0, min(1, norm))
            return f'rgba({int(255*norm)}, {int(128*(1-norm))}, {int(255*(1-norm))}, 0.9)'

        vmin, vmax = df[param].min(), df[param].max()

        # تب‌ها
        tabs = st.tabs(["📍 نقشه", "📊 جدول", "📈 نمودار زمانی"])

        # تب نقشه
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

            # افزودن Legend
            def add_legend(m, param, vmin, vmax):
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

            add_legend(m, param, vmin, vmax)

            st.subheader(f"🗺️ نقشه {param}")
            st_folium(m, width=1000, height=600)

        # تب جدول
        with tabs[1]:
            st.subheader("📋 جدول داده‌ها")
            st.dataframe(df[['Site ID', 'Site Name', 'Date', param, 'Latitude', 'Longitude']])
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ دانلود داده‌های فیلترشده", csv, f"filtered_{param}.csv", "text/csv")

        # تب نمودار زمانی
        with tabs[2]:
            st.subheader("📈 نمودار سری زمانی")
            sites = df['Site Name'].unique().tolist()
            selected_site = st.selectbox("انتخاب سایت برای مشاهده نمودار زمانی", sites)

            site_df = df[df['Site Name'] == selected_site].sort_values('Date')

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(site_df['Date'], site_df[param], marker='o', linestyle='-')
            ax.set_title(f"{param} در طول زمان در سایت {selected_site}")
            ax.set_ylabel(param)
            ax.set_xlabel("تاریخ")
            ax.grid(True)
            st.pyplot(fig)

else:
    st.info("📌 لطفاً یک فایل CSV بارگذاری کنید تا شروع کنیم.")
