import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io
import json
import os
import base64
from PIL import Image

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False

st.set_page_config(page_title="Phần Mềm Chấm Điểm Sản Lượng", page_icon="📊", layout="wide")

# ==================== KẾT NỐI SUPABASE & CƠ CHẾ AN TOÀN ====================
SUPABASE_URL = "https://xbozutjkiwnaoiluahq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhib3p1dGpraXl3bmFvaWx1YWhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwMjUwODIsImV4cCI6MjEwNDYwMTA4Mn0.ByzJ_xC9Cl3uUACmiIYD1xrHtDEs-fQBKZ4wSX-nlWc"

supabase = None
if HAS_SUPABASE_LIB and SUPABASE_KEY:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

DATA_FILE = "app_storage.json"
BUCKET_NAME = "APP_IMAGES"

class VietnamTz(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=7)
    def tzname(self, dt):
        return "ICT"
    def dst(self, dt):
        return datetime.timedelta(0)

VN_TIMEZONE = VietnamTz()

master_rules = [
    {"STT": 1, "Hạng Mục Công Việc": "Lấy hộp có sẵn", "Đơn Vị": "Cái", "Hệ Số Điểm": 0.5, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 2, "Hạng Mục Công Việc": "Lấy hộp mới", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 3, "Hạng Mục Công Việc": "Lấy đế có sẵn", "Đơn Vị": "Cái", "Hệ Số Điểm": 0.5, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 4, "Hạng Mục Công Việc": "Lấy đế mới", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 5, "Hạng Mục Công Việc": "Lấy phụ kiện có sẵn", "Đơn Vị": "Cái", "Hệ Số Điểm": 0.5, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 6, "Hạng Mục Công Việc": "Lấy phụ kiện mới", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 7, "Hạng Mục Công Việc": "Lấy mặt có sẵn", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 8, "Hạng Mục Công Việc": "Lấy mặt mới", "Đơn Vị": "Cái", "Hệ Số Điểm": 2.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 9, "Hạng Mục Công Việc": "Vệ sinh + kiểm tra ,+ cắt hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.5, "Ghi Chú": "Kiểm tra chất lượng"},
    {"STT": 10, "Hạng Mục Công Việc": "Kiểm tra BTP + cắt hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kiểm tra chất lượng"},
    {"STT": 11, "Hạng Mục Công Việc": "Kiểm tra hộp + cất hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kiểm tra chất lượng"},
    {"STT": 12, "Hạng Mục Công Việc": "Kiểm tra pha lê + cất hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 2.0, "Ghi Chú": "Kiểm tra chất lượng"},
    {"STT": 13, "Hạng Mục Công Việc": "Giao hàng shiper", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Vận chuyển / Giao nhận"},
    {"STT": 14, "Hạng Mục Công Việc": "tự đi giao hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 2.0, "Ghi Chú": "Vận chuyển / Giao nhận"},
    {"STT": 15, "Hạng Mục Công Việc": "Nhận hàng gia công ngoài", "Đơn Vị": "Cái", "Hệ Số Điểm": 0.1, "Ghi Chú": "Vận chuyển / Giao nhận"},
    {"STT": 16, "Hạng Mục Công Việc": "Cắp pha lê tấm", "Đơn Vị": "Cái", "Hệ Số Điểm": 2.0, "Ghi Chú": "Sản xuất / Gia công"},
]

default_chart_colors = ["#ff4b4b", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#14b8a6", "#f97316", "#6366f1"]

default_folders = [
    {
        "folder_name": "📌 Quản Lý Nghiệp Vụ",
        "items": [
            {"id": "menu_1", "name": "1. Nhập Sản Lượng"},
            {"id": "menu_2", "name": "2. Báo Cáo & Biểu Đồ"},
            {"id": "menu_3", "name": "3. Tham Chiếu Công Việc"},
            {"id": "menu_4", "name": "4. Thùng Rác Sản Lượng"}
        ]
    }
]

def upload_image_to_supabase(uploaded_file, folder_prefix="uploads"):
    if uploaded_file is None or supabase is None:
        return None
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((800, 800))
        
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        file_bytes = buffered.getvalue()
        
        file_name = f"{folder_prefix}/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        
        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
        return public_url
    except Exception as e:
        buffered_fb = io.BytesIO()
        img.save(buffered_fb, format="JPEG", quality=60)
        encoded = base64.b64encode(buffered_fb.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

def load_data():
    data = {}
    if supabase is not None:
        try:
            response = supabase.table("app_storage_table").select("data").eq("id", "main_config").execute()
            if response.data and len(response.data) > 0:
                raw_data = response.data[0]["data"]
                if isinstance(raw_data, str):
                    data = json.loads(raw_data)
                elif isinstance(raw_data, dict):
                    data = raw_data
        except Exception:
            pass
    
    if not data and os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    return data

def save_data():
    username = st.session_state.get("username", "admin")
    
    current_all_data = load_data()
    if not isinstance(current_all_data, dict):
        current_all_data = {}
        
    if "user_settings" not in current_all_data:
        current_all_data["user_settings"] = {}
        
    current_all_data["user_settings"][username] = {
        "primary_color": st.session_state.get("primary_color", "#ff4b4b"),
        "bg_color": st.session_state.get("bg_color", "#ffffff"),
        "sidebar_bg": st.session_state.get("sidebar_bg", "#f0f2f6"),
        "sidebar_opacity": st.session_state.get("sidebar_opacity", 0.9),
        "text_color": st.session_state.get("text_color", "#31333F"),
        "bg_image_url": st.session_state.get("bg_image_url", None),
        "avatar_url": st.session_state.get("avatar_url", None)
    }
    
    current_all_data["rules_df"] = st.session_state.rules_df.to_dict(orient="records") if "rules_df" in st.session_state else master_rules
    current_all_data["input_df"] = st.session_state.input_df.to_dict(orient="records") if "input_df" in st.session_state else []
    current_all_data["attendance_df"] = st.session_state.attendance_df.to_dict(orient="records") if "attendance_df" in st.session_state else []
    current_all_data["deleted_input_df"] = st.session_state.deleted_input_df.to_dict(orient="records") if "deleted_input_df" in st.session_state else []
    current_all_data["accounts"] = st.session_state.get("accounts", {"admin": {"password": "123456", "role": "admin", "staff_name": "Admin"}})
    
    normalized_accounts = {}
    for u, info in current_all_data["accounts"].items():
        if isinstance(info, dict):
            pass_val = info.get("password", "")
            role_val = info.get("role", "admin" if u == "admin" else "nhan_vien")
            s_name = info.get("staff_name", u)
            normalized_accounts[u] = {"password": pass_val, "role": role_val, "staff_name": s_name}
        else:
            normalized_accounts[u] = {"password": str(info), "role": "admin" if u == "admin" else "nhan_vien", "staff_name": u}
            
    current_all_data["accounts"] = normalized_accounts
    
    staff_map = {u: info["staff_name"] for u, info in normalized_accounts.items() if u != "admin"}
    current_all_data["account_staff_map"] = staff_map
    current_all_data["staff_list"] = list(staff_map.values())
    
    current_all_data["chart_colors"] = st.session_state.chart_colors if "chart_colors" in st.session_state else default_chart_colors
    current_all_data["folders"] = st.session_state.folders if "folders" in st.session_state else default_folders
    current_all_data["auto_refresh_minutes"] = st.session_state.get("auto_refresh_minutes", 5)
    
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(current_all_data, f, ensure_ascii=False, default=str, indent=4)
    except Exception:
        pass

    if supabase is not None:
        try:
            payload = {"id": "main_config", "data": current_all_data}
            supabase.table("app_storage_table").upsert(payload).execute()
        except Exception:
            pass

def safe_merge_and_save(table_key, new_rows_df):
    latest = load_data()
    if table_key == "input_df":
        existing = latest.get("input_df", [])
        df_existing = pd.DataFrame(existing) if existing else pd.DataFrame(columns=["STT", "Ngày", "Tài Khoản Tạo", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"])
        st.session_state.input_df = pd.concat([df_existing, new_rows_df], ignore_index=True)
        st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
    elif table_key == "attendance_df":
        existing = latest.get("attendance_df", [])
        df_existing = pd.DataFrame(existing) if existing else pd.DataFrame(columns=["STT", "Ngày", "Nhân Sự", "Giờ Vào Ca", "Giờ Ra Ca", "Số Phút Làm Việc", "Ghi Chú"])
        st.session_state.attendance_df = pd.concat([df_existing, new_rows_df], ignore_index=True)
        st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)
    
    if "accounts" in latest:
        raw_accs = latest["accounts"]
        norm_accs = {}
        for u, info in raw_accs.items():
            if isinstance(info, dict):
                norm_accs[u] = {"password": info.get("password", ""), "role": info.get("role", "nhan_vien"), "staff_name": info.get("staff_name", u)}
            else:
                norm_accs[u] = {"password": str(info), "role": "nhan_vien", "staff_name": u}
        st.session_state.accounts = norm_accs
        st.session_state.account_staff_map = {u: info["staff_name"] for u, info in norm_accs.items() if u != "admin"}
        st.session_state.staff_list = list(st.session_state.account_staff_map.values())

    if "rules_df" in latest:
        st.session_state.rules_df = pd.DataFrame(latest["rules_df"])
    if "auto_refresh_minutes" in latest:
        st.session_state.auto_refresh_minutes = latest["auto_refresh_minutes"]
        
    save_data()

saved_data = load_data()

if "auto_refresh_minutes" not in st.session_state:
    st.session_state.auto_refresh_minutes = saved_data.get("auto_refresh_minutes", 5)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = "nhan_vien"

loaded_accounts = saved_data.get("accounts", {})
if "admin" not in loaded_accounts:
    loaded_accounts["admin"] = {"password": "123456", "role": "admin", "staff_name": "Admin"}

norm_accounts = {}
for u, info in loaded_accounts.items():
    if isinstance(info, dict):
        norm_accounts[u] = {"password": info.get("password", ""), "role": info.get("role", "admin" if u == "admin" else "nhan_vien"), "staff_name": info.get("staff_name", u)}
    else:
        norm_accounts[u] = {"password": str(info), "role": "admin" if u == "admin" else "nhan_vien", "staff_name": u}

st.session_state.accounts = norm_accounts
staff_map = {u: info["staff_name"] for u, info in norm_accounts.items() if u != "admin"}
st.session_state.account_staff_map = staff_map
st.session_state.staff_list = list(staff_map.values())

if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1>📊 Phần Mềm Chấm Điểm Sản Lượng</h1>
            <p>Vui lòng đăng nhập hoặc tạo tài khoản để tiếp tục sử dụng hệ thống.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    with col_center2:
        tab_login, tab_register = st.tabs(["🔐 Đăng Nhập", "📝 Đăng Ký Tài Khoản"])
        
        with tab_login:
            with st.form("login_form"):
                lg_user = st.text_input("Tên đăng nhập")
                lg_pass = st.text_input("Mật khẩu", type="password")
                submit_lg = st.form_submit_button("Đăng Nhập", use_container_width=True)
                
                if submit_lg:
                    latest_fresh = load_data()
                    if "accounts" in latest_fresh:
                        raw_accs = latest_fresh["accounts"]
                        norm_accs = {}
                        for u, info in raw_accs.items():
                            if isinstance(info, dict):
                                norm_accs[u] = {"password": info.get("password", ""), "role": info.get("role", "nhan_vien"), "staff_name": info.get("staff_name", u)}
                            else:
                                norm_accs[u] = {"password": str(info), "role": "nhan_vien", "staff_name": u}
                        st.session_state.accounts = norm_accs
                    if "auto_refresh_minutes" in latest_fresh:
                        st.session_state.auto_refresh_minutes = latest_fresh["auto_refresh_minutes"]
                        
                    user_info = st.session_state.accounts.get(lg_user)
                    if user_info:
                        stored_pass = user_info.get("password", "")
                        user_role = user_info.get("role", "nhan_vien")
                        
                        if stored_pass == lg_pass:
                            st.session_state.logged_in = True
                            st.session_state.username = lg_user
                            st.session_state.role = user_role
                            
                            user_settings_map = latest_fresh.get("user_settings", {})
                            u_set = user_settings_map.get(lg_user, {})
                            st.session_state.primary_color = u_set.get("primary_color", "#ff4b4b")
                            st.session_state.bg_color = u_set.get("bg_color", "#ffffff")
                            st.session_state.sidebar_bg = u_set.get("sidebar_bg", "#f0f2f6")
                            st.session_state.sidebar_opacity = u_set.get("sidebar_opacity", 0.9)
                            st.session_state.text_color = u_set.get("text_color", "#31333F")
                            st.session_state.bg_image_url = u_set.get("bg_image_url", None)
                            st.session_state.avatar_url = u_set.get("avatar_url", None)
                            st.session_state.current_menu = "1. Nhập Sản Lượng"
                            
                            st.success("Đăng nhập thành công!")
                            st.rerun()
                        else:
                            st.error("Sai tên đăng nhập hoặc mật khẩu!")
                    else:
                        st.error("Sai tên đăng nhập hoặc mật khẩu!")
                        
        with tab_register:
            with st.form("register_form"):
                rg_user = st.text_input("Tên đăng nhập mới")
                rg_staff_name = st.text_input("Tên hiển thị nhân sự (Ví dụ: Nguyễn Văn A)")
                rg_pass = st.text_input("Mật khẩu mới", type="password")
                rg_pass_confirm = st.text_input("Xác nhận lại mật khẩu", type="password")
                submit_rg = st.form_submit_button("Đăng Ký", use_container_width=True)
                
                if submit_rg:
                    if not rg_user or not rg_pass or not rg_staff_name:
                        st.warning("Vui lòng điền đầy đủ tên đăng nhập, tên nhân sự và mật khẩu!")
                    elif rg_pass != rg_pass_confirm:
                        st.error("Mật khẩu xác nhận không khớp!")
                    else:
                        latest_fresh = load_data()
                        current_accounts = latest_fresh.get("accounts", st.session_state.accounts)
                        
                        norm_existing = {}
                        for u, info in current_accounts.items():
                            if isinstance(info, dict):
                                norm_existing[u] = {"password": info.get("password", ""), "role": info.get("role", "nhan_vien"), "staff_name": info.get("staff_name", u)}
                            else:
                                norm_existing[u] = {"password": str(info), "role": "nhan_vien", "staff_name": u}
                                
                        if rg_user in norm_existing:
                            st.error("Tên đăng nhập này đã tồn tại!")
                        else:
                            norm_existing[rg_user] = {
                                "password": rg_pass, 
                                "role": "nhan_vien", 
                                "staff_name": rg_staff_name.strip()
                            }
                            st.session_state.accounts = norm_existing
                            save_data()
                            st.success("Đăng ký thành công! Bạn có thể chuyển sang tab Đăng Nhập.")
    st.stop()

if st.session_state.role == "admin" and HAS_AUTOREFRESH:
    refresh_interval_ms = int(st.session_state.get("auto_refresh_minutes", 5)) * 60 * 1000
    st_autorefresh(interval=refresh_interval_ms, key="admin_global_auto_refresh")

user_settings_dict = saved_data.get("user_settings", {}).get(st.session_state.username, {})

if "rules_df" not in st.session_state:
    r_data = saved_data.get("rules_df")
    st.session_state.rules_df = pd.DataFrame(r_data) if r_data else pd.DataFrame(master_rules)

default_input_columns = ["STT", "Ngày", "Tài Khoản Tạo", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"]
if "input_df" not in st.session_state:
    in_data = saved_data.get("input_df")
    st.session_state.input_df = pd.DataFrame(in_data) if in_data else pd.DataFrame(columns=default_input_columns)

for col in default_input_columns:
    if col not in st.session_state.input_df.columns:
        st.session_state.input_df[col] = ""

if "attendance_df" not in st.session_state:
    att_data = saved_data.get("attendance_df")
    st.session_state.attendance_df = pd.DataFrame(att_data) if att_data else pd.DataFrame(columns=["STT", "Ngày", "Nhân Sự", "Giờ Vào Ca", "Giờ Ra Ca", "Số Phút Làm Việc", "Ghi Chú"])

if "deleted_input_df" not in st.session_state:
    del_data = saved_data.get("deleted_input_df")
    st.session_state.deleted_input_df = pd.DataFrame(del_data) if del_data else pd.DataFrame(columns=default_input_columns)

for col in default_input_columns:
    if col not in st.session_state.deleted_input_df.columns:
        st.session_state.deleted_input_df[col] = ""

if "chart_colors" not in st.session_state:
    st.session_state.chart_colors = saved_data.get("chart_colors", default_chart_colors)
if "folders" not in st.session_state:
    st.session_state.folders = saved_data.get("folders", default_folders)

if "primary_color" not in st.session_state:
    st.session_state.primary_color = user_settings_dict.get("primary_color", "#ff4b4b")
if "bg_color" not in st.session_state:
    st.session_state.bg_color = user_settings_dict.get("bg_color", "#ffffff")
if "sidebar_bg" not in st.session_state:
    st.session_state.sidebar_bg = user_settings_dict.get("sidebar_bg", "#f0f2f6")
if "sidebar_opacity" not in st.session_state:
    st.session_state.sidebar_opacity = user_settings_dict.get("sidebar_opacity", 0.9)
if "text_color" not in st.session_state:
    st.session_state.text_color = user_settings_dict.get("text_color", "#31333F")
if "bg_image_url" not in st.session_state:
    st.session_state.bg_image_url = user_settings_dict.get("bg_image_url", None)
if "avatar_url" not in st.session_state:
    st.session_state.avatar_url = user_settings_dict.get("avatar_url", None)

if "current_menu" not in st.session_state:
    st.session_state.current_menu = "1. Nhập Sản Lượng"

if not st.session_state.input_df.empty:
    st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
if not st.session_state.attendance_df.empty:
    if "Ghi Chú" not in st.session_state.attendance_df.columns:
        st.session_state.attendance_df["Ghi Chú"] = ""
    st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)

bg_style = f"background-color: {st.session_state.bg_color};"
if st.session_state.bg_image_url:
    bg_style = f"background-image: url({st.session_state.bg_image_url}); background-size: cover; background-repeat: no-repeat; background-position: center; background-attachment: fixed;"

def hex_to_rgba(hex_str, opacity):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"
    except:
        return f"rgba(240, 242, 246, {opacity})"

sidebar_rgba = hex_to_rgba(st.session_state.sidebar_bg, st.session_state.sidebar_opacity)

st.markdown(f"""
<style>
    .stApp {{
        {bg_style}
        color: {st.session_state.text_color} !important;
    }}
    
    p, span, label, div, h1, h2, h3, h4, h5, h6, 
    .stMarkdown, [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"], [data-testid="stMetricValue"], [data-testid="stMetricLabel"],
    [data-testid="stWidgetLabel"] *, .streamlit-expanderHeader *,
    [data-testid="stDataEditor"] *, [data-testid="stDataFrame"] *, [data-testid="stTable"] *,
    .stSelectbox *, .stDateInput *, .stNumberInput *, .stTextInput *, .stTimeInput *,
    table, th, td, tr, [class*="css-"], 
    div[data-baseweb="select"] *, span[title], 
    div[data-testid="stDataFrame"] div, div[data-testid="stDataEditor"] div,
    canvas {{
        color: {st.session_state.text_color} !important;
    }}
    
    h1 {{
        color: {st.session_state.primary_color} !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: {sidebar_rgba} !important;
        backdrop-filter: blur(8px);
    }}
    
    [data-testid="stSidebar"] > div:first-child {{
        display: flex;
        flex-direction: column;
        height: 100vh;
        overflow-y: auto !important;
        padding: 0px !important;
    }}
    
    [data-testid="stSidebar"] * {{
        color: {st.session_state.text_color} !important;
    }}
    
    .fixed-avatar-container {{
        position: sticky;
        top: 0;
        z-index: 999999;
        background-color: {sidebar_rgba};
        padding-top: 15px;
        padding-bottom: 15px;
        border-bottom: 2px solid {st.session_state.primary_color};
        margin-bottom: 10px;
        text-align: center;
        flex-shrink: 0;
        backdrop-filter: blur(8px);
    }}

    .sidebar-scrollable-content {{
        flex-grow: 1;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 50px;
    }}

    .avatar-wrapper {{
        position: relative;
        width: 140px;
        height: 140px;
        margin: 0 auto;
    }}
    
    .avatar-popover-wrapper {{
        position: absolute;
        bottom: 2px;
        right: 10px;
        z-index: 9999999;
    }}
    .avatar-popover-wrapper [data-testid="stPopover"] button {{
        background-color: #ffffff !important;
        border: 2px solid {st.session_state.primary_color} !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        padding: 0px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }}
    .avatar-popover-wrapper [data-testid="stPopover"] button p {{
        display: none !important;
    }}
    .avatar-popover-wrapper [data-testid="stPopover"] button::after {{
        content: "⋮";
        font-size: 16px;
        font-weight: bold;
        color: #333333;
        line-height: 1;
    }}

    @media (max-width: 768px) {{
        .stApp {{
            padding: 2px !important;
        }}
        h1 {{
            font-size: 1.3rem !important;
        }}
        [data-testid="column"] {{
            width: 100% !important;
            flex: 100% !important;
            min-width: 100% !important;
        }}
        .stButton button {{
            width: 100% !important;
            margin-bottom: 5px;
        }}
    }}
</style>
""", unsafe_allow_html=True)

@st.fragment
def render_avatar_widget():
    has_custom_avatar = False
    if st.session_state.avatar_url:
        has_custom_avatar = True

    st.markdown('<div class="avatar-wrapper">', unsafe_allow_html=True)
    
    if has_custom_avatar:
        with st.popover(" ", use_container_width=False):
            st.markdown("##### 🔍 Xem Ảnh Đại Diện")
            st.image(st.session_state.avatar_url, use_container_width=True)
            
        st.markdown(f"""
        <div style="cursor: pointer; text-align: center;">
            <img src="{st.session_state.avatar_url}" style="width:140px; height:140px; border-radius:50%; object-fit:cover; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3);">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="width:140px; height:140px; border-radius:50%; background:#cbd5e1; display:flex; align-items:center; justify-content:center; font-size:50px; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3); margin: 0 auto;">
            👤
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="avatar-popover-wrapper">', unsafe_allow_html=True)
    with st.popover(" "):
        st.markdown("##### ⚙️ Cài Đặt Ảnh Đại Diện Riêng")
        avatar_file = st.file_uploader("Tải ảnh", type=["png", "jpg", "jpeg"], key="avatar_uploader_popover", label_visibility="collapsed")
        if avatar_file is not None:
            with st.spinner("Đang tải lên Supabase..."):
                avatar_public_url = upload_image_to_supabase(avatar_file, folder_prefix="avatars")
            if avatar_public_url:
                st.session_state.avatar_url = avatar_public_url
                save_data()
                st.success("Đã cập nhật ảnh đại diện cá nhân!")
            
        if st.session_state.avatar_url:
            st.markdown("---")
            if st.button("🗑️ Xóa Ảnh Đại Diện", use_container_width=True, key="del_avatar_btn"):
                st.session_state.avatar_url = None
                save_data()
                st.success("Đã xóa ảnh đại diện!")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with st.sidebar:
    role_label = "👑 Quản Trị Viên" if st.session_state.role == "admin" else "👤 Nhân Viên"
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.7); padding: 8px 12px; border-radius: 6px; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); text-align: center;">
        <span style="font-size: 0.9rem;">{role_label}: <b>{st.session_state.username}</b></span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Đăng Xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = "nhan_vien"
        st.rerun()

    st.markdown('<div class="fixed-avatar-container">', unsafe_allow_html=True)
    render_avatar_widget()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-scrollable-content">', unsafe_allow_html=True)

    if st.button("🔄 Cập Nhật", use_container_width=True):
        st.cache_data.clear()
        latest_data = load_data()
        if "accounts" in latest_data:
            raw_accs = latest_data["accounts"]
            norm_accs = {}
            for u, info in raw_accs.items():
                if isinstance(info, dict):
                    norm_accs[u] = {"password": info.get("password", ""), "role": info.get("role", "nhan_vien"), "staff_name": info.get("staff_name", u)}
                else:
                    norm_accs[u] = {"password": str(info), "role": "nhan_vien", "staff_name": u}
            st.session_state.accounts = norm_accs
            st.session_state.account_staff_map = {u: info["staff_name"] for u, info in norm_accs.items() if u != "admin"}
            st.session_state.staff_list = list(st.session_state.account_staff_map.values())
        if "input_df" in latest_data:
            st.session_state.input_df = pd.DataFrame(latest_data["input_df"])
        if "attendance_df" in latest_data:
            st.session_state.attendance_df = pd.DataFrame(latest_data["attendance_df"])
        if "rules_df" in latest_data:
            st.session_state.rules_df = pd.DataFrame(latest_data["rules_df"])
        if "deleted_input_df" in latest_data:
            st.session_state.deleted_input_df = pd.DataFrame(latest_data["deleted_input_df"])
        if "auto_refresh_minutes" in latest_data:
            st.session_state.auto_refresh_minutes = latest_data["auto_refresh_minutes"]
            
        st.success("Đã đồng bộ toàn bộ dữ liệu mới nhất thành công!")
        st.rerun()

    if st.button("⏱️ Chấm Công Ca Làm Việc", use_container_width=True):
        st.session_state.current_menu = "⏱️ Chấm Công Ca Làm Việc"
        save_data()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📂 CHỨC NĂNG HỆ THỐNG")

    for f_idx, folder in enumerate(st.session_state.folders):
        with st.expander(folder["folder_name"], expanded=True):
            for item in folder["items"]:
                if st.session_state.role != "admin" and item["id"] == "menu_4":
                    continue
                
                if st.button(item["name"], use_container_width=True, key=f"btn_{item['id']}"):
                    st.session_state.current_menu = item["name"]
                    save_data()
                    st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Cấu Hình Hệ Thống")
    
    if st.session_state.role == "admin":
        if st.button("👥 Quản Lý Tài Khoản", use_container_width=True):
            st.session_state.current_menu = "Quản Lý Tài Khoản"
            save_data()
            st.rerun()
            
    if st.button("📁 Quản Lý Thư Mục & Menu", use_container_width=True):
        st.session_state.current_menu = "📁 Quản Lý Thư Mục & Menu"
        save_data()
        st.rerun()
    if st.button("🎨 Cài Đặt Giao Diện Riêng", use_container_width=True):
        st.session_state.current_menu = "🎨 Cài Đặt Giao Diện"
        save_data()
        st.rerun()
        
    if st.session_state.role == "admin":
        if st.button("🧹 Làm Sạch & Tối Ưu Dữ Liệu", use_container_width=True):
            st.session_state.current_menu = "🧹 Làm Sạch Dữ Liệu"
            save_data()
            st.rerun()

    st.markdown("---")
    st.markdown("### 🟢 Trạng Thái Hệ Thống")
    db_status = "🟢 Supabase Đã Kết Nối" if supabase is not None else "🟡 Dùng Bộ Nhớ Cục Bộ"
    st.markdown(f"<small>{db_status}</small>", unsafe_allow_html=True)
    st.markdown(f"<small>🔗 Ping Health: <a href='./_stcore/health' target='_blank'>Online</a></small>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

menu = st.session_state.current_menu

def get_feature_type(menu_name):
    if menu_name == "Quản Lý Tài Khoản":
        return "manage_accounts"
    if menu_name == "⏱️ Chấm Công Ca Làm Việc":
        return "attendance"
    if menu_name == "📁 Quản Lý Thư Mục & Menu":
        return "manage_folders"
    if menu_name == "🎨 Cài Đặt Giao Diện":
        return "settings_ui"
    if menu_name == "🧹 Làm Sạch Dữ Liệu":
        return "clean_data"
        
    for folder in st.session_state.folders:
        for item in folder["items"]:
            if item["name"] == menu_name:
                item_id = item["id"]
                if item_id == "menu_1": return "input_production"
                if item_id == "menu_2": return "report"
                if item_id == "menu_3": return "rules"
                if item_id == "menu_4": return "trash"
                return "input_production"
    return "input_production"

feature = get_feature_type(menu)

# ==================== QUẢN LÝ TÀI KHOẢN (DÀNH CHO ADMIN) ====================
if feature == "manage_accounts":
    if st.session_state.role != "admin":
        st.error("⚠️ Bạn không có quyền truy cập trang này!")
    else:
        st.header("👥 Quản Lý Tài Khoản Hệ Thống")
        st.markdown("Thay đổi mật khẩu, tên nhân sự, quyền hạn hoặc chọn **Xóa** tài khoản khỏi hệ thống.")
        
        fresh_load = load_data()
        if "accounts" in fresh_load and isinstance(fresh_load["accounts"], dict):
            norm_accs = {}
            for u, info in fresh_load["accounts"].items():
                if isinstance(info, dict):
                    norm_accs[u] = {"password": info.get("password", ""), "role": info.get("role", "admin" if u == "admin" else "nhan_vien"), "staff_name": info.get("staff_name", u)}
                else:
                    norm_accs[u] = {"password": str(info), "role": "admin" if u == "admin" else "nhan_vien", "staff_name": u}
            st.session_state.accounts = norm_accs
            st.session_state.account_staff_map = {u: info["staff_name"] for u, info in norm_accs.items() if u != "admin"}
            st.session_state.staff_list = list(st.session_state.account_staff_map.values())
            
        acc_data = []
        for u, info in st.session_state.accounts.items():
            pass_val = info.get("password", "") if isinstance(info, dict) else str(info)
            s_name = info.get("staff_name", u) if isinstance(info, dict) else u
            r_val = info.get("role", "admin" if u == "admin" else "nhan_vien") if isinstance(info, dict) else ("admin" if u == "admin" else "nhan_vien")
            acc_data.append({
                "Xóa": False,
                "Tên Đăng Nhập": u, 
                "Tên Nhân Sự": s_name,
                "Mật Khẩu": pass_val,
                "Quyền Hạn": r_val
            })
        
        acc_df = pd.DataFrame(acc_data)
        
        with st.form("manage_acc_form"):
            edited_acc = st.data_editor(
                acc_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Xóa": st.column_config.CheckboxColumn("Xóa tài khoản", default=False),
                    "Tên Đăng Nhập": st.column_config.TextColumn("Tên Đăng Nhập", disabled=True),
                    "Tên Nhân Sự": st.column_config.TextColumn("Tên Nhân Sự"),
                    "Mật Khẩu": st.column_config.TextColumn("Mật Khẩu"),
                    "Quyền Hạn": st.column_config.SelectboxColumn(
                        "Quyền Hạn",
                        options=["admin", "nhan_vien"],
                        required=True
                    )
                }
            )
            save_acc_btn = st.form_submit_button("💾 Lưu Thay Đổi / Xóa Tài Khoản", use_container_width=True)
            
            if save_acc_btn:
                new_accounts = {}
                deleted_users = []
                for idx, row in edited_acc.iterrows():
                    u = row["Tên Đăng Nhập"]
                    s_name = row["Tên Nhân Sự"]
                    p = row["Mật Khẩu"]
                    r = row["Quyền Hạn"]
                    is_deleted = row["Xóa"]
                    
                    if is_deleted:
                        deleted_users.append(u)
                    else:
                        new_accounts[u] = {"password": p, "role": r, "staff_name": s_name.strip() if s_name else u}
                
                if not any(info.get("role") == "admin" for info in new_accounts.values()):
                    st.error("⚠️ Không thể xóa toàn bộ tài khoản Admin! Hệ thống cần ít nhất một Admin hoạt động.")
                else:
                    st.session_state.accounts = new_accounts
                    st.session_state.account_staff_map = {u: info["staff_name"] for u, info in new_accounts.items() if u != "admin"}
                    st.session_state.staff_list = list(st.session_state.account_staff_map.values())
                    
                    if deleted_users:
                        if not st.session_state.input_df.empty and "Tài Khoản Tạo" in st.session_state.input_df.columns:
                            st.session_state.input_df = st.session_state.input_df[~st.session_state.input_df["Tài Khoản Tạo"].isin(deleted_users)].reset_index(drop=True)
                            if not st.session_state.input_df.empty:
                                st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                                
                        latest_all = load_data()
                        if "user_settings" in latest_all:
                            for du in deleted_users:
                                latest_all["user_settings"].pop(du, None)
                                
                    save_data()
                    
                    if deleted_users:
                        st.success(f"Đã xóa vĩnh viễn tài khoản và toàn bộ dữ liệu của các tài khoản: {', '.join(deleted_users)}!")
                    else:
                        st.success("Đã cập nhật thông tin tài khoản thành công!")
                    st.rerun()

# ==================== 1. NHẬP SẢN LƯỢNG ====================
elif feature == "input_production":
    now_vn = datetime.datetime.now(VN_TIMEZONE)
    today_str = str(now_vn.date())
    
    active_staff = []
    inactive_staff = []
    if not st.session_state.attendance_df.empty:
        today_att = st.session_state.attendance_df[st.session_state.attendance_df["Ngày"] == today_str]
        checked_in_set = set(today_att[today_att["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist())
    else:
        checked_in_set = set()

    for s in st.session_state.staff_list:
        if s in checked_in_set:
            active_staff.append(s)
        else:
            inactive_staff.append(s)

    st.subheader(f"{menu} ({today_str})")

    if not st.session_state.staff_list:
        st.warning("⚠️ Danh sách nhân sự hiện đang trống. Vui lòng đăng ký tài khoản con kèm tên nhân sự để hệ thống tự động cập nhật!")
    elif not active_staff:
        st.warning(f"⚠️ Hôm nay ({today_str}) chưa có nhân sự nào **Check-in (Vào ca)** hoặc đã Check-out. Vui lòng thực hiện Check-in trước khi nhập sản lượng!")
    else:
        st.info("💡 Mẹo trên điện thoại: Có thể chụp ảnh trực tiếp từ camera điện thoại hoặc tải ảnh có sẵn.")
        
        with st.form("entry_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                ngay = st.date_input("Ngày làm việc", now_vn.date(), disabled=True)
            with f_col2:
                nhan_su = st.selectbox("Nhân sự thực hiện", active_staff)
            with f_col3:
                danh_sach_hang_muc = st.session_state.rules_df["Hạng Mục Công Việc"].tolist()
                hang_muc = st.selectbox("Hạng mục công việc", danh_sach_hang_muc)
                
            img_source = st.radio("Nguồn ảnh:", ["Tải lên / Kéo thả", "Chụp trực tiếp"], horizontal=True)
            if img_source == "Chụp trực tiếp":
                record_image = st.camera_input("Chụp ảnh công việc (Bắt buộc)")
            else:
                record_image = st.file_uploader("Tải ảnh đính kèm (Bắt buộc)", type=["png", "jpg", "jpeg"], key="record_img")
                    
            f_col4, f_col5 = st.columns(2)
            with f_col4:
                so_luong = st.number_input("Số lượng thực tế", min_value=1, value=100, step=1)
            with f_col5:
                ghi_chu = st.text_input("Ghi chú", "")
                
            submitted = st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True)

            if submitted:
                is_valid = True
                missing_fields = []
                if not nhan_su:
                    is_valid = False
                    missing_fields.append("Nhân sự thực hiện")
                if not hang_muc:
                    is_valid = False
                    missing_fields.append("Hạng mục công việc")
                if record_image is None:
                    is_valid = False
                    missing_fields.append("Ảnh đính kèm / Chụp ảnh công việc")

                if not is_valid:
                    st.error(f"⚠️ Vui lòng hoàn thành các mục bắt buộc: {', '.join(missing_fields)}")
                else:
                    with st.spinner("Đang tải ảnh lên Supabase Storage..."):
                        img_url = upload_image_to_supabase(record_image, folder_prefix="production") if record_image is not None else ""
                    
                    row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
                    he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
                    don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
                    tong_diem = so_luong * he_so
                    
                    new_row = {
                        "STT": 1,
                        "Ngày": today_str,
                        "Tài Khoản Tạo": st.session_state.username,
                        "Nhân Sự": nhan_su,
                        "Hạng Mục Công Việc": hang_muc,
                        "Hình Ảnh": img_url,
                        "Đơn Vị": don_vi,
                        "Số Lượng": so_luong,
                        "Hệ Số Điểm": he_so,
                        "Tổng Điểm": round(tong_diem, 2),
                        "Ghi Chú": ghi_chu
                    }
                    safe_merge_and_save("input_df", pd.DataFrame([new_row]))
                    st.success(f"Đã báo cáo sản lượng thành công cho **{nhan_su}**! Tổng điểm: **{tong_diem} điểm**")
                    st.rerun()

    st.markdown("---")
    st.subheader("Bảng Tin")
    
    # Luôn tải dữ liệu mới nhất từ cloud/storage để hiển thị toàn bộ bản ghi không bị thiếu
    latest_storage = load_data()
    latest_input_list = latest_storage.get("input_df", [])
    current_input_df = pd.DataFrame(latest_input_list) if latest_input_list else st.session_state.input_df.copy()
    
    if not current_input_df.empty:
        current_input_df["STT"] = range(1, len(current_input_df) + 1)
        
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            all_dates = ["Tất cả"] + sorted(current_input_df["Ngày"].unique().tolist())
            filter_date = st.selectbox("Lọc theo Ngày", all_dates)
        with s_col2:
            all_staff = ["Tất cả"] + sorted(current_input_df["Nhân Sự"].unique().tolist())
            filter_staff = st.selectbox("Lọc theo Nhân Sự", all_staff)
        
        filtered_df = current_input_df.copy()
        if filter_date != "Tất cả":
            filtered_df = filtered_df[filtered_df["Ngày"] == filter_date]
        if filter_staff != "Tất cả":
            filtered_df = filtered_df[filtered_df["Nhân Sự"] == filter_staff]
            
        if not filtered_df.empty:
            filtered_df["STT"] = range(1, len(filtered_df) + 1)
            filtered_df = filtered_df.iloc[::-1].reset_index(drop=True)
            
            with st.form("input_delete_form"):
                for idx, row in filtered_df.iterrows():
                    row_c1, row_c2 = st.columns([4, 1])
                    with row_c1:
                        acc_creator = row.get('Tài Khoản Tạo', 'Admin')
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem; line-height: 1.3;">
                            <b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} &nbsp;|&nbsp; 💻 Tài khoản nhập: <b>{acc_creator}</b><br>
                            👤 Nhân sự: <b>{row['Nhân Sự']}</b> &nbsp;|&nbsp; 📌 {row['Hạng Mục Công Việc']}<br>
                            📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                            💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        is_selected = st.checkbox(f"Xóa bản ghi STT {row['STT']}", key=f"chk_{row['STT']}")
                        filtered_df.loc[idx, "Chọn_Xóa"] = is_selected
                        
                    with row_c2:
                        img_url_val = row.get("Hình Ảnh", "")
                        if img_url_val and isinstance(img_url_val, str):
                            try:
                                st.image(img_url_val, width=50)
                                with st.popover("🔍 Phóng to"):
                                    st.image(img_url_val, use_container_width=True)
                            except Exception:
                                st.text("Lỗi hiển thị ảnh")
                    st.markdown("---")
                    
                delete_submitted = st.form_submit_button("🗑️ Xóa Các Dòng Đã Tích Chọn", use_container_width=True)
                if delete_submitted:
                    selected_rows = filtered_df[filtered_df["Chọn_Xóa"] == True]
                    if not selected_rows.empty:
                        stt_to_remove = selected_rows["STT"].tolist()
                        rows_to_delete = current_input_df[current_input_df["STT"].isin(stt_to_remove)]
                        st.session_state.deleted_input_df = pd.concat([st.session_state.deleted_input_df, rows_to_delete], ignore_index=True)
                        
                        st.session_state.input_df = current_input_df[~current_input_df["STT"].isin(stt_to_remove)].reset_index(drop=True)
                        st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                        
                        if not st.session_state.deleted_input_df.empty:
                            st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
                            
                        save_data()
                        st.success("Đã chuyển các dòng đã chọn vào thùng rác thành công!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn ít nhất một dòng để xóa!")
        else:
            st.info("Không tìm thấy bản ghi nào khớp với bộ lọc.")
    else:
        st.info("Chưa có dữ liệu sản lượng nào.")

# ==================== CHẤM CÔNG CA LÀM VIỆC ====================
elif feature == "attendance":
    st.header(menu)
    st.markdown("Thực hiện Check-in và Check-out theo múi giờ Việt Nam (GMT+7). Hệ thống sẽ tự động tính số phút làm việc từ lúc Check-in đến khi Check-out.")
    
    latest_att_storage = load_data()
    latest_att_list = latest_att_storage.get("attendance_df", [])
    st.session_state.attendance_df = pd.DataFrame(latest_att_list) if latest_att_list else st.session_state.attendance_df

    now_vn = datetime.datetime.now(VN_TIMEZONE)
    today_str = str(now_vn.date())
    
    active_staff = []
    inactive_staff = []
    if not st.session_state.attendance_df.empty:
        today_att = st.session_state.attendance_df[st.session_state.attendance_df["Ngày"] == today_str]
        checked_in_set = set(today_att[today_att["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist())
    else:
        checked_in_set = set()

    for s in st.session_state.staff_list:
        if s in checked_in_set:
            active_staff.append(s)
        else:
            inactive_staff.append(s)

    sorted_staff_status = active_staff + inactive_staff
    staff_status_lines = ""
    for s in sorted_staff_status:
        if s in checked_in_set:
            staff_status_lines += f"🟢 <b>{s}</b> - Đang Làm Việc<br>"
        else:
            staff_status_lines += f"🔴 <b>{s}</b> - Không hoạt động<br>"
        
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.7); padding: 10px 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(4px);">
        <h4 style="margin-top:0; margin-bottom:8px;">📌 Trạng Thái Hôm Nay ({today_str})</h4>
        {staff_status_lines if staff_status_lines else 'Chưa có nhân sự nào trong hệ thống.'}
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.staff_list:
        st.warning("⚠️ Danh sách nhân sự đang trống. Vui lòng đăng ký tài khoản con kèm tên nhân sự.")
    else:
        with st.form("attendance_form"):
            f_att1, f_att2, f_att3 = st.columns(3)
            with f_att1:
                att_date = st.date_input("Ngày chấm công", now_vn.date(), key="att_date")
            with f_att2:
                att_staff = st.selectbox("Nhân sự", st.session_state.staff_list, key="att_staff")
            with f_att3:
                att_note = st.text_input("Ghi chú ca", "", key="att_note")
                
            b_att1, b_att2 = st.columns(2)
            with b_att1:
                check_in_clicked = st.form_submit_button("🟢 Check-in (Vào ca)", use_container_width=True)
            with b_att2:
                check_out_clicked = st.form_submit_button("🔴 Check-out (Kết thúc ca)", use_container_width=True)
                
            current_time_str = now_vn.strftime("%H:%M:%S")
            
            if check_in_clicked:
                latest_fresh = load_data()
                if "attendance_df" in latest_fresh:
                    st.session_state.attendance_df = pd.DataFrame(latest_fresh["attendance_df"])

                already_active = False
                if not st.session_state.attendance_df.empty:
                    active_check = (st.session_state.attendance_df["Nhân Sự"] == att_staff) & \
                                   (st.session_state.attendance_df["Ngày"] == str(att_date)) & \
                                   (st.session_state.attendance_df["Giờ Ra Ca"] == "Chưa kết thúc")
                    if active_check.any():
                        already_active = True

                if already_active:
                    st.warning(f"⚠️ Nhân sự **{att_staff}** đang trong ca làm việc, không thể Check-in lại khi chưa Check-out!")
                else:
                    new_att_row = {
                        "STT": 1,
                        "Ngày": str(att_date),
                        "Nhân Sự": att_staff,
                        "Giờ Vào Ca": current_time_str,
                        "Giờ Ra Ca": "Chưa kết thúc",
                        "Số Phút Làm Việc": 0,
                        "Ghi Chú": att_note
                    }
                    safe_merge_and_save("attendance_df", pd.DataFrame([new_att_row]))
                    st.success(f"Đã ghi nhận **Vào ca** cho **{att_staff}** lúc {current_time_str}!")
                    st.rerun()
                
            if check_out_clicked:
                latest_fresh = load_data()
                if "attendance_df" in latest_fresh:
                    st.session_state.attendance_df = pd.DataFrame(latest_fresh["attendance_df"])

                if not st.session_state.attendance_df.empty:
                    mask = (st.session_state.attendance_df["Nhân Sự"] == att_staff) & \
                           (st.session_state.attendance_df["Ngày"] == str(att_date)) & \
                           (st.session_state.attendance_df["Giờ Ra Ca"] == "Chưa kết thúc")
                    if mask.any():
                        in_time_str = st.session_state.attendance_df.loc[mask, "Giờ Vào Ca"].values[0]
                        try:
                            t_in = datetime.datetime.strptime(in_time_str, "%H:%M:%S")
                            t_out = datetime.datetime.strptime(current_time_str, "%H:%M:%S")
                            diff_minutes = int((t_out - t_in).total_seconds() / 60)
                            if diff_minutes < 0:
                                diff_minutes = 0
                        except Exception:
                            diff_minutes = 0

                        st.session_state.attendance_df.loc[mask, "Giờ Ra Ca"] = current_time_str
                        st.session_state.attendance_df.loc[mask, "Số Phút Làm Việc"] = diff_minutes
                        if att_note:
                            old_note = str(st.session_state.attendance_df.loc[mask, "Ghi Chú"].values[0])
                            if old_note and old_note != "nan":
                                st.session_state.attendance_df.loc[mask, "Ghi Chú"] = f"{old_note} | {att_note}"
                            else:
                                st.session_state.attendance_df.loc[mask, "Ghi Chú"] = att_note
                            
                        save_data()
                        st.success(f"Đã ghi nhận **Kết thúc ca** cho **{att_staff}** lúc {current_time_str}. Tổng thời gian làm việc: **{diff_minutes} phút**!")
                        st.rerun()
                    else:
                        st.warning(f"⚠️ Nhân sự **{att_staff}** chưa được Check-in trong ngày hôm nay để có thể Check-out!")
                else:
                    st.warning("Chưa có lịch sử chấm công nào trong hệ thống!")

    st.markdown("---")
    st.subheader("📋 Lịch Sử Chấm Công & Số Phút Làm Việc")
    if not st.session_state.attendance_df.empty:
        st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)
        att_display = st.session_state.attendance_df.copy()
        att_display.insert(0, "Chọn", False)
        
        with st.form("att_delete_form"):
            edited_att = st.data_editor(
                att_display,
                hide_index=True,
                use_container_width=True,
                key="att_editor"
            )
            delete_att_btn = st.form_submit_button("🗑️ Xóa Các Dòng Chấm Công Đã Chọn", use_container_width=True)
            if delete_att_btn:
                selected_att = edited_att[edited_att["Chọn"] == True]
                if not selected_att.empty:
                    stt_to_remove = selected_att["STT"].tolist()
                    st.session_state.attendance_df = st.session_state.attendance_df[~st.session_state.attendance_df["STT"].isin(stt_to_remove)].reset_index(drop=True)
                    if not st.session_state.attendance_df.empty:
                        st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)
                    save_data()
                    st.success("Đã xóa các dòng lịch sử chấm công được chọn!")
                    st.rerun()
                else:
                    st.warning("Vui lòng tích chọn ít nhất một dòng để xóa!")
    else:
        st.info("Chưa có dữ liệu lịch sử chấm công.")

    st.markdown("---")
    st.subheader("⏱️ Tổng Thời Gian & Số Ngày Làm Việc Tích Lũy Theo Nhân Sự")
    if not st.session_state.attendance_df.empty:
        accumulated_df = st.session_state.attendance_df.groupby("Nhân Sự")["Số Phút Làm Việc"].sum().reset_index()
        accumulated_df.columns = ["Nhân Sự", "Tổng Thời Gian (Phút)"]
        accumulated_df["Số Ngày Làm Việc"] = (accumulated_df["Tổng Thời Gian (Phút)"] / 480.0).round(2)
        accumulated_df = accumulated_df.sort_values(by="Tổng Thời Gian (Phút)", ascending=False).reset_index(drop=True)
        accumulated_df.insert(0, "STT", range(1, len(accumulated_df) + 1))
        
        st.dataframe(
            accumulated_df.style.format({
                "Tổng Thời Gian (Phút)": "{:,.0f}",
                "Số Ngày Làm Việc": "{:,.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Chưa có dữ liệu tích lũy thời gian.")

# ==================== BÁO CÁO & BIỂU ĐỒ ====================
elif feature == "report":
    st.header(menu)
    
    latest_report_storage = load_data()
    latest_report_input_list = latest_report_storage.get("input_df", [])
    current_report_df = pd.DataFrame(latest_report_input_list) if latest_report_input_list else st.session_state.input_df.copy()
    
    all_staff_current = st.session_state.staff_list
    
    if not all_staff_current:
        st.warning("⚠️ Danh sách nhân sự đang trống. Vui lòng đăng ký tài khoản con để thêm nhân sự hiển thị báo cáo.")
    else:
        if not current_report_df.empty:
            df_in = current_report_df.copy()
            df_in["Tổng Điểm"] = pd.to_numeric(df_in["Tổng Điểm"], errors="coerce").fillna(0)
            summary = df_in.groupby("Nhân Sự").agg(
                Tổng_Số_Lượng=("Số Lượng", "sum"),
                Tổng_Điểm=("Tổng Điểm", "sum")
            ).reindex(all_staff_current).fillna(0).reset_index()
        else:
            summary = pd.DataFrame({
                "Nhân Sự": all_staff_current,
                "Tổng_Số_Lượng": [0.0] * len(all_staff_current),
                "Tổng_Điểm": [0.0] * len(all_staff_current)
            })
            
        summary["Tổng_Điểm"] = pd.to_numeric(summary["Tổng_Điểm"], errors="coerce").fillna(0)
        total_all_points = summary["Tổng_Điểm"].sum()
        summary["Tỷ_Lệ_Đóng_Góp"] = summary["Tổng_Điểm"].apply(lambda x: (x / total_all_points) if total_all_points > 0 else 0)
        
        def rank_func(pts):
            if pts >= 700:
                return "Xuất Sắc"
            elif pts >= 400:
                return "Đạt"
            else:
                return "Cần Cố Gắn"
                
        summary["Xếp_Loại"] = summary["Tổng_Điểm"].apply(rank_func)
        
        st.subheader("Bảng Tổng Kết Theo Nhân Sự")
        st.dataframe(
            summary.style.format({
                "Tổng_Số_Lượng": "{:,.0f}",
                "Tổng_Điểm": "{:,.1f}",
                "Tỷ_Lệ_Đóng_Góp": "{:.2%}"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        st.subheader("⚖️ Bảng Đối Chiếu Thời Gian Làm Việc & Sản Lượng")
        
        latest_att_storage = load_data()
        latest_att_list = latest_att_storage.get("attendance_df", [])
        current_att_df = pd.DataFrame(latest_att_list) if latest_att_list else st.session_state.attendance_df.copy()
        
        if not current_att_df.empty:
            att_summary = current_att_df.groupby("Nhân Sự")["Số Phút Làm Việc"].sum().reset_index()
            att_summary.columns = ["Nhân Sự", "Tổng Phút Làm Việc"]
        else:
            att_summary = pd.DataFrame({"Nhân Sự": all_staff_current, "Tổng Phút Làm Việc": 0})
            
        comparison_df = pd.merge(summary[["Nhân Sự", "Tổng_Điểm", "Tỷ_Lệ_Đóng_Góp"]], att_summary, on="Nhân Sự", how="outer").fillna(0)
        comparison_df = comparison_df.sort_values(by="Tỷ_Lệ_Đóng_Góp", ascending=False).reset_index(drop=True)
        
        rank_badges = []
        current_rank_num = 1
        for idx in range(len(comparison_df)):
            if idx > 0 and comparison_df.loc[idx, "Tổng_Điểm"] == comparison_df.loc[idx - 1, "Tổng_Điểm"]:
                rank_badges.append(rank_badges[-1])
            else:
                if idx > 0:
                    current_rank_num += 1
                else:
                    current_rank_num = 1
                    
                if current_rank_num == 1:
                    rank_badges.append("🥇 Hạng 1")
                elif current_rank_num == 2:
                    rank_badges.append("🥈 Hạng 2")
                elif current_rank_num == 3:
                    rank_badges.append("🥉 Hạng 3")
                else:
                    rank_badges.append(f"Top {current_rank_num}")
                
        comparison_df.insert(0, "Xếp Hạng", rank_badges)
        
        total_minutes_all = comparison_df["Tổng Phút Làm Việc"].sum()
        comparison_df["Tỷ_Lệ_Thời_Gian"] = comparison_df["Tổng Phút Làm Việc"].apply(lambda x: (x / total_minutes_all) if total_minutes_all > 0 else 0)
        comparison_df["Chênh_Lệch_%"] = comparison_df["Tỷ_Lệ_Đóng_Góp"] - comparison_df["Tỷ_Lệ_Thời_Gian"]
        
        comparison_table = comparison_df[["Xếp Hạng", "Nhân Sự", "Tổng Phút Làm Việc", "Tỷ_Lệ_Thời_Gian", "Tổng_Điểm", "Tỷ_Lệ_Đóng_Góp", "Chênh_Lệch_%"]].copy()
        comparison_table.columns = ["Xếp Hạng", "Nhân Sự", "Tổng Thời Gian (Phút)", "Tỷ Lệ Thời Gian (%)", "Tổng Điểm", "Tỷ Lệ Sản Lượng (%)", "Chênh Lệch (Sản Lượng - Thời Gian)"]
        
        st.dataframe(
            comparison_table.style.format({
                "Tổng Thời Gian (Phút)": "{:,.0f}",
                "Tỷ Lệ Thời Gian (%)": "{:.2%}",
                "Tổng Điểm": "{:,.1f}",
                "Tỷ Lệ Sản Lượng (%)": "{:.2%}",
                "Chênh Lệch (Sản Lượng - Thời Gian)": "{:+.2%}"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("📥 Xuất Dữ Liệu Báo Cáo")
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_summary = summary.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Tải Bảng Tổng Kết (CSV)",
                data=csv_summary,
                file_name=f"Tong_Ket_Nhan_Su_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_dl2:
            if not current_report_df.empty:
                csv_detail = current_report_df.drop(columns=["Hình Ảnh"], errors="ignore").to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Tải Chi Tiết Sản Lượng (CSV)",
                    data=csv_detail,
                    file_name=f"Chi_Tiet_San_Luong_{datetime.date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        st.markdown("---")
        st.subheader("🔍 Kiểm Tra Chi Tiết Theo Từng Tài Khoản Con")
        if not current_report_df.empty and "Tài Khoản Tạo" in current_report_df.columns:
            list_acc_created = sorted(current_report_df["Tài Khoản Tạo"].dropna().unique().tolist())
            selected_acc_filter = st.selectbox("Chọn tài khoản con:", ["Tất cả tài khoản"] + list_acc_created)
            
            filtered_acc_df = current_report_df.copy()
            if selected_acc_filter != "Tất cả tài khoản":
                filtered_acc_df = filtered_acc_df[filtered_acc_df["Tài Khoản Tạo"] == selected_acc_filter]
            st.dataframe(filtered_acc_df.drop(columns=["Hình Ảnh"], errors="ignore"), use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu phân loại theo tài khoản con.")

        st.markdown("---")
        st.subheader("Biểu Đồ & Chi Tiết Tỷ Lệ Đóng Góp")
        
        with st.expander("🎨 Tùy Chỉnh Màu Sắc Biểu Đồ", expanded=False):
            while len(st.session_state.chart_colors) < len(all_staff_current):
                st.session_state.chart_colors.append("#3b82f6")
            
            color_cols = st.columns(min(len(all_staff_current), 4) if len(all_staff_current) > 0 else 1)
            for i, staff_name in enumerate(all_staff_current):
                col_idx = i % len(color_cols)
                with color_cols[col_idx]:
                    st.session_state.chart_colors[i] = st.color_picker(f"Màu: {staff_name}", st.session_state.chart_colors[i], key=f"color_pick_{i}")
            if st.button("Lưu Màu Biểu Đồ", use_container_width=True):
                save_data()
                st.success("Đã cập nhật màu sắc biểu đồ!")
                st.rerun()

        chart_size = 3.2
        col_pie, col_details = st.columns([1, 1])
        
        with col_pie:
            total_pts_check = summary["Tổng_Điểm"].sum()
            if total_pts_check > 0:
                fig, ax = plt.subplots(figsize=(chart_size, chart_size), dpi=300)
                current_colors = st.session_state.chart_colors[:len(summary)]
                
                chart_values = pd.to_numeric(summary["Tổng_Điểm"], errors="coerce").fillna(0).tolist()
                max_pts = max(chart_values) if chart_values else 0
                explode_values = [0.02 + 0.05 * (pts / max_pts) if max_pts > 0 else 0.0 for pts in chart_values]

                wedges, texts, autotexts = ax.pie(
                    chart_values, 
                    labels=None, 
                    autopct=lambda pct: f"{pct:.1f}%" if pct >= 3.0 else "", 
                    startangle=90, 
                    colors=current_colors,
                    explode=explode_values,
                    shadow=False,
                    pctdistance=0.6
                )
                
                for autotext in autotexts:
                    autotext.set_fontsize(8)
                    autotext.set_weight("bold")
                    autotext.set_color("black")
                        
                ax.axis('equal')
                st.pyplot(fig)
            else:
                st.info("ℹ️ Chưa có dữ liệu sản lượng hoặc tổng điểm bằng 0, chưa thể hiển thị biểu đồ tỷ lệ.")
            
        with col_details:
            st.markdown("#### 📌 Chi Tiết Điểm Số & Tỷ Lệ")
            current_colors = st.session_state.chart_colors[:len(summary)]
            for i, row in summary.iterrows():
                color_box = current_colors[i] if i < len(current_colors) else "#3b82f6"
                staff_name = row["Nhân Sự"]
                staff_pts = float(row["Tổng_Điểm"]) if pd.notnull(row["Tổng_Điểm"]) else 0.0
                staff_pct = row["Tỷ_Lệ_Đóng_Góp"] * 100
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px; background: rgba(255,255,255,0.7); padding: 8px 10px; border-radius: 6px;">
                    <div style="width: 16px; height: 16px; background-color: {color_box}; border-radius: 4px; margin-right: 10px; flex-shrink: 0;"></div>
                    <div style="font-size: 0.9rem;">
                        <b>{staff_name}</b>: {staff_pts:,.1f} điểm (<b>{staff_pct:.1f}%</b>)
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ==================== THAM CHIẾU CÔNG VIỆC ====================
elif feature == "rules":
    st.header(menu)
    st.markdown("Chỉnh sửa trực tiếp tên công việc, đơn vị hoặc hệ số điểm ngay trên bảng dưới đây. Bạn có thể tự do thêm, sửa, xóa các mục mà không bị cố định cứng.")
    
    if not st.session_state.rules_df.empty:
        st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
        
    current_items = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else []
    deleted_items_list = [r for r in master_rules if r["Hạng Mục Công Việc"] not in current_items]
    
    if deleted_items_list:
        deleted_names = [item["Hạng Mục Công Việc"] for item in deleted_items_list]
        selected_to_restore = st.multiselect("Khôi phục hạng mục đã xóa:", deleted_names)
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("📥 Khôi Phục Đã Chọn", use_container_width=True):
                if selected_to_restore:
                    items_to_add = [item for item in deleted_items_list if item["Hạng Mục Công Việc"] in selected_to_restore]
                    restored_df = pd.DataFrame(items_to_add)
                    st.session_state.rules_df = pd.concat([st.session_state.rules_df, restored_df], ignore_index=True)
                    st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
                    save_data()
                    st.success("Đã khôi phục thành công!")
                    st.rerun()
                else:
                    st.warning("Vui lòng chọn mục cần khôi phục!")
        with col_r2:
            if st.button("🔥 Xóa Vĩnh Viễn Đã Chọn Khỏi Danh Sách Xóa", use_container_width=True):
                if selected_to_restore:
                    master_rules[:] = [item for item in master_rules if item["Hạng Mục Công Việc"] not in selected_to_restore]
                    save_data()
                    st.success("Đã xóa vĩnh viễn các mục đã chọn khỏi bộ nhớ tạm!")
                    st.rerun()
                else:
                    st.warning("Vui lòng chọn mục cần xóa vĩnh viễn!")

    st.markdown("---")
    with st.form("rules_form"):
        edited_rules = st.data_editor(
            st.session_state.rules_df, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="rules_editor",
            hide_index=True
        )
        save_rules_btn = st.form_submit_button("💾 Lưu Thay Đổi Định Mức", use_container_width=True)
        if save_rules_btn:
            edited_rules["STT"] = range(1, len(edited_rules) + 1)
            st.session_state.rules_df = edited_rules
            save_data()
            st.success("Đã lưu danh mục tham chiếu công việc thành công!")
            st.rerun()

# ==================== THÙNG RÁC SẢN LƯỢNG ====================
elif feature == "trash":
    if st.session_state.role != "admin":
        st.error("⚠️ Bạn không có quyền truy cập vào Thùng Rác Sản Lượng!")
    else:
        st.header(menu)
        st.markdown("Các bản ghi sản lượng đã xóa sẽ được lưu ở đây kèm theo ảnh đính kèm. Bạn có thể khôi phục lại (giữ nguyên ảnh) hoặc xóa vĩnh viễn.")
        
        if not st.session_state.deleted_input_df.empty:
            st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
            
            with st.form("trash_form"):
                for idx, row in st.session_state.deleted_input_df.iterrows():
                    row_c1, row_c2 = st.columns([4, 1])
                    with row_c1:
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem; line-height: 1.3;">
                            <b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} &nbsp;|&nbsp; 👤 <b>{row['Nhân Sự']}</b><br>
                            📌 {row['Hạng Mục Công Việc']} &nbsp;|&nbsp; 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                            💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        is_selected = st.checkbox(f"Chọn bản ghi STT {row['STT']}", key=f"trash_chk_{row['STT']}")
                        st.session_state.deleted_input_df.loc[idx, "Chọn_Xóa"] = is_selected
                        
                    with row_c2:
                        img_url_val = row.get("Hình Ảnh", "")
                        if img_url_val and isinstance(img_url_val, str):
                            try:
                                st.image(img_url_val, width=50)
                                with st.popover("🔍 Phóng to"):
                                    st.image(img_url_val, use_container_width=True)
                            except Exception:
                                st.text("Lỗi hiển thị ảnh")
                    st.markdown("---")
                
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    restore_btn = st.form_submit_button("📥 Khôi Phục Dòng Đã Chọn", use_container_width=True)
                with t_col2:
                    delete_perm_btn = st.form_submit_button("🔥 Xóa Vĩnh Viễn Dòng Đã Chọn", use_container_width=True)
                    
                if restore_btn:
                    selected_rows = st.session_state.deleted_input_df[st.session_state.deleted_input_df["Chọn_Xóa"] == True]
                    if not selected_rows.empty:
                        stt_to_remove = selected_rows["STT"].tolist()
                        
                        st.session_state.deleted_input_df = st.session_state.deleted_input_df[~st.session_state.deleted_input_df["STT"].isin(stt_to_remove)].reset_index(drop=True)
                        if not st.session_state.deleted_input_df.empty:
                            st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
                        
                        for idx, row in selected_rows.iterrows():
                            new_row = row.drop(labels=["Chọn_Xóa"], errors="ignore").copy()
                            new_row["STT"] = len(st.session_state.input_df) + 1
                            st.session_state.input_df = pd.concat([st.session_state.input_df, pd.DataFrame([new_row])], ignore_index=True)
                        
                        st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                        save_data()
                        st.success("Đã khôi phục các dòng đã chọn thành công!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn ít nhất một dòng!")

                if delete_perm_btn:
                    selected_rows = st.session_state.deleted_input_df[st.session_state.deleted_input_df["Chọn_Xóa"] == True]
                    if not selected_rows.empty:
                        stt_to_remove = selected_rows["STT"].tolist()
                        
                        st.session_state.deleted_input_df = st.session_state.deleted_input_df[~st.session_state.deleted_input_df["STT"].isin(stt_to_remove)].reset_index(drop=True)
                        if not st.session_state.deleted_input_df.empty:
                            st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
                        
                        save_data()
                        st.success("Đã xóa vĩnh viễn các dòng đã chọn!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn ít nhất một dòng!")

            st.markdown("---")
            if st.button("🔥 Làm Sạch Hoàn Toàn Thùng Rác", use_container_width=True):
                st.session_state.deleted_input_df = pd.DataFrame(columns=default_input_columns)
                save_data()
                st.success("Đã làm sạch hoàn toàn thùng rác!")
                st.rerun()
        else:
            st.info("Thùng rác hiện tại đang trống.")

# ==================== QUẢN LÝ THƯ MỤC & MENU ====================
elif feature == "manage_folders":
    st.header("📁 Quản Lý Thư Mục & Mục Menu Tùy Chỉnh")
    st.markdown("Cấu hình tên hiển thị của các thư mục và sắp xếp các mục menu trong hệ thống.")

    with st.form("folder_manager_form"):
        updated_folders = []
        for f_idx, folder in enumerate(st.session_state.folders):
            st.markdown(f"### Thư mục #{f_idx + 1}")
            new_f_name = st.text_input(f"Tên thư mục {f_idx + 1}", value=folder["folder_name"], key=f"f_name_{f_idx}")
            
            st.markdown("##### Các mục trong thư mục này:")
            updated_items = []
            for i_idx, item in enumerate(folder["items"]):
                new_item_name = st.text_input(f"Tên mục {i_idx + 1}", value=item["name"], key=f"item_name_{f_idx}_{i_idx}")
                updated_items.append({"id": item["id"], "name": new_item_name})
            
            add_new_item = st.text_input(f"Thêm tên mục mới vào thư mục này (để trống nếu không thêm)", key=f"add_new_{f_idx}")
            if add_new_item.strip():
                new_id = f"custom_menu_{f_idx}_{len(updated_items) + 1}"
                updated_items.append({"id": new_id, "name": add_new_item.strip()})

            updated_folders.append({
                "folder_name": new_f_name,
                "items": updated_items
            })
            st.markdown("---")

        save_folders_btn = st.form_submit_button("💾 Lưu Cấu Hình Thư Mục & Menu", use_container_width=True)
        if save_folders_btn:
            st.session_state.folders = updated_folders
            save_data()
            st.success("Đã cập nhật tên thư mục và menu thành công!")
            st.rerun()

# ==================== CÀI ĐẶT GIAO DIỆN ====================
elif feature == "settings_ui":
    st.header("Cài Đặt Giao Diện Riêng Cho Bạn")
    
    if st.session_state.role == "admin":
        st.subheader("⚡ Tự Động Đồng Bộ Dữ Liệu Ngầm (Dành cho Admin)")
        st.markdown("Tùy chỉnh thời gian tự động làm mới trang để cập nhật dữ liệu chung từ các tài khoản con (từ 1 đến 60 phút).")
        
        current_refresh_min = int(st.session_state.get("auto_refresh_minutes", 5))
        new_refresh_min = st.slider("Thời gian tự động đồng bộ (Phút):", min_value=1, max_value=60, value=current_refresh_min, step=1)
        
        if st.button("💾 Lưu Thời Gian Đồng Bộ", use_container_width=True):
            st.session_state.auto_refresh_minutes = new_refresh_min
            save_data()
            st.success(f"Đã cập nhật thời gian tự động đồng bộ là {new_refresh_min} phút!")
            st.rerun()
        st.markdown("---")

    st.subheader("Màu Sắc Giao Diện Cá Nhân")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        new_primary = st.color_picker("Màu chủ đạo", st.session_state.primary_color, key="picker_primary")
        new_bg = st.color_picker("Màu nền trang", st.session_state.bg_color, key="picker_bg")
    with col_c2:
        new_sidebar_bg = st.color_picker("Màu nền thanh bên", st.session_state.sidebar_bg, key="picker_sidebar")
        new_text_color = st.color_picker("Màu chữ", st.session_state.text_color, key="picker_text")
        
    new_opacity = st.slider("Độ trong suốt thanh Sidebar", min_value=0.0, max_value=1.0, value=float(st.session_state.sidebar_opacity), step=0.05, key="slider_opacity")

    if st.button("💾 Lưu Thay Đổi Màu Sắc Riêng", use_container_width=True):
        st.session_state.primary_color = new_primary
        st.session_state.bg_color = new_bg
        st.session_state.sidebar_bg = new_sidebar_bg
        st.session_state.text_color = new_text_color
        st.session_state.sidebar_opacity = new_opacity
        save_data()
        st.success("Đã lưu và cập nhật màu sắc giao diện cá nhân thành công!")
        st.rerun()

    st.markdown("---")
    st.subheader("🖼️ Quản Lý Hình Nền Cá Nhân (Tải lên / Xóa / Tắt nền)")

    if st.session_state.bg_image_url:
        if st.button("👁️ Tắt / Ẩn Hình Nền Riêng (Dùng màu đơn)", use_container_width=True):
            st.session_state.bg_image_url = None
            save_data()
            st.success("Đã ẩn hình nền cá nhân!")
            st.rerun()

    bg_file = st.file_uploader("Tải ảnh hình nền mới (PNG, JPG)", type=["png", "jpg", "jpeg"], key="bg_uploader_standalone")
    if bg_file is not None:
        with st.spinner("Đang tải ảnh nền lên Supabase..."):
            bg_public_url = upload_image_to_supabase(bg_file, folder_prefix="backgrounds")
        if bg_public_url:
            st.session_state.bg_image_url = bg_public_url
            save_data()
            st.success("Đã cập nhật hình nền cá nhân thành công!")
            st.rerun()

    if st.session_state.bg_image_url:
        st.markdown("---")
        st.markdown("#### 📂 Hình Nền Đang Sử Dụng")
        try:
            st.image(st.session_state.bg_image_url, width=150, caption="Ảnh nền hiện tại")
            if st.button("🗑️ Xóa Vĩnh Viễn Hình Nền", use_container_width=True):
                st.session_state.bg_image_url = None
                save_data()
                st.success("Đã xóa hình nền!")
                st.rerun()
        except Exception:
            pass
    else:
        st.text("Chưa có hình nền cá nhân nào.")

# ==================== LÀM SẠCH DỮ LIỆU ====================
elif feature == "clean_data":
    if st.session_state.role != "admin":
        st.error("⚠️ Bạn không có quyền truy cập vào mục Làm Sạch Dữ Liệu!")
    else:
        st.header("Làm Sạch & Tối Ưu Dữ Liệu")
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("📦 Tổng bản ghi sản lượng", len(st.session_state.input_df))
        with m_col2:
            st.metric("🗑️ Bản ghi trong thùng rác", len(st.session_state.deleted_input_df))

        st.markdown("---")
        
        with st.form("clean_by_date_form"):
            clean_date = st.date_input("Xóa tất cả dữ liệu sản lượng trước ngày:")
            confirm_text = st.text_input("Nhập chữ 'XAC NHAN':", "")
            
            clean_btn = st.form_submit_button("🧹 Xóa Dữ Liệu Cũ Theo Ngày", use_container_width=True)
            if clean_btn:
                if confirm_text == "XAC NHAN":
                    if not st.session_state.input_df.empty:
                        st.session_state.input_df["_dt"] = pd.to_datetime(st.session_state.input_df["Ngày"], errors="coerce")
                        target_dt = pd.to_datetime(clean_date)
                        
                        keep_df = st.session_state.input_df[st.session_state.input_df["_dt"] >= target_dt].drop(columns=["_dt"])
                        removed_count = len(st.session_state.input_df) - len(keep_df)
                        
                        st.session_state.input_df = keep_df
                        if not st.session_state.input_df.empty:
                            st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                            
                        save_data()
                        st.success(f"Đã xóa {removed_count} bản ghi cũ trước ngày {clean_date}.")
                        st.rerun()
                    else:
                        st.info("Danh sách sản lượng hiện đang trống.")
                else:
                    st.warning("⚠️ Vui lòng nhập đúng chữ 'XAC NHAN'.")

        st.markdown("---")
        if st.button("🔥 Làm Sạch Hoàn Toàn Thùng Rác", use_container_width=True):
            st.session_state.deleted_input_df = pd.DataFrame(columns=default_input_columns)
            save_data()
            st.success("Đã làm sạch hoàn toàn thùng rác!")
            st.rerun()
