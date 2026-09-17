import streamlit as st
import base64
import hashlib
from utils import compress_image_to_base64, hex_to_rgba
from database import (
    supabase, 
    is_supabase_connected, 
    init_db_data,
    get_staff_list_db, 
    load_app_settings_db, 
    load_folders_db,
    get_production_logs_db,
    get_total_production_count_db
)

st.set_page_config(page_title="POSS - Quản Lý Sản Xuất", page_icon="📊", layout="wide")

init_db_data()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Kiểm tra đăng nhập Session & Query Params
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
                password_admin = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...", key="pw_admin")
                remember_admin = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_admin")
                
                if st.form_submit_button("🚀 Đăng Nhập Quản Trị Viên", use_container_width=True):
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
                                st.success("✅ Đăng nhập Admin thành công!")
                                st.rerun()
                            else:
                                st.error("❌ Email hoặc mật khẩu không chính xác!")
                        except Exception as e:
                            st.error(f"❌ Lỗi đăng nhập: {e}")
                            
        with tab_staff:
            with st.form("login_staff_form"):
                staff_list_opt = ["--- Chọn họ và tên ---"] + get_staff_list_db()
                login_name = st.selectbox("👤 Họ và tên nhân sự", staff_list_opt)
                password_staff = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...", key="pw_staff")
                remember_staff = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_staff")
                
                if st.form_submit_button("🚀 Đăng Nhập Nhân Viên", use_container_width=True):
                    if login_name == "--- Chọn họ và tên ---" or not password_staff:
                        st.error("⚠️ Vui lòng chọn họ tên và nhập mật khẩu!")
                    elif supabase is None:
                        st.error("⚠️ Chưa kết nối được tới cơ sở dữ liệu!")
                    else:
                        try:
                            res = supabase.table("user_accounts").select("*").eq("name", login_name).execute()
                            if res.data and len(res.data) > 0:
                                if res.data[0]["password_hash"] == hash_password(password_staff):
                                    st.session_state.logged_in = True
                                    st.session_state.user_identifier = login_name
                                    if remember_staff: st.query_params["auth_user"] = login_name
                                    st.success("✅ Đăng nhập thành công!")
                                    st.rerun()
                                else:
                                    st.error("❌ Mật khẩu không chính xác!")
                            else:
                                st.error("❌ Tài khoản chưa được cấp mật khẩu!")
                        except Exception as e:
                            st.error(f"❌ Lỗi đăng nhập: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Phân quyền & Giao diện chung khi đã đăng nhập
def get_user_permissions(identifier):
    default_perms = {"role": "Staff", "perm_input": False, "perm_report": False, "perm_attendance": True, "perm_rules": False}
    if not identifier or supabase is None: return default_perms
    if str(identifier).strip().lower() == "lamhoangsang169@gmail.com":
        return {"role": "Admin", "perm_input": True, "perm_report": True, "perm_attendance": True, "perm_rules": True}
    try:
        res = supabase.table("user_accounts").select("*").eq("name", identifier).execute()
        if res.data:
            row = res.data[0]
            return {"role": row.get("role", "Staff"), "perm_input": row.get("perm_input", False), "perm_report": row.get("perm_report", False), "perm_attendance": row.get("perm_attendance", True), "perm_rules": row.get("perm_rules", False)}
    except Exception: pass
    return default_perms

user_perms = get_user_permissions(st.session_state.user_identifier)
current_user_role = user_perms["role"]

db_settings = load_app_settings_db()
primary_color = db_settings.get("primary_color") or "#ff4b4b"
bg_color = db_settings.get("bg_color") or "#ffffff"
text_color = db_settings.get("text_color") or "#31333F"
sidebar_bg = hex_to_rgba(db_settings.get("sidebar_bg") or "#f0f2f6", float(db_settings.get("sidebar_opacity") or 0.9))

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_color}; color: {text_color} !important; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; backdrop-filter: blur(8px); }}
</style>
""", unsafe_allow_html=True)

# Giao diện Trang Chủ (Home Page)
st.title("📊 HỆ THỐNG QUẢN LÝ SẢN XUẤT POSS")
st.markdown("---")
st.info(f"👋 Chào mừng **{st.session_state.user_identifier}** đã đăng nhập vào hệ thống!")
st.markdown("👈 **Vui lòng chọn các chức năng ở thanh menu bên trái (Sidebar) để bắt đầu làm việc.**")

role_badge = "👑 Quản Trị Viên (Admin)" if current_user_role == "Admin" else "👤 Nhân Viên"
st.markdown(f"**Phân quyền hiện tại:** {role_badge}")

with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_identifier}**")
    if st.button("🚪 Đăng Xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_identifier = ""
        if "auth_user" in st.query_params: del st.query_params["auth_user"]
        st.rerun()
    st.markdown("---")
