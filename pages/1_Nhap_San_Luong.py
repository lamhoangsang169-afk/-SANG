import streamlit as st
import pandas as pd
import datetime
from database import (
    supabase, get_staff_df_db, get_rules_df_db, 
    get_production_logs_db, add_production_log_db
)
from utils import compress_image_to_base64, VN_TIMEZONE

st.set_page_config(page_title="Nhập Sản Lượng", page_icon="📊", layout="wide")

# Kiểm tra đăng nhập
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ (`app.py`) trước khi sử dụng hệ thống!")
    st.stop()

st.title("📥 Nhập Sản Lượng Công Việc")

# Lấy dữ liệu cơ sở từ Database
staff_df = get_staff_df_db()
rules_df = get_rules_df_db()
logs_df = get_production_logs_db(is_deleted=False, limit_rows=50)

# An toàn kiểm tra chấm công để lọc nhân sự đang làm việc
try:
    att_res = supabase.table("attendance").select("*").execute()
    att_df_check = pd.DataFrame(att_res.data) if att_res.data else pd.DataFrame()
except Exception:
    att_df_check = pd.DataFrame()

if not att_df_check.empty and "Giờ Ra Ca" in att_df_check.columns and "Nhân Sự" in att_df_check.columns:
    checked_in_set = set(att_df_check[att_df_check["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist())
else:
    checked_in_set = set()

staff_list = staff_df["name"].tolist() if not staff_df.empty and "name" in staff_df.columns else []

if not staff_list:
    st.error("⚠️ Không tìm thấy danh sách nhân sự! Vui lòng kiểm tra lại bảng nhân sự trong cơ sở dữ liệu.")
    st.stop()

# Form nhập liệu sản lượng
with st.form("production_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        now_vn = datetime.datetime.now(VN_TIMEZONE)
        ngay = st.date_input("Ngày thực hiện", value=now_vn.date())
        gio = st.time_input("Giờ thực hiện", value=now_vn.time())
        
        nhan_su = st.selectbox("Nhân sự thực hiện", staff_list)
        
        # Cảnh báo nếu nhân sự chưa chấm công vào ca
        if nhan_su not in checked_in_set:
            st.warning(f"⚠️ Lưu ý: Nhân sự **{nhan_su}** chưa bấm 'Vào Ca' ở trang Chấm Công!")

    with col2:
        hang_muc_list = rules_df["hang_muc_cong_viec"].tolist() if not rules_df.empty and "hang_muc_cong_viec" in rules_df.columns else ["Mặc định"]
        hang_muc = st.selectbox("Hạng mục công việc", hang_muc_list)
        
        so_luong = st.number_input("Số lượng", min_value=0.0, step=1.0, value=1.0)
        
        # Tự động lấy hệ số theo hạng mục
        he_so = 1.0
        don_vi = "Cái"
        if not rules_df.empty and "hang_muc_cong_viec" in rules_df.columns:
            rule_row = rules_df[rules_df["hang_muc_cong_viec"] == hang_muc]
            if not rule_row.empty:
                he_so = float(rule_row.iloc[0].get("he_so", 1.0))
                don_vi = str(rule_row.iloc[0].get("don_vi", "Cái"))

        st.info(f"📌 Đơn vị: **{don_vi}** | Hệ số định mức: **{he_so}**")
        
        uploaded_image = st.file_uploader("Đính kèm hình ảnh minh chứng (nếu có)", type=["jpg", "jpeg", "png"])

    ghi_chu = st.text_area("Ghi chú thêm", placeholder="Nhập ghi chú chi tiết công việc...")
    
    submit_btn = st.form_submit_button("🚀 Ghi Nhận Sản Lượng", use_container_width=True)

    if submit_btn:
        # Xử lý nén ảnh nếu có
        img_base64 = compress_image_to_base64(uploaded_image) if uploaded_image else ""
        tong_diem = round(so_luong * he_so, 2)
        
        # Thêm vào database
        add_production_log_db(
            ngay=str(ngay),
            gio=str(gio),
            nhan_su=nhan_su,
            hang_muc=hang_muc,
            hinh_anh=img_base64,
            don_vi=don_vi,
            so_luong=so_luong,
            he_so=he_so,
            tong_diem=tong_diem,
            ghi_chu=ghi_chu
        )
        st.success(f"🎉 Đã ghi nhận thành công sản lượng cho **{nhan_su}**! Tổng điểm: **{tong_diem}**")

st.markdown("---")
st.subheader("📋 Nhật Ký Sản Lượng Gần Đây")
if not logs_df.empty:
    st.dataframe(logs_df, use_container_width=True)
else:
    st.info("Chưa có dữ liệu sản lượng nào được ghi nhận.")
