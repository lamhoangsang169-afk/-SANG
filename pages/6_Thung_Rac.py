import streamlit as st
import pandas as pd
from database import get_production_logs_db, update_production_log_deleted_status, supabase

st.set_page_config(page_title="Thùng Rác", page_icon="🗑️", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ trước!")
    st.stop()

def get_user_role(identifier):
    if not identifier or supabase is None: return "Staff"
    if str(identifier).strip().lower() == "lamhoangsang169@gmail.com": return "Admin"
    try:
        res = supabase.table("user_accounts").select("role").eq("name", identifier).execute()
        if res.data: return res.data[0].get("role", "Staff")
    except: pass
    return "Staff"

current_user_role = get_user_role(st.session_state.user_identifier)

col_trash_h1, col_trash_h2 = st.columns([3, 1])
with col_trash_h1:
    st.subheader("🗑️ Thùng Rác: Bản Ghi Sản Lượng Đã Xóa")
with col_trash_h2:
    if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_trash"):
        st.cache_data.clear()
        st.rerun()

if current_user_role != "Admin":
    st.warning("🔒 Tính năng thùng rác chỉ dành cho Quản trị viên (Admin).")
else:
    trash_df = get_production_logs_db(is_deleted=True, limit_rows=100)
    if not trash_df.empty:
        with st.form("trash_form"):
            for idx, row in trash_df.iterrows():
                st.markdown(f'<div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;"><b>STT: {row["STT"]}</b> | 📅 {row["Ngày"]} | 👤 <b>{row["Nhân Sự"]}</b> | 📌 {row["Hạng Mục Công Việc"]} ({row["Số Lượng"]} {row["Đơn Vị"]})</div>', unsafe_allow_html=True)
                trash_df.loc[idx, "Chọn"] = st.checkbox(f"Chọn sản lượng STT {row['STT']}", key=f"t_{row['db_id']}")
                
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📥 Khôi Phục Đã Chọn", use_container_width=True):
                    ids = trash_df[trash_df["Chọn"] == True]["db_id"].tolist()
                    if ids:
                        update_production_log_deleted_status(ids, False)
                        st.success("Đã khôi phục thành công!")
                        st.rerun()
            with c2:
                if st.form_submit_button("🔥 Xóa Vĩnh Viễn Đã Chọn", use_container_width=True, type="primary"):
                    ids = trash_df[trash_df["Chọn"] == True]["db_id"].tolist()
                    if ids and supabase:
                        for db_id in ids:
                            supabase.table("production_logs").delete().eq("id", db_id).execute()
                        st.cache_data.clear()
                        st.success("Đã xóa vĩnh viễn thành công!")
                        st.rerun()
    else:
        st.info("Thùng rác sản lượng đang trống.")
