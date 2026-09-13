import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io
import base64
import json
import os
from PIL import Image

# Thử import supabase, nếu có lỗi cài đặt thư viện thì vẫn chạy ổn định với file cục bộ
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False

st.set_page_config(page_title="Phần Mềm Chấm Điểm Sản Lượng", page_icon="📊", layout="wide")

# ==================== KẾT NỐI SUPABASE & CƠ CHẾ AN TOÀN ====================
SUPABASE_URL = "https://xbozutjkiwnaoiluahq.supabase.co"
SUPABASE_KEY = "sb_publishable_UKjUhq93nc51-dvjE6Xong_DhlJB7FP"

supabase = None
if HAS_SUPABASE_LIB and SUPABASE_KEY and SUPABASE_KEY != "YOUR_SUPABASE_ANON_KEY":
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

DATA_FILE = "app_storage.json"

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

default_staff_list = ["Nguyễn Hữu Khang Tôn Đức", "Nguyễn Đức Anh Tiến", "Trần Gia Bảo"]
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

def compress_image_to_base64(uploaded_file, max_size=(800, 800), quality=70):
    try:
        if uploaded_file is None:
            return None
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(max_size)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=quality)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception:
        return None

def load_data():
    # 1. Thử lấy từ Supabase trực tiếp không qua cache gây lỗi treo
    if supabase is not None:
        try:
            response = supabase.table("app_storage_table").select("data").eq("id", "main_config").execute()
            if response.data and len(response.data) > 0:
                raw_data = response.data[0]["data"]
                if isinstance(raw_data, str):
                    return json.loads(raw_data)
                elif isinstance(raw_data, dict):
                    return raw_data
        except Exception:
            pass
    
    # 2. Nếu Supabase lỗi hoặc chưa có, đọc từ file cục bộ
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    return {}

def save_data():
    data = {
        "rules_df": st.session_state.rules_df.to_dict(orient="records") if "rules_df" in st.session_state else master_rules,
        "input_df": st.session_state.input_df.to_dict(orient="records") if "input_df" in st.session_state else [],
        "attendance_df": st.session_state.attendance_df.to_dict(orient="records") if "attendance_df" in st.session_state else [],
        "deleted_input_df": st.session_state.deleted_input_df.to_dict(orient="records") if "deleted_input_df" in st.session_state else [],
        "staff_list": st.session_state.staff_list if "staff_list" in st.session_state else default_staff_list,
        "chart_colors": st.session_state.chart_colors if "chart_colors" in st.session_state else default_chart_colors,
        "folders": st.session_state.folders if "folders" in st.session_state else default_folders,
        "primary_color": st.session_state.primary_color if "primary_color" in st.session_state else "#ff4b4b",
        "bg_color": st.session_state.bg_color if "bg_color" in st.session_state else "#ffffff",
        "sidebar_bg": st.session_state.sidebar_bg if "sidebar_bg" in st.session_state else "#f0f2f6",
        "sidebar_opacity": st.session_state.sidebar_opacity if "sidebar_opacity" in st.session_state else 0.9,
        "text_color": st.session_state.text_color if "text_color" in st.session_state else "#31333F",
        "require_image": st.session_state.get("require_image", True),
        "require_quantity": st.session_state.get("require_quantity", True),
        "bg_image_base64": st.session_state.get("bg_image_base64", None),
        "avatar_base64": st.session_state.get("avatar_base64", None),
        "current_menu": st.session_state.get("current_menu", "1. Nhập Sản Lượng")
    }
    
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str, indent=4)
    except Exception:
        pass

    if supabase is not None:
        try:
            json_str = json.dumps(data, ensure_ascii=False, default=str)
            payload = {"id": "main_config", "data": json_str}
            supabase.table("app_storage_table").upsert(payload).execute()
        except Exception:
            pass

saved_data = load_data()

st.session_state.rules_df = pd.DataFrame(saved_data["rules_df"]) if "rules_df" in saved_data and saved_data["rules_df"] else pd.DataFrame(master_rules)

default_input_columns = ["STT", "Ngày", "Thời Gian", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"]
if "input_df" in saved_data and saved_data["input_df"]:
    st.session_state.input_df = pd.DataFrame(saved_data["input_df"])
else:
    st.session_state.input_df = pd.DataFrame(columns=default_input_columns)

for col in default_input_columns:
    if col not in st.session_state.input_df.columns:
        st.session_state.input_df[col] = ""

st.session_state.attendance_df = pd.DataFrame(saved_data["attendance_df"]) if "attendance_df" in saved_data else pd.DataFrame(columns=["STT", "Ngày", "Nhân Sự", "Giờ Vào Ca", "Giờ Ra Ca", "Số Phút Làm Việc", "Ghi Chú"])

if "deleted_input_df" in saved_data and saved_data["deleted_input_df"]:
    st.session_state.deleted_input_df = pd.DataFrame(saved_data["deleted_input_df"])
else:
    st.session_state.deleted_input_df = pd.DataFrame(columns=default_input_columns)

for col in default_input_columns:
    if col not in st.session_state.deleted_input_df.columns:
        st.session_state.deleted_input_df[col] = ""

st.session_state.staff_list = saved_data.get("staff_list", default_staff_list)
st.session_state.chart_colors = saved_data.get("chart_colors", default_chart_colors)
st.session_state.folders = saved_data.get("folders", default_folders)
st.session_state.primary_color = saved_data.get("primary_color", "#ff4b4b")
st.session_state.bg_color = saved_data.get("bg_color", "#ffffff")
st.session_state.sidebar_bg = saved_data.get("sidebar_bg", "#f0f2f6")
st.session_state.sidebar_opacity = saved_data.get("sidebar_opacity", 0.9)
st.session_state.text_color = saved_data.get("text_color", "#31333F")
st.session_state.require_image = saved_data.get("require_image", True)
st.session_state.require_quantity = saved_data.get("require_quantity", True)
st.session_state.bg_image_base64 = saved_data.get("bg_image_base64", None)
st.session_state.avatar_base64 = saved_data.get("avatar_base64", None)

first_item_name = "1. Nhập Sản Lượng"
if st.session_state.folders and st.session_state.folders[0]["items"]:
    first_item_name = st.session_state.folders[0]["items"][0]["name"]
st.session_state.current_menu = saved_data.get("current_menu", first_item_name)

if not st.session_state.input_df.empty:
    st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
if not st.session_state.attendance_df.empty:
    if "Ghi Chú" not in st.session_state.attendance_df.columns:
        st.session_state.attendance_df["Ghi Chú"] = ""
    st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)
