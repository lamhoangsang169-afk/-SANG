import streamlit as st
import datetime
import hashlib
import pytz
import pandas as pd
import plotly.express as px
from database import (
    supabase, is_supabase_connected, get_staff_df_db, get_staff_list_db, 
    get_rules_df_db, get_production_logs_db, get_production_logs_by_date_range,
    get_attendance_db, load_app_settings_db, load_folders_db
)

st.set_page_config(
    page_title="Hệ Thống Quản Lý Sản Lượng & Chấm Công",
    page_icon="🐧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cấu hình múi giờ Việt Nam
VN_TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")

# Khởi tạo session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_identifier" not in st.session_state:
    st.session_state.user_identifier = ""
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "1. Nhập Sản Lượng"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login_admin(email, password):
    clean_email = email.strip().lower()
    clean_pw = password.strip()
    
    # Ưu tiên đăng nhập tài khoản Admin mặc định
    if clean_email == "lamhoangsang169@gmail.com" and clean_pw in ["123456", "Sang1998*"]:
        return True
        
    if supabase is not None:
        try:
            res = supabase.auth.sign_in_with_password({"email": clean_email, "password": clean_pw})
            if res and res.user:
                return True
        except Exception:
            pass
            
    return False

# ==================== ĐĂNG NHẬP ====================
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
                email_input = st.text_input("📧 Email Admin", value="lamhoangsang169@gmail.com")
                password_admin = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...", key="pw_admin")
                remember_admin = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_admin")
                
                if st.form_submit_button("🚀 Đăng Nhập Quản Trị Viên", use_container_width=True):
                    if not email_input or not password_admin:
                        st.error("⚠️ Vui lòng nhập đầy đủ!")
                    elif check_login_admin(email_input, password_admin):
                        st.session_state.logged_in = True
                        st.session_state.user_identifier = email_input.strip()
                        if remember_admin:
                            st.query_params["auth_user"] = email_input.strip()
                        st.success("✅ Đăng nhập Admin thành công!")
                        st.rerun()
                    else:
                        st.error("❌ Mật khẩu hoặc Email không chính xác!")
                        
        with tab_staff:
            with st.form("login_staff_form"):
                staff_list_opt = ["--- Chọn họ và tên ---"] + get_staff_list_db()
                login_name = st.selectbox("👤 Họ và tên nhân sự", staff_list_opt)
                password_staff = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...", key="pw_staff")
                remember_staff = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_staff")
                
                if st.form_submit_button("🚀 Đăng Nhập Nhân Viên", use_container_width=True):
                    if login_name == "--- Chọn họ và tên ---" or not password_staff:
                        st.error("⚠️ Vui lòng chọn tên và nhập mật khẩu!")
                    elif supabase is None:
                        st.error("⚠️ Chưa kết nối CSDL!")
                    else:
                        try:
                            res = supabase.table("user_accounts").select("*").eq("name", login_name).execute()
                            if res.data and len(res.data) > 0:
                                user_record = res.data[0]
                                if user_record.get("password_hash") == hash_password(password_staff):
                                    st.session_state.logged_in = True
                                    st.session_state.user_identifier = login_name
                                    if remember_staff:
                                        st.query_params["auth_user"] = login_name
                                    st.success("✅ Đăng nhập thành công!")
                                    st.rerun()
                                else:
                                    st.error("❌ Mật khẩu không chính xác!")
                            else:
                                st.error("❌ Tài khoản chưa được cấp quyền!")
                        except Exception as e:
                            st.error(f"❌ Lỗi đăng nhập: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==================== TRANG CHÍNH ====================
st.sidebar.title("📌 Danh Mục Chức Năng")
st.sidebar.markdown(f"👤 Đang đăng nhập: **{st.session_state.user_identifier}**")

if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_identifier = ""
    if "auth_user" in st.query_params:
        del st.query_params["auth_user"]
    st.rerun()

st.sidebar.markdown("---")
folders = load_folders_db()
for folder in folders:
    with st.sidebar.expander(folder["folder_name"], expanded=True):
        for item in folder["items"]:
            if st.button(item["name"], use_container_width=True, key=f"nav_{item['id']}"):
                st.session_state.current_menu = item["name"]
                st.rerun()

# Hiển thị nội dung
current_menu = st.session_state.current_menu
st.header(f"📋 {current_menu}")

if "1. Nhập Sản Lượng" in current_menu:
    st.subheader("Nhập Sản Lượng Hàng Ngày")
    input_df = get_production_logs_db(is_deleted=False)
    if not input_df.empty:
        st.dataframe(input_df, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu sản lượng.")

elif "2. Báo Cáo Thống Kê" in current_menu:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_d = st.date_input("Từ ngày", datetime.date.today().replace(day=1))
    with col_d2:
        end_d = st.date_input("Đến ngày", datetime.date.today())
        
    rep_df = get_production_logs_by_date_range(start_d, end_d)
    if not rep_df.empty:
        summary = rep_df.groupby("Nhân Sự").agg(Tổng_Số_Lượng=("Số Lượng", "sum"), Tổng_Điểm=("Tổng Điểm", "sum")).reset_index()
        st.dataframe(summary, use_container_width=True, hide_index=True)
        
        fig = px.pie(summary, names="Nhân Sự", values="Tổng_Điểm", title="Tỷ lệ đóng góp điểm sản lượng")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Không có dữ liệu báo cáo trong khoảng thời gian này.")

elif "3. Tham Chiếu Định Mức" in current_menu:
    rules_df = get_rules_df_db()
    st.dataframe(rules_df, use_container_width=True, hide_index=True)

else:
    st.info(f"Tính năng **{current_menu}** đang hoạt động.")
