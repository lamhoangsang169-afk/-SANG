import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from database import get_production_logs_by_date_range, get_staff_list_db

st.set_page_config(page_title="Báo Cáo & Biểu Đồ", page_icon="📈", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ trước!")
    st.stop()

st.subheader("📈 Báo Cáo & Biểu Đồ Sản Lượng")
col1, col2 = st.columns(2)
start_date = col1.date_input("Từ ngày", datetime.date.today().replace(day=1))
end_date = col2.date_input("Đến ngày", datetime.date.today())

input_df = get_production_logs_by_date_range(start_date, end_date)
staff_list = get_staff_list_db()

if not input_df.empty:
    summary = input_df.groupby("Nhân Sự").agg(Tổng_Số_Lượng=("Số Lượng", "sum"), Tổng_Điểm=("Tổng Điểm", "sum")).reset_index()
    summary = summary[summary["Nhân Sự"].isin(staff_list)]
    total_pts = summary["Tổng_Điểm"].sum()
    summary["Tỷ_Lệ"] = summary["Tổng_Điểm"].apply(lambda x: x / total_pts if total_pts > 0 else 0)
    
    st.dataframe(summary.style.format({"Tổng_Điểm": "{:,.1f}", "Tỷ_Lệ": "{:.2%}"}), use_container_width=True, hide_index=True)
    
    fig = px.pie(summary, names="Nhân Sự", values="Tổng_Điểm", hole=0.3)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Không có dữ liệu trong khoảng thời gian này.")
