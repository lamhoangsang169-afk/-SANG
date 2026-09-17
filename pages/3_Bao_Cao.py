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

st.title("📈 Báo Cáo & Thống Kê Sản Lượng Chi Tiết")

# Bộ lọc thời gian chung
col1, col2 = st.columns(2)
now_vn = datetime.datetime.now(VN_TIMEZONE)
default_start = now_vn.date() - datetime.timedelta(days=7)

with col1:
    start_date = st.date_input("Từ ngày", value=default_start)
with col2:
    end_date = st.date_input("Đến ngày", value=now_vn.date())

# Lấy dữ liệu theo khoảng thời gian
df_report = get_production_logs_by_date_range(start_date, end_date)

if not df_report.empty:
    # Chia thành các mục (tabs) tách riêng biệt để dễ theo dõi
    tab1, tab2, tab3 = st.tabs(["📋 Nhật Ký Chi Tiết", "👤 Tổng Hợp Theo Nhân Sự", "📊 Tổng Hợp Theo Hạng Mục"])

    # Chuẩn hóa chung dataframe hiển thị
    base_df = df_report.copy()
    if "db_id" in base_df.columns:
        base_df = base_df.drop(columns=["db_id"])
    if "is_deleted" in base_df.columns:
        base_df = base_df.drop(columns=["is_deleted"])

    # Xác định cột hình ảnh
    img_col = None
    if "hinh_anh_url" in base_df.columns:
        img_col = "hinh_anh_url"
    elif "hinh_anh" in base_df.columns:
        img_col = "hinh_anh"

    rename_map = {
        "STT": "STT",
        "ngay": "Ngày",
        "thoi_gian": "Giờ",
        "nhan_su": "Nhân Sự",
        "hang_muc_cong_viec": "Hạng Mục Công Việc",
        "don_vi": "Đơn Vị",
        "so_luong": "Số Lượng",
        "he_so": "Hệ Số",
        "he_so_diem": "Hệ Số",
        "tong_diem": "Tổng Điểm",
        "ghi_chu": "Ghi Chú"
    }
    if img_col:
        rename_map[img_col] = "Hình Ảnh Minh Chứng"

    base_df = base_df.rename(columns=rename_map)

    # --- TAB 1: NHẬT KÝ CHI TIẾT ---
    with tab1:
        st.subheader("📋 Báo Cáo Nhật Ký Chi Tiết Từng Công Việc")
        
        desired_columns = [
            "STT", "Ngày", "Giờ", "Nhân Sự", 
            "Hạng Mục Công Việc", "Đơn Vị", 
            "Số Lượng", "Hệ Số", "Tổng Điểm", 
            "Ghi Chú", "Hình Ảnh Minh Chứng"
        ]
        exist_cols = [c for c in desired_columns if c in base_df.columns]
        
        st.dataframe(
            base_df[exist_cols],
            use_container_width=True,
            column_config={
                "Hình Ảnh Minh Chứng": st.column_config.ImageColumn("Hình Ảnh Minh Chứng", help="Ảnh minh chứng công việc")
            }
        )

    # --- TAB 2: TỔNG HỢP THEO NHÂN SỰ ---
    with tab2:
        st.subheader("👤 Thống Kê Sản Lượng Theo Từng Nhân Sự")
        if "Nhân Sự" in base_df.columns and "Tổng Điểm" in base_df.columns:
            staff_summary = base_df.groupby("Nhân Sự").agg({
                "Số Lượng": "sum",
                "Tổng Điểm": "sum"
            }).reset_index().sort_values(by="Tổng Điểm", ascending=False)
            
            st.dataframe(staff_summary, use_container_width=True)
        else:
            st.info("Không đủ dữ liệu để tổng hợp theo nhân sự.")

    # --- TAB 3: TỔNG HỢP THEO HẠNG MỤC ---
    with tab3:
        st.subheader("📊 Thống Kê Sản Lượng Theo Từng Hạng Mục Công Việc")
        if "Hạng Mục Công Việc" in base_df.columns and "Tổng Điểm" in base_df.columns:
            task_summary = base_df.groupby("Hạng Mục Công Việc").agg({
                "Số Lượng": "sum",
                "Tổng Điểm": "sum"
            }).reset_index().sort_values(by="Tổng Điểm", ascending=False)
            
            st.dataframe(task_summary, use_container_width=True)
        else:
            st.info("Không đủ dữ liệu để tổng hợp theo hạng mục.")

else:
    st.info("⚠️ Không tìm thấy dữ liệu báo cáo trong khoảng thời gian này.")
