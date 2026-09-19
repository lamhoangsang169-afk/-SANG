import streamlit as st
import pandas as pd
import datetime
import base64
import hashlib
import os

# Import từ các module tiện ích và database gốc
from utils import (
    VN_TIMEZONE, 
    compress_image_to_base64, 
    calculate_exact_minutes, 
    hex_to_rgba
)
from database import (
    supabase, 
    is_supabase_connected, 
    init_db_data,
    get_staff_df_db, 
    get_staff_list_db, 
    get_rules_df_db,
    get_production_logs_db, 
    get_total_production_count_db, 
    load_app_settings_db, 
    load_folders_db,
    save_staff_list_db,
    save_app_settings_db,
    save_folders_db,
    permanent_delete_db
)

# ==================== IMPORT TỪ THƯ MỤC VIEW ====================
from view import (
    render_nhap_san_luong,
    render_cham_cong,
    render_bao_cao,
    render_thu_muc_bao_cao,
    render_dinh_muc_cong_viec,
    render_thung_rac
)

st.set_page_config(page_title="POSS - Quản Lý Sản Xuất", page_icon="📊", layout="wide")

init_db_data()

# Các hàm trợ giúp hệ thống
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_app_memory_usage():
    try:
        import sys, psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 ** 2)
        return f"{mem_mb:.1f} MB"
    except Exception:
        return "Ổn định"

def get_detailed_storage_usage():
    if supabase is None:
        return "0 MB / 500 MB", "0 MB / 1 GB"
    try:
        logs_count = len(supabase.table("production_logs").select("id", count="exact").execute().data)
        att_count = len(supabase.table("attendance").select("id", count="exact").execute().data)
        users_count = len(supabase.table("user_accounts").select("id", count="exact").execute().data)
        
        estimated_db_kb = (logs_count + att_count + users_count) * 2.5
        db_used_str = f"{estimated_db_kb / 1024:.2f} MB" if estimated_db_kb > 1024 else f"{estimated_db_kb:.1f} KB"
        db_display = f"{db_used_str} / 500 MB"

        storage_bytes = 0
        try:
            files_img = supabase.storage.from_("production-images").list()
            files_rep = supabase.storage.from_("reports-storage").list()
            total_files = (files_img if files_img else []) + (files_rep if files_rep else [])
            for f in total_files:
                storage_bytes += f.get("metadata", {}).get("size", 0)
        except Exception:
            pass

        storage_mb = storage_bytes / (1024 * 1024)
        storage_display = f"{storage_mb / 1024:.2f} GB / 1 GB" if storage_mb >= 1024 else f"{storage_mb:.2f} MB / 1 GB"
            
        return db_display, storage_display
    except Exception:
        return "0 MB / 500 MB", "0 MB / 1 GB"

# ==================== CHECK SESSION & ĐĂNG NHẬP ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_identifier" not in st.session_state:
    st.session_state.user_identifier = ""

