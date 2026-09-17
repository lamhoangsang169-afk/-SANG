import streamlit as st
import pandas as pd
import datetime
from database import get_production_logs_by_date_range, get_staff_list_db
from utils import VN_TIMEZONE

st.set_page_config(page_title="Báo Cáo Sản Lượng", page_icon="📈", layout="wide")

# Kiểm tra đăng nhập
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ (`app.py`) trước khi sử dụng hệ thống!")
    st.stop()

st.title("📈 Báo Cáo & Thống Kê Sản Lượng")

# Bộ lọc thời gian và nhân sự (Giống hệt bản cũ)
col1, col2, col3 = st.columns(3)

now_vn = datetime.datetime.now(VN_TIMEZONE)
default_start = now_vn.date() - datetime.timedelta(days=7)

with col1:
    start_date = st.date_input("Từ ngày", value=default_start)
with col2:
    end_date = st.date_input("Đến ngày", value=now_vn.date())
with col3:
    staff_list = ["Tất cả"] + get_staff_list_db()
    selected_staff = st.selectbox("Lọc theo nhân sự", staff_list)

# Lấy dữ liệu theo khoảng thời gian
df_report = get_production_logs_by_date_range(start_date, end_date)

if not df_report.empty:
    # Lọc theo nhân sự nếu chọn cụ thể
    if selected_staff != "Tất cả":
        df_report = df_report[df_report["nhan_su"] == selected_staff]

    if not df_report.empty:
        # Thống kê tổng quan dạng métrics
        total_records = len(df_report)
        total_quantity = df_report["so_luong"].sum() if "so_luong" in df_report.columns else 0
        total_points = df_report["tong_diem"].sum() if "tong_diem" in df_report.columns else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng số dòng báo cáo", f"{total_records} bản ghi")
        m2.metric("Tổng số lượng", f"{total_quantity:,.2f}")
        m3.metric("Tổng điểm tích lũy", f"{total_points:,.2f}")

        st.markdown("---")
        st.subheader("📋 Chi Tiết Báo Cáo Sản Lượng")

        # Chuẩn hóa hiển thị bảng gọn gàng, ẩn các cột kỹ thuật
        display_df = df_report.copy()
        if "id" in display_df.columns:
            display_df = display_df.drop(columns=["id"])
        if "is_deleted" in display_df.columns:
            display_df = display_df.drop(columns=["is_deleted"])
        if "hinh_anh_url" in display_df.columns:
            display_df = display_df.drop(columns=["hinh_anh_url"])

        # Đổi tên cột tiếng Việt trực quan
        rename_map = {
            "ngay": "Ngày",
            "thoi_gian": "Giờ",
            "nhan_su": "Nhân Sự",
            "hang_muc_cong_viec": "Hạng Mục Công Việc",
            "don_vi": "Đơn Vị",
            "so_luong": "Số Lượng",
            "he_so": "Hệ Số",
            "tong_diem": "Tổng Điểm",
            "ghi_chu": "Ghi Chú",
            "hinh_anh": "Hình Ảnh"
        }
        display_df = display_df.rename(columns=rename_map)

        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "Hình Ảnh": st.column_config.ImageColumn("Hình Ảnh Minh Chứng", help="Ảnh đính kèm công việc")
            }
        )
    else:
        st.info("⚠️ Không có dữ liệu sản lượng nào phù hợp với bộ lọc đã chọn.")
else:
    st.info("⚠️ Không tìm thấy dữ liệu trong khoảng thời gian này.")
