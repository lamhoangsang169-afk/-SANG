import streamlit as st
import datetime
import hashlib
from utils import hex_to_rgba, VN_TIMEZONE
from database import supabase, get_staff_list_db

st.set_page_config(
    page_title="Hệ Thống Quản Lý Sản Lượng & Chấm Công",
    page_icon="🐧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_identifier" not in st.session_state:
    st.session_state.user_identifier = ""

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(identifier, password):
    identifier = identifier.strip()
    if identifier.lower() == "lamhoangsang169@gmail.com" and password == "123456":
        return True, "Admin"
    
    if supabase is None:
        return False, "Staff"
        
    try:
        res = supabase.table("user_accounts").select("*").eq("name", identifier).execute()
        if res.data:
            user = res.data[0]
            if user.get("password_hash") == hash_password(password):
                return True, user.get("role", "Staff")
    except Exception as e:
        print(f"Login error: {e}")
    return False, "Staff"

# Giao diện Đăng nhập nếu chưa xác thực
if not st.session_state.logged_in:
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h2>🔐 Đăng Nhập Hệ Thống POSS</h2>
            <p>Vui lòng đăng nhập để tiếp tục sử dụng các tính năng</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập / Email nhân sự")
            password = st.text_input("Mật khẩu", type="password")
            submit = st.form_submit_button("🚀 Đăng Nhập", use_container_width=True)
            
            if submit:
                success, role = check_login(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user_identifier = username
                    st.success("🎉 Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("⚠️ Sai tên đăng nhập hoặc mật khẩu!")
    st.stop()

# --- Giao diện Trang Chủ khi đã đăng nhập ---
st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <img src="https://api.dicebear.com/7.x/bottts/svg?seed={st.session_state.user_identifier}" width="80" style="border-radius: 50%; background: #fff; padding: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <p style="margin-top: 10px; font-weight: bold; font-size: 0.9rem;">👤 {st.session_state.user_identifier}</p>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Đăng Xuất", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_identifier = ""
    st.rerun()

st.sidebar.markdown("---")

# Nội dung trang chủ
st.subheader("👋 Chào mừng bạn đến với Hệ Thống Quản Lý Sản Lượng & Chấm Công!")
st.info("💡 **Hướng dẫn:** Sử dụng thanh menu ở góc trên bên trái màn hình (Sidebar) để chuyển đổi qua lại giữa các chức năng: **Nhập Sản Lượng, Chấm Công, Báo Cáo, Quản Trị...**")

now_vn = datetime.datetime.now(VN_TIMEZONE)
st.success(f"📅 Thời gian hệ thống hiện tại (VN): **{now_vn.strftime('%d/%m/%Y - %H:%M:%S')}**")