params = st.query_params
if not st.session_state.logged_in and "auth_user" in params:
    st.session_state.logged_in = True
    st.session_state.user_identifier = params["auth_user"]

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.9); padding: 25px 30px 10px 30px; border-radius: 12px 12px 0 0; box-shadow: 0 8px 20px rgba(0,0,0,0.15); border: 1px solid #e2e8f0; border-bottom: none;">
            <h2 style="text-align: center; color: #ff4b4b; margin-bottom: 0px;">🔐 HỆ THỐNG POSS</h2>
            <p style="text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 5px;">Đăng nhập hệ thống nội bộ</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='background: rgba(255, 255, 255, 0.9); padding: 20px 30px 30px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.15); border: 1px solid #e2e8f0; border-top: none;'>", unsafe_allow_html=True)
        tab_admin, tab_staff = st.tabs(["👑 Quản Trị Viên", "👤 Nhân Viên"])
        
        with tab_admin:
            with st.form("login_admin_form"):
                email_input = st.text_input("📧 Email Admin", placeholder="lamhoangsang169@gmail.com")
                password_admin = st.text_input("🔑 Mật khẩu", type="password", key="pw_admin")
                remember_admin = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_admin")
                submitted_admin = st.form_submit_button("🚀 Đăng Nhập Quản Trị Viên", use_container_width=True)
                
                if submitted_admin:
                    if not email_input or not password_admin:
                        st.error("⚠️ Vui lòng nhập đầy đủ Email và Mật khẩu!")
                    elif supabase is None:
                        st.error("⚠️ Chưa kết nối được tới cơ sở dữ liệu!")
                    else:
                        try:
                            res = supabase.auth.sign_in_with_password({"email": email_input.strip(), "password": password_admin.strip()})
                            if res and res.user:
                                st.session_state.logged_in = True
                                st.session_state.user_identifier = res.user.email
                                if remember_admin: st.query_params["auth_user"] = res.user.email
                                st.rerun()
                            else: st.error("❌ Email hoặc mật khẩu Admin không chính xác!")
                        except Exception as e: st.error(f"❌ Lỗi đăng nhập: {e}")

        with tab_staff:
            with st.form("login_staff_form"):
                staff_list_opt = ["--- Chọn họ và tên ---"] + get_staff_list_db()
                login_name = st.selectbox("👤 Họ và tên nhân sự", staff_list_opt)
                password_staff = st.text_input("🔑 Mật khẩu", type="password", key="pw_staff")
                remember_staff = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_staff")
                submitted_staff = st.form_submit_button("🚀 Đăng Nhập Nhân Viên", use_container_width=True)
                
                if submitted_staff:
                    if login_name == "--- Chọn họ và tên ---" or not password_staff:
                        st.error("⚠️ Vui lòng chọn họ tên và nhập mật khẩu!")
                    elif supabase is None:
                        st.error("⚠️ Chưa kết nối được tới cơ sở dữ liệu!")
                    else:
                        try:
                            res = supabase.table("user_accounts").select("*").eq("name", login_name).execute()
                            if res.data and len(res.data) > 0:
                                user_record = res.data[0]
                                if user_record["password_hash"] == hash_password(password_staff):
                                    st.session_state.logged_in = True
                                    st.session_state.user_identifier = login_name
                                    if remember_staff: st.query_params["auth_user"] = login_name
                                    st.rerun()
                                else: st.error("❌ Mật khẩu không chính xác!")
                            else: st.error("❌ Tài khoản chưa được Quản trị viên cấp mật khẩu!")
                        except Exception as e: st.error(f"❌ Lỗi đăng nhập: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==================== HỆ THỐNG PHÂN QUYỀN ====================
def get_user_permissions(identifier):
    default_perms = {"role": "Staff", "perm_input": False, "perm_report": False, "perm_attendance": True, "perm_rules": False}
    if not identifier or supabase is None: return default_perms
    if str(identifier).strip().lower() == "lamhoangsang169@gmail.com":
        return {"role": "Admin", "perm_input": True, "perm_report": True, "perm_attendance": True, "perm_rules": True}
    try:
        res = supabase.table("user_accounts").select("*").eq("name", identifier).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            return {
                "role": row.get("role", "Staff"), "perm_input": row.get("perm_input", False),
                "perm_report": row.get("perm_report", False), "perm_attendance": row.get("perm_attendance", True),
                "perm_rules": row.get("perm_rules", False)
            }
    except Exception: pass
    return default_perms

user_perms = get_user_permissions(st.session_state.user_identifier)
current_user_role = user_perms["role"]

# ==================== KHỞI TẠO BIẾN SESSION & UI ====================
st.session_state.staff_list = get_staff_list_db()
st.session_state.rules_df = get_rules_df_db()
st.session_state.chart_colors = ["#ff4b4b", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#14b8a6", "#f97316", "#6366f1"]
st.session_state.folders = load_folders_db()

db_settings = load_app_settings_db()
if "primary_color" not in st.session_state: st.session_state.primary_color = db_settings.get("primary_color") or "#ff4b4b"
if "bg_color" not in st.session_state: st.session_state.bg_color = db_settings.get("bg_color") or "#ffffff"
if "sidebar_bg" not in st.session_state: st.session_state.sidebar_bg = db_settings.get("sidebar_bg") or "#f0f2f6"
if "sidebar_opacity" not in st.session_state: st.session_state.sidebar_opacity = float(db_settings.get("sidebar_opacity") or 0.9)
if "text_color" not in st.session_state: st.session_state.text_color = db_settings.get("text_color") or "#31333F"
if "bg_image_base64" not in st.session_state: st.session_state.bg_image_base64 = db_settings.get("bg_image_base64")
if "avatar_base64" not in st.session_state: st.session_state.avatar_base64 = db_settings.get("avatar_base64")
if "current_menu" not in st.session_state: st.session_state.current_menu = "1. Nhập Sản Lượng"

sidebar_rgba = hex_to_rgba(st.session_state.sidebar_bg, st.session_state.sidebar_opacity)

# ==================== SIDEBAR NAVIGATION ====================
with st.sidebar:
    st.markdown(f"<small>👤 <b>{st.session_state.user_identifier}</b> (Role: <b>{current_user_role}</b>)</small>", unsafe_allow_html=True)
    if st.button("🚪 Đăng Xuất", use_container_width=True):
        if current_user_role == "Admin" and supabase: supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.session_state.user_identifier = ""
        if "auth_user" in st.query_params: del st.query_params["auth_user"]
        st.rerun()

    st.markdown("---")
    if user_perms["perm_attendance"] or current_user_role == "Admin":
        if st.button("⏱️ Chấm Công Ca Làm Việc", use_container_width=True):
            st.session_state.current_menu = "⏱️ Chấm Công Ca Làm Việc"
            st.rerun()

    st.markdown("---")
    st.markdown("### 📂 CHỨC NĂNG HỆ THỐNG")
    for folder in st.session_state.folders:
        filtered_items = []
        for item in folder["items"]:
            if current_user_role == "Admin": filtered_items.append(item)
            else:
                item_id = item.get("id")
                if item_id == "menu_1" and user_perms["perm_input"]: filtered_items.append(item)
                elif item_id == "menu_2" and user_perms["perm_report"]: filtered_items.append(item)
                elif item_id == "menu_3" and user_perms["perm_rules"]: filtered_items.append(item)
                elif item_id == "menu_5" and user_perms["perm_report"]: filtered_items.append(item)

        if filtered_items:
            with st.expander(folder["folder_name"], expanded=True):
                for item in filtered_items:
                    if st.button(item["name"], use_container_width=True, key=f"btn_{item['id']}"):
                        st.session_state.current_menu = item["name"]
                        st.rerun()

    if current_user_role == "Admin":
        st.markdown("---")
        st.markdown("### ⚙️ Cấu Hình Hệ Thống (Admin)")
        if st.button("📁 Quản Lý Thư Mục & Menu", use_container_width=True):
            st.session_state.current_menu = "📁 Quản Lý Thư Mục & Menu"
            st.rerun()
        if st.button("🎨 Cài Đặt Giao Diện", use_container_width=True):
            st.session_state.current_menu = "🎨 Cài Đặt Giao Diện"
            st.rerun()
        if st.button("🛡️ Quản Lý Tài Khoản & Phân Quyền", use_container_width=True):
            st.session_state.current_menu = "🛡️ Quản Lý Tài Khoản & Phân Quyền"
            st.rerun()
        if st.button("🧹 Làm Sạch & Tối Ưu Dữ Liệu", use_container_width=True):
            st.session_state.current_menu = "🧹 Làm Sạch Dữ Liệu"
            st.rerun()

menu = st.session_state.current_menu

def get_feature_type(menu_name):
    if menu_name == "⏱️ Chấm Công Ca Làm Việc": return "attendance"
    if menu_name == "📁 Quản Lý Thư Mục & Menu": return "manage_folders"
    if menu_name == "🎨 Cài Đặt Giao Diện": return "settings_ui"
    if menu_name == "🛡️ Quản Lý Tài Khoản & Phân Quyền": return "manage_roles"
    if menu_name == "🧹 Làm Sạch Dữ Liệu": return "clean_data"
    for folder in st.session_state.folders:
        for item in folder["items"]:
            if item["name"] == menu_name:
                if item["id"] == "menu_1": return "input_production"
                if item["id"] == "menu_2": return "report"
                if item["id"] == "menu_3": return "rules"
                if item["id"] == "menu_4": return "trash"
                if item["id"] == "menu_5": return "report_folder"
    return "input_production"

# ==================== BỘ ĐIỀU HƯỚNG MODULE VIEW ====================
@st.fragment
def render_main_content(current_menu_name):
    feature = get_feature_type(current_menu_name)

    # 1. Gọi Module Nhập Sản Lượng từ view/
    if feature == "input_production":
        render_nhap_san_luong(current_menu_name, current_user_role, user_perms)

    # 2. Gọi Module Chấm Công từ view/
    elif feature == "attendance":
        render_cham_cong(current_menu_name, current_user_role)

    # 3. Gọi Module Báo Cáo từ view/
    elif feature == "report":
        render_bao_cao(current_menu_name)

    # 4. Gọi Module Thư Mục Báo Cáo từ view/
    elif feature == "report_folder":
        render_thu_muc_bao_cao(current_menu_name)

    # 5. Gọi Module Định Mức Công Việc từ view/
    elif feature == "rules":
        render_dinh_muc_cong_viec(current_menu_name, current_user_role, user_perms)

    # 6. Gọi Module Thùng Rác từ view/
    elif feature == "trash":
        render_thung_rac(current_menu_name, current_user_role)

    # Các tính năng quản trị Admin
    elif feature == "manage_folders" and current_user_role == "Admin":
        st.header("Quản Lý Thư Mục & Menu")
        with st.form("manage_menu_form"):
            current_folder_name = st.session_state.folders[0]["folder_name"] if st.session_state.folders else "📌 Quản Lý Nghiệp Vụ"
            new_folder_name = st.text_input("Tên thư mục", value=current_folder_name)
            current_items = st.session_state.folders[0]["items"] if st.session_state.folders else []
            updated_items = []
            for i_idx, item in enumerate(current_items):
                new_name = st.text_input(f"Tên hiển thị {i_idx+1}", value=item.get("name", ""), key=f"edit_name_{i_idx}")
                updated_items.append({"id": item.get("id", f"menu_{i_idx+1}"), "name": new_name})
            if st.form_submit_button("💾 Lưu Thay Đổi", use_container_width=True):
                new_folders_structure = [{"folder_name": new_folder_name, "items": updated_items}]
                st.session_state.folders = new_folders_structure
                save_folders_db(new_folders_structure)
                st.success("Đã lưu menu thành công!")
                st.rerun()

    elif feature == "settings_ui" and current_user_role == "Admin":
        st.header("Cài Đặt Giao Diện & Nhân Sự")
        with st.form("staff_form"):
            staff_df = get_staff_df_db()
            edited_staff = st.data_editor(staff_df, num_rows="dynamic", use_container_width=True, hide_index=True, disabled=["id"])
            if st.form_submit_button("💾 Lưu Nhân Sự", use_container_width=True):
                save_staff_list_db(edited_staff)
                st.session_state.staff_list = get_staff_list_db()
                st.success("Đã cập nhật danh sách nhân sự!")
                st.rerun()

    elif feature == "clean_data" and current_user_role == "Admin":
        st.header("Làm Sạch Dữ Liệu")
        if st.button("🔥 Xóa Toàn Bộ Dữ Liệu Thùng Rác Vĩnh Viễn", use_container_width=True):
            trash_df = get_production_logs_db(is_deleted=True, limit_rows=500)
            if not trash_df.empty:
                permanent_delete_db(trash_df["db_id"].tolist())
                st.success("Đã làm sạch thùng rác!")
                st.rerun()

render_main_content(menu)
