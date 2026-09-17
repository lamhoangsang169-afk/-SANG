import streamlit as st
import pandas as pd
import datetime
from utils import VN_TIMEZONE
from database import (
    supabase, 
    get_production_logs_db, 
    get_attendance_db, 
    upload_multiple_images_to_storage, 
    add_production_log_db, 
    update_production_log_deleted_status
)

def render(current_user_role, user_perms):
    now_vn = datetime.datetime.now(VN_TIMEZONE)
    today_str = str(now_vn.date())
    
    st.subheader(f"1. Nhập Sản Lượng ({today_str})")

    if current_user_role != "Admin" and not user_perms.get("perm_input", False):
        st.info("👁️ Tài khoản của bạn đang ở chế độ **Chỉ xem**. Bạn có thể theo dõi bảng danh sách bên dưới nhưng không được phép thêm hoặc chỉnh sửa dữ liệu.")
    else:
        att_df_check = get_attendance_db()
        checked_in_set = set()
        if not att_df_check.empty:
            checked_in_set = set(att_df_check[att_df_check["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist())

        active_staff = [s for s in st.session_state.staff_list if s in checked_in_set]

        if not active_staff:
            st.warning("⚠️ Hiện tại chưa có nhân sự nào **Check-in (Vào ca)** hoặc các ca trước chưa kết thúc. Vui lòng thực hiện Check-in trước khi nhập sản lượng!")
        else:
            req_img = st.session_state.get("require_image", True)
            req_qty = st.session_state.get("require_quantity", True)
            
            with st.form("entry_form"):
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1: st.date_input("Ngày làm việc", now_vn.date(), disabled=True)
                with f_col2:
                    staff_options = ["--- Vui lòng chọn nhân sự ---"] + active_staff
                    nhan_su = st.selectbox("Nhân sự thực hiện", staff_options)
                with f_col3:
                    raw_tasks = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else []
                    danh_sach_hang_muc = [str(t).strip() for t in raw_tasks if pd.notna(t) and str(t).strip() and str(t).strip().lower() not in ["nan", "none"]]
                    hang_muc = st.selectbox("Hạng mục công việc", danh_sach_hang_muc)
                    
                record_images = st.file_uploader("Tải ảnh đính kèm (Tối đa 4 ảnh)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="record_img")
                        
                f_col4, f_col5 = st.columns(2)
                with f_col4: so_luong = st.number_input("Số lượng thực tế", min_value=0, value=0, step=1)
                with f_col5: ghi_chu = st.text_input("Ghi chú", "")
                    
                submitted = st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True)

                if submitted:
                    is_valid = True
                    cleaned_hang_muc = str(hang_muc).strip()
                    cleaned_ghi_chu = str(ghi_chu).strip()

                    if nhan_su == "--- Vui lòng chọn nhân sự ---":
                        is_valid = False
                        st.session_state["form_msg"] = ("error", "⚠️ Vui lòng chọn đúng tên nhân sự thực hiện!")
                    elif req_img and not record_images: 
                        is_valid = False
                        st.session_state["form_msg"] = ("error", "⚠️ Vui lòng tải lên ảnh đính kèm!")
                    elif req_qty and so_luong <= 0: 
                        is_valid = False
                        st.session_state["form_msg"] = ("error", "⚠️ Số lượng thực tế phải lớn hơn 0!")
                    elif record_images and len(record_images) > 4:
                        is_valid = False
                        st.session_state["form_msg"] = ("error", "⚠️ Bạn chỉ được phép đính kèm tối đa 4 ảnh!")
                    elif "công việc phát sinh" in cleaned_hang_muc.lower() and not cleaned_ghi_chu:
                        is_valid = False
                        st.session_state["form_msg"] = ("error", "⚠️ Bắt buộc phải nhập nội dung vào phần Ghi chú khi chọn 'Công việc phát sinh'!")

                    if is_valid:
                        row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
                        he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
                        don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
                        tong_diem = so_luong * he_so
                        
                        img_urls = upload_multiple_images_to_storage(record_images) if record_images else ""
                        current_time_str = datetime.datetime.now(VN_TIMEZONE).strftime("%H:%M:%S")
                        
                        add_production_log_db(today_str, current_time_str, nhan_su, hang_muc, img_urls, don_vi, so_luong, he_so, tong_diem, ghi_chu)
                        st.session_state["form_msg"] = ("success", f"✅ Ghi nhận thành công cho **{nhan_su}**! Tổng điểm: **{tong_diem} điểm**")
                        st.rerun()

            if "form_msg" in st.session_state:
                m_type, m_text = st.session_state["form_msg"]
                if m_type == "success": st.success(m_text)
                else: st.error(m_text)
                del st.session_state["form_msg"]

    st.markdown("---")
    col_title_1, col_title_2 = st.columns([3, 1])
    with col_title_1:
        st.subheader("Danh Sách Sản Lượng & Hình Ảnh")
    with col_title_2:
        if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_input"):
            st.cache_data.clear()
            st.rerun()
    
    input_df = get_production_logs_db(is_deleted=False, limit_rows=150)
    if not input_df.empty:
        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([0.9, 1.2, 0.9, 0.9, 0.8])
        
        with f_col1:
            all_dates = ["Tất cả"] + sorted(input_df["Ngày"].unique().tolist())
            default_index = all_dates.index(today_str) if today_str in all_dates else 0
            filter_date = st.selectbox("Lọc theo Ngày", all_dates, index=default_index)
            count_by_date = len(input_df) if filter_date == "Tất cả" else len(input_df[input_df["Ngày"] == filter_date])
            st.markdown(f"<small style='color: #1d4ed8; font-weight: bold;'>📅 Ngày này có: {count_by_date} bản ghi</small>", unsafe_allow_html=True)
            
        with f_col2:
            enable_hour_filter = st.checkbox("Lọc theo Giờ", value=False)
            if enable_hour_filter:
                t_sub1, t_sub2 = st.columns(2)
                with t_sub1: start_t = st.time_input("Từ", datetime.time(7, 30), label_visibility="collapsed")
                with t_sub2: end_t = st.time_input("Đến", datetime.time(17, 0), label_visibility="collapsed")
            else:
                start_t, end_t = None, None
            
        with f_col3:
            all_staff = ["Tất cả"] + sorted(input_df["Nhân Sự"].unique().tolist())
            filter_staff = st.selectbox("Lọc theo Nhân Sự", all_staff)
            
        temp_filtered_df = input_df.copy()
        if filter_date != "Tất cả": temp_filtered_df = temp_filtered_df[temp_filtered_df["Ngày"] == filter_date]
        if filter_staff != "Tất cả": temp_filtered_df = temp_filtered_df[temp_filtered_df["Nhân Sự"] == filter_staff]

        if enable_hour_filter and start_t and end_t:
            def check_time_in_range(t_str):
                try:
                    t_val = datetime.datetime.strptime(str(t_str).strip(), "%H:%M:%S").time()
                    return start_t <= t_val <= end_t
                except:
                    return True
            temp_filtered_df = temp_filtered_df[temp_filtered_df["Thời Gian"].apply(check_time_in_range)]

        with f_col4:
            available_tasks = ["Tất cả"] + sorted(temp_filtered_df["Hạng Mục Công Việc"].unique().tolist()) if not temp_filtered_df.empty else ["Tất cả"]
            filter_task = st.selectbox("Lọc theo Hạng Mục", available_tasks)
        
        filtered_df = temp_filtered_df.copy()
        if filter_task != "Tất cả": filtered_df = filtered_df[filtered_df["Hạng Mục Công Việc"] == filter_task]
            
        rows_per_page = 10
        total_rows = len(filtered_df)
        total_pages = (total_rows - 1) // rows_per_page + 1

        with f_col5:
            current_page = st.number_input(f"Trang hiển thị ({total_pages} tr | {total_rows} bản ghi)", min_value=1, max_value=max(total_pages, 1), value=1, step=1, key="pagination_page_num")

        start_idx = (current_page - 1) * rows_per_page
        paginated_df = filtered_df.iloc[start_idx:start_idx + rows_per_page]

        if filter_task != "Tất cả":
            total_qty_task = filtered_df["Số Lượng"].sum() if not filtered_df.empty else 0
            unit_name = filtered_df["Đơn Vị"].values[0] if not filtered_df.empty and "Đơn Vị" in filtered_df.columns else "Cái"
            st.markdown(f'<div style="background: rgba(59, 130, 246, 0.15); padding: 12px 18px; border-radius: 8px; border: 2px solid #3b82f6; margin-bottom: 15px; font-size: 1rem; font-weight: bold; text-align: center;">📊 Tổng số lượng của hạng mục <span style="color: #ff4b4b;">"{filter_task}"</span>: <span style="font-size: 1.2rem; color: #1d4ed8;">{total_qty_task:,.0f}</span> {unit_name}</div>', unsafe_allow_html=True)

        if not paginated_df.empty:
            can_delete_data = (current_user_role == "Admin" or user_perms.get("perm_input", False))
            if can_delete_data:
                _, col_del_all_2 = st.columns([2.5, 1.5])
                with col_del_all_2:
                    del_c1, del_c2 = st.columns([1, 1])
                    with del_c1: confirm_delete_all = st.checkbox("Xác nhận xóa tất cả trang này", key="chk_confirm_delete_all")
                    with del_c2:
                        if st.button("🗑️ Xóa tất cả trang này", use_container_width=True, type="primary"):
                            if confirm_delete_all:
                                all_paginated_ids = paginated_df["db_id"].tolist()
                                if all_paginated_ids:
                                    update_production_log_deleted_status(all_paginated_ids, True)
                                    st.success("Đã chuyển toàn bộ bản ghi đang hiển thị ở trang này vào thùng rác!")
                                    st.rerun()
                            else:
                                st.warning("⚠️ Vui lòng tích chọn xác nhận trước khi bấm!")

            selected_ids_to_delete = []
            for idx, row in paginated_df.iterrows():
                row_c1, row_c2 = st.columns([4, 1])
                with row_c1:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;">
                        <b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} ⏰ {row['Thời Gian']} &nbsp;|&nbsp; 👤 <b>{row['Nhân Sự']}</b><br>
                        📌 {row['Hạng Mục Công Việc']} &nbsp;|&nbsp; 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                        💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                    </div>
                    """, unsafe_allow_html=True)
                    if can_delete_data and st.checkbox(f"Chọn xóa bản ghi STT {row['STT']}", key=f"chk_{row['db_id']}"):
                        selected_ids_to_delete.append(row['db_id'])
                        
                with row_c2:
                    img_url_val = row.get("Hình Ảnh", "")
                    if img_url_val and isinstance(img_url_val, str):
                        urls = [u.strip() for u in img_url_val.split(",") if u.strip()]
                        if urls:
                            sub_cols = st.columns(min(len(urls), 4), gap="small")
                            for i, u in enumerate(urls):
                                with sub_cols[i]:
                                    with st.popover("🔍", help="Xem ảnh lớn"): st.image(u, use_container_width=True)
                                    st.image(u, width=40)
                    else:
                        st.markdown("<small style='color: gray;'>Không ảnh</small>", unsafe_allow_html=True)
                st.markdown("---")
            
            if can_delete_data and selected_ids_to_delete:
                if st.button("🗑️ Chuyển Các Dòng Đã Chọn Vào Thùng Rác", use_container_width=True, type="secondary"):
                    update_production_log_deleted_status(selected_ids_to_delete, True)
                    st.success("Đã chuyển các dòng đã chọn vào thùng rác!")
                    st.rerun()
        else:
            st.info("Không tìm thấy bản ghi nào khớp bộ lọc.")
    else:
        st.info("Chưa có dữ liệu sản lượng.")
