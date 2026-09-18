import streamlit as st
import datetime
import hashlib
import pytz
from database import supabase

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
         
