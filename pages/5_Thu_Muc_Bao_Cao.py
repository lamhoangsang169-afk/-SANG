import streamlit as st
import pandas as pd
from database import get_export_reports_db, update_export_report_deleted_status, supabase

st.set_page_config(page_title="Thư Mục Báo Cáo", page_icon="📁", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ trước!")
    st.stop()

col_fold_h1, col_fold_h2 = st.columns([3, 1])
with col_fold_h1:
    st.subheader("📁 Thư Mục Lưu Trữ Báo Cáo")
with col_fold_h2:
    if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_folder"):
        st.cache_data.clear()
        st.rerun()

reports_df = get_export_reports_db(is_deleted=False)
if not reports_df.empty:
    with st.form("reports_folder_form"):
        for idx, row in reports_df.iterrows():
            st.markdown(f'<div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;"><b>STT: {row["STT"]}</b> &nbsp;|&nbsp; 📁 File: <b>{row["Tên File"]}</b><br>📅 Ngày tạo: {row["Ngày Tạo"]}<br>🔗 <a href="{row["Đường Dẫn URL"]}" target="_blank">Mở liên kết trực tiếp</a></div>', unsafe_allow_html=True)
            reports_df.loc[idx, "Chọn"] = st.checkbox(f"Chọn báo cáo STT {row['STT']}", key=f"rep_{row['db_id']}")
            st.markdown("---")
        if st.form_submit_button("🗑️ Chuyển Các Báo Cáo Đã Chọn Vào Thùng Rác", use_container_width=True):
            selected_ids = reports_df[reports_df["Chọn"] == True]["db_id"].tolist()
            if selected_ids:
                update_export_report_deleted_status(selected_ids, True)
                st.success("Đã chuyển vào thùng rác thành công!")
                st.rerun()
            else:
                st.warning("Vui lòng tích chọn báo cáo cần chuyển!")
else:
    st.info("Thư mục báo cáo đang trống.")
