import streamlit as st
import pandas as pd
import datetime
from utils import VN_TIMEZONE, compress_image_to_base64
from database import (
    supabase, get_staff_list_db, get_rules_df_db, 
    get_production_logs_db, add_production_log_db, 
    update_production_log_deleted_status, get_attendance_db
)

st.set_page_config(page_title="Nhập Sản Lượng", page_icon="📊", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ trước!")
    st.stop()

now_vn = datetime.datetime.now(VN_TIMEZONE)
today_str = str(now_vn.date())
st.subheader(f"📊 Nhập Sản Lượng ({today_str})")

staff_list = get_staff_list_db()
rules_df = get_rules_df_db()

att_df_check = get_attendance_db()
checked_in_set = set(att_df_check[att_df_check["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist()) if not att_df_check.empty else set()
active_staff = [s for s in staff_list if s in checked_in_set]

if not active_staff:
    st.warning("⚠️ Chưa có nhân sự nào Check-in (Vào ca). Vui lòng thực hiện Check-in ở mục Chấm công trước!")
else:
    with st.form("entry_form"):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1: ngay = st.date_input("Ngày làm việc", now_vn.date(), disabled=True)
        with f_col2: nhan_su = st.selectbox("Nhân sự thực hiện", ["--- Chọn ---"] + active_staff)
        with f_col3:
            raw_tasks = rules_df["Hạng Mục Công Việc"].tolist() if not rules_df.empty else []
            danh_sach_hang_muc = [str(t).strip() for t in raw_tasks if pd.notna(t) and str(t).strip()]
            hang_muc = st.selectbox("Hạng mục công việc", danh_sach_hang_muc)
            
        record_images = st.file_uploader("Tải ảnh đính kèm (Tối đa 4 ảnh)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        f_col4, f_col5 = st.columns(2)
        with f_col4: so_luong = st.number_input("Số lượng thực tế", min_value=0, value=0, step=1)
        with f_col5: ghi_chu = st.text_input("Ghi chú", "")
            
        if st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True):
            if nhan_su == "--- Chọn ---":
                st.error("⚠️ Vui lòng chọn nhân sự!")
            elif so_luong <= 0:
                st.error("⚠️ Số lượng phải lớn hơn 0!")
            else:
                row_rule = rules_df[rules_df["Hạng Mục Công Việc"] == hang_muc]
                he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
                don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
                tong_diem = so_luong * he_so
                
                # Hàm upload ảnh phụ trợ
                def upload_imgs(files):
                    if not supabase or not files: return ""
                    urls = []
                    for f in files[:4]:
                        try:
                            fname = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{f.name}"
                            supabase.storage.from_("production-images").upload(fname, f.getvalue(), {"content-type": f.type})
                            urls.append(f"{st.secrets['supabase']['SUPABASE_URL']}/storage/v1/object/public/production-images/{fname}")
                        except: pass
                    return ",".join(urls)

                img_urls = upload_imgs(record_images)
                add_production_log_db(today_str, datetime.datetime.now(VN_TIMEZONE).strftime("%H:%M:%S"), nhan_su, hang_muc, img_urls, don_vi, so_luong, he_so, tong_diem, ghi_chu)
                st.success(f"✅ Ghi nhận thành công cho **{nhan_su}**! Tổng điểm: **{tong_diem}**")
                st.rerun()

st.markdown("---")
st.subheader("Danh Sách Sản Lượng Gần Nhất")
input_df = get_production_logs_db(is_deleted=False, limit_rows=50)
if not input_df.empty:
    st.dataframe(input_df.drop(columns=["db_id", "Hình Ảnh"]), use_container_width=True, hide_index=True)
else:
    st.info("Chưa có dữ liệu sản lượng.")
