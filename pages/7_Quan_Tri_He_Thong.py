import streamlit as st
import pandas as pd
from utils import compress_image_to_base64
from database import supabase, get_staff_df_db, get_staff_list_db, load_app_settings_db, save_app_settings_db, save_folders_db, save_staff_list_db

def render(current_user_role, hash_password_func):
    # Ở đây chúng ta gom các trang Admin: Cài đặt giao diện, Quản lý thư mục/menu, Quản lý tài khoản & phân quyền, Làm sạch dữ liệu
    st.header("7. Quản Trị Hệ Thống (Admin)")
    
    if current_user_role != "Admin":
        st.warning("🔒 Khu vực này chỉ dành riêng cho Quản trị viên hệ thống!")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["🛡️ Tài Khoản & Phân Quyền", "🎨 Giao Diện & Nhân Sự", "📁 Cấu Hình Thư Mục", "🧹 Làm Sạch Dữ Liệu"])

    with tab1:
        st.subheader("Quản Lý Tài Khoản & Phân Quyền Chi Tiết")
        try:
            staff_list_names = get_staff_list_db()
            for s_name in staff_list_names:
                chk = supabase.table("user_accounts").select("*").eq("name", s_name).execute()
                if not chk.data:
                    supabase.table("user_accounts").insert({
                        "name": s_name, "password_hash": hash_password_func("123456"),
                        "role": "Staff", "perm_input": False, "perm_report": False,
                        "perm_attendance": True, "perm_rules": False
                    }).execute()

            res_roles = supabase.table("user_accounts").select("*").execute()
            if res_roles.data:
                roles_df = pd.DataFrame(res_roles.data)
                with st.form("manage_accounts_form"):
                    edited_roles_df = st.data_editor(
                        roles_df,
                        column_config={
                            "id": "ID", "name": st.column_config.TextColumn("Họ và tên nhân sự", disabled=True),
                            "password_hash": None,
                            "role": st.column_config.SelectboxColumn("Vai trò", options=["Admin", "Manager", "Staff"], required=True),
                            "perm_input": st.column_config.CheckboxColumn("Nhập sản lượng"),
                            "perm_report": st.column_config.CheckboxColumn("Xem báo cáo"),
                            "perm_attendance": st.column_config.CheckboxColumn("Chấm công"),
                            "perm_rules": st.column_config.CheckboxColumn("Sửa định mức")
                        },
                        hide_index=True, use_container_width=True
                    )
                    
                    st.markdown("---")
                    st.markdown("##### 🔑 Đổi mật khẩu nhanh cho nhân sự")
                    col_p1, col_p2, col_p3 = st.columns([1.5, 1.5, 1])
                    with col_p1: target_staff_pw = st.selectbox("Chọn nhân sự", ["--- Chọn nhân sự ---"] + staff_list_names)
                    with col_p2: new_staff_pass = st.text_input("Mật khẩu mới", type="password")
                    with col_p3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_update_pw = st.form_submit_button("Cập Nhật Mật Khẩu", use_container_width=True)

                    if btn_update_pw:
                        if target_staff_pw != "--- Chọn nhân sự ---" and new_staff_pass:
                            if len(new_staff_pass) >= 6:
                                supabase.table("user_accounts").update({"password_hash": hash_password_func(new_staff_pass)}).eq("name", target_staff_pw).execute()
                                st.success(f"✅ Đã đổi mật khẩu thành công cho **{target_staff_pw}**!")
                            else:
                                st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
                        else:
                            st.warning("⚠️ Vui lòng chọn nhân sự và nhập mật khẩu mới!")

                    if st.form_submit_button("💾 Lưu Cập Nhật Quyền Hạn Hàng Loạt", use_container_width=True):
                        for _, row in edited_roles_df.iterrows():
                            supabase.table("user_accounts").update({
                                "role": row["role"], "perm_input": bool(row["perm_input"]),
                                "perm_report": bool(row["perm_report"]), "perm_attendance": bool(row["perm_attendance"]),
                                "perm_rules": bool(row["perm_rules"])
                            }).eq("id", row["id"]).execute()
                        st.cache_data.clear()
                        st.success("✅ Đã cập nhật quyền hạn chi tiết thành công!")
                        st.rerun()
        except Exception as e:
            st.error(f"Lỗi quản lý tài khoản: {e}")

    with tab2:
        st.subheader("Cài Đặt Giao Diện & Danh Sách Nhân Sự")
        db_settings = load_app_settings_db()
        with st.form("ui_settings_form"):
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                picker_bg = st.color_picker("Màu nền ứng dụng", value=db_settings.get("bg_color") or "#ffffff")
                picker_text = st.color_picker("Màu chữ", value=db_settings.get("text_color") or "#31333F")
            with c_col2:
                picker_primary = st.color_picker("Màu chủ đạo", value=db_settings.get("primary_color") or "#ff4b4b")
                picker_sidebar = st.color_picker("Màu nền sidebar", value=db_settings.get("sidebar_bg") or "#f0f2f6")
                
            slider_opacity = st.slider("Độ mờ sidebar", 0.1, 1.0, float(db_settings.get("sidebar_opacity") or 0.9), 0.05)
            bg_file_upload = st.file_uploader("🖼️ Tải lên hình nền ứng dụng", type=["png", "jpg", "jpeg"])
            
            if st.form_submit_button("💾 Lưu Cài Đặt Giao Diện", use_container_width=True):
                st.session_state.bg_color = picker_bg
                st.session_state.text_color = picker_text
                st.session_state.primary_color = picker_primary
                st.session_state.sidebar_bg = picker_sidebar
                st.session_state.sidebar_opacity = slider_opacity
                if bg_file_upload is not None:
                    if compressed_bg := compress_image_to_base64(bg_file_upload, max_size=(1920, 1080), quality=80):
                        st.session_state.bg_image_base64 = compressed_bg
                save_app_settings_db({
                    "primary_color": st.session_state.primary_color, "bg_color": st.session_state.bg_color,
                    "sidebar_bg": st.session_state.sidebar_bg, "sidebar_opacity": st.session_state.sidebar_opacity,
                    "text_color": st.session_state.text_color, "bg_image_base64": st.session_state.bg_image_base64,
                    "avatar_base64": st.session_state.avatar_base64
                })
                st.success("Đã lưu cài đặt giao diện!")
                st.rerun()

        st.markdown("---")
        st.markdown("### 👥 Quản Lý Danh Sách Nhân Sự")
        with st.form("staff_form"):
            staff_df = get_staff_df_db()
            edited_staff = st.data_editor(staff_df, num_rows="dynamic", use_container_width=True, hide_index=True, disabled=["id"])
            if st.form_submit_button("💾 Lưu Nhân Sự", use_container_width=True):
                save_staff_list_db(edited_staff)
                st.session_state.staff_list = get_staff_list_db()
                st.success("Đã cập nhật danh sách nhân sự!")
                st.rerun()

    with tab3:
        st.subheader("Quản Lý Cấu Trúc Thư Mục & Menu")
        with st.form("manage_menu_form"):
            current_folder_name = st.session_state.folders[0]["folder_name"] if st.session_state.folders else "📌 Quản Lý Nghiệp Vụ"
            new_folder_name = st.text_input("Tên thư mục", value=current_folder_name)
            current_items = st.session_state.folders[0]["items"] if st.session_state.folders else []
            updated_items = []
            for i_idx, item in enumerate(current_items):
                new_name = st.text_input(f"Tên hiển thị {i_idx+1}", value=item.get("name", ""), key=f"edit_name_{i_idx}")
                updated_items.append({"id": item.get("id", f"menu_{i_idx+1}"), "name": new_name})
                
            if st.form_submit_button("💾 Lưu Thay Đổi Menu", use_container_width=True):
                new_folders_structure = [{"folder_name": new_folder_name, "items": updated_items}]
                st.session_state.folders = new_folders_structure
                save_folders_db(new_folders_structure)
                st.success("Đã lưu menu thành công!")
                st.rerun()

    with tab4:
        st.subheader("Làm Sạch Dữ Liệu Hệ Thống")
        if st.button("🔥 Xóa Toàn Bộ Dữ Liệu Thùng Rác Vĩnh Viễn", use_container_width=True):
            from database import get_production_logs_db, permanent_delete_db
            trash_df = get_production_logs_db(is_deleted=True, limit_rows=500)
            if not trash_df.empty:
                permanent_delete_db(trash_df["db_id"].tolist())
                st.success("Đã làm sạch thùng rác!")
                st.rerun()
