import streamlit as st
import pandas as pd
import folium
from folium import IFrame
from streamlit_folium import st_folium
import plotly.express as px
import base64
import io

# تنظیمات صفحه
st.set_page_config(page_title="نقشه تعاملی کیفیت آب", layout="wide")
st.title("💧 نقشه تعاملی کیفیت آب با پاپ‌آپ‌های نموداری")

# بارگذاری فایل CSV
uploaded_file = st.sidebar.file_uploader("📂 بارگذاری فایل CSV", type=["csv"])

if uploaded_file:
    # خواندن داده‌ها
    df = pd.read_csv(uploaded_file)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])

    # انتخاب پارامتر
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    param = st.sidebar.selectbox("🎯 انتخاب پارامتر", numeric_cols)

    # ایجاد نقشه
    m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()],
                   zoom_start=10, control_scale=True)

    # افزودن نقاط به نقشه
    for site_id in df['Site ID'].unique():
        site_data = df[df['Site ID'] == site_id]
        lat = site_data['Latitude'].iloc[0]
        lon = site_data['Longitude'].iloc[0]
        site_name = site_data['Site Name'].iloc[0]

        # نمودار سری زمانی
        fig = px.line(site_data, x='Date', y=param, title=f'{param} در ایستگاه {site_name}')
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))

        # تبدیل نمودار به HTML
        fig_html = fig.to_html(include_plotlyjs='cdn')
        iframe = IFrame(fig_html, width=500, height=350)
        popup = folium.Popup(iframe, max_width=500)

        # افزودن دایره به نقشه
        folium.Circle(
            location=[lat, lon],
            radius=1000,  # شعاع 1 کیلومتر
            color='blue',
            fill=True,
            fill_opacity=0.1
        ).add_to(m)

        # افزودن نشانگر با پاپ‌آپ
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.7,
            popup=popup
        ).add_to(m)

    # نمایش نقشه در Streamlit
    st_folium(m, width=1000, height=600)

else:
    st.info("لطفاً یک فایل CSV بارگذاری کنید.")
