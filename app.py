import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io
import base64
import json
import os
from PIL import Image

st.set_page_config(page_title="Phần Mềm Chấm Điểm Sản Lượng", page_icon="📊", layout="wide")

STORAGE_FILE = "app_storage.json"

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
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
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
        "bg_image_base64": st.session_state.get("bg_image_base64", None),
        "avatar_base64": st.session_state.get("avatar_base64", None),
        "current_menu": st.session_state.get("current_menu", "1. Nhập Sản Lượng")
    }
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception:
        pass

saved_data = load_data()

st.session_state.rules_df = pd.DataFrame(saved_data["rules_df"]) if "rules_df" in saved_data and saved_data["rules_df"] else pd.DataFrame(master_rules)

default_input_columns = ["STT", "Ngày", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"]
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

bg_style = f"background-color: {st.session_state.bg_color};"
if st.session_state.bg_image_base64:
    bg_style = f"background-image: url(data:image/jpeg;base64,{st.session_state.bg_image_base64}); background-size: cover; background-repeat: no-repeat; background-position: center; background-attachment: fixed;"

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

with st.sidebar:
    st.markdown('<div class="fixed-avatar-container">', unsafe_allow_html=True)
    
    has_custom_avatar = False
    avatar_bytes_obj = None
    if st.session_state.avatar_base64:
        try:
            pure_b64 = st.session_state.avatar_base64.split(",")[1] if "," in st.session_state.avatar_base64 else st.session_state.avatar_base64
            pure_b64 += "=" * (-len(pure_b64) % 4)
            avatar_bytes_obj = base64.b64decode(pure_b64)
            has_custom_avatar = True
        except Exception:
            pass

    st.markdown('<div class="avatar-wrapper">', unsafe_allow_html=True)
    
    if has_custom_avatar:
        with st.popover(" ", use_container_width=False):
            st.markdown("##### 🔍 Xem Ảnh Đại Diện")
            st.image(avatar_bytes_obj, use_container_width=True)
            
        encoded_img = base64.b64encode(avatar_bytes_obj).decode("utf-8")
        st.markdown(f"""
        <div style="cursor: pointer; text-align: center;">
            <img src="data:image/jpeg;base64,{encoded_img}" style="width:140px; height:140px; border-radius:50%; object-fit:cover; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3);">
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
        st.markdown("##### ⚙️ Cài Đặt Ảnh Đại Diện")
        avatar_file = st.file_uploader("Tải ảnh", type=["png", "jpg", "jpeg"], key="avatar_uploader_popover", label_visibility="collapsed")
        if avatar_file is not None:
            compressed_avatar = compress_image_to_base64(avatar_file, max_size=(300, 300), quality=60)
            if compressed_avatar:
                st.session_state.avatar_base64 = compressed_avatar
                save_data()
                st.success("Đã cập nhật ảnh đại diện!")
                st.rerun()
            
        if st.session_state.avatar_base64:
            st.markdown("---")
            if st.button("🗑️ Xóa Ảnh Đại Diện", use_container_width=True):
                st.session_state.avatar_base64 = None
                save_data()
                st.success("Đã xóa ảnh đại diện!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-scrollable-content">', unsafe_allow_html=True)

    if st.button("🔄 Cập Nhật", use_container_width=True, help="Bấm để đồng bộ dữ liệu mới nhất"):
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
                if st.button(item["name"], use_container_width=True, key=f"btn_{item['id']}"):
                    st.session_state.current_menu = item["name"]
                    save_data()
                    st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Cấu Hình Hệ Thống")
    if st.button("📁 Quản Lý Thư Mục & Menu", use_container_width=True):
        st.session_state.current_menu = "📁 Quản Lý Thư Mục & Menu"
        save_data()
        st.rerun()
    if st.button("🎨 Cài Đặt Giao Diện", use_container_width=True):
        st.session_state.current_menu = "🎨 Cài Đặt Giao Diện"
        save_data()
        st.rerun()
    if st.button("🧹 Làm Sạch & Tối Ưu Dữ Liệu", use_container_width=True):
        st.session_state.current_menu = "🧹 Làm Sạch Dữ Liệu"
        save_data()
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

menu = st.session_state.current_menu

def get_feature_type(menu_name):
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

# ==================== 1. NHẬP SẢN LƯỢNG ====================
if feature == "input_production":
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

    if not active_staff:
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
                    row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
                    he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
                    don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
                    tong_diem = so_luong * he_so
                    
                    img_base64 = compress_image_to_base64(record_image, max_size=(800, 800), quality=65) if record_image is not None else ""
                    
                    new_stt = len(st.session_state.input_df) + 1
                    new_row = {
                        "STT": new_stt,
                        "Ngày": today_str,
                        "Nhân Sự": nhan_su,
                        "Hạng Mục Công Việc": hang_muc,
                        "Hình Ảnh": img_base64,
                        "Đơn Vị": don_vi,
                        "Số Lượng": so_luong,
                        "Hệ Số Điểm": he_so,
                        "Tổng Điểm": round(tong_diem, 2),
                        "Ghi Chú": ghi_chu
                    }
                    st.session_state.input_df = pd.concat([st.session_state.input_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                    save_data()
                    st.success(f"Đã báo cáo sản lượng thành công cho **{nhan_su}**! Tổng điểm: **{tong_diem} điểm**")
                    st.rerun()

    st.markdown("---")
    st.subheader("Danh Sách Sản Lượng & Hình Ảnh")
    
    if not st.session_state.input_df.empty:
        st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
        
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            all_dates = ["Tất cả"] + sorted(st.session_state.input_df["Ngày"].unique().tolist())
            filter_date = st.selectbox("Lọc theo Ngày", all_dates)
        with s_col2:
            all_staff = ["Tất cả"] + sorted(st.session_state.input_df["Nhân Sự"].unique().tolist())
            filter_staff = st.selectbox("Lọc theo Nhân Sự", all_staff)
        with s_col3:
            zoom_level = st.slider("🔍 Kích thước ảnh:", min_value=50, max_value=200, value=80, step=10)
        
        filtered_df = st.session_state.input_df.copy()
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
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem; line-height: 1.3;">
                            <b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} &nbsp;|&nbsp; 👤 <b>{row['Nhân Sự']}</b><br>
                            📌 {row['Hạng Mục Công Việc']} &nbsp;|&nbsp; 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                            💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        is_selected = st.checkbox(f"Xóa bản ghi STT {row['STT']}", key=f"chk_{row['STT']}")
                        filtered_df.loc[idx, "Chọn_Xóa"] = is_selected
                        
                    with row_c2:
                        img_b64_val = row.get("Hình Ảnh", "")
                        if img_b64_val and isinstance(img_b64_val, str) and len(img_b64_val) > 10:
                            try:
                                pure_b64 = img_b64_val.split(",")[1] if "," in img_b64_val else img_b64_val
                                pure_b64 += "=" * (-len(pure_b64) % 4)
                                img_bytes = base64.b64decode(pure_b64)
                                
                                st.image(img_bytes, width=zoom_level)
                                with st.popover("🔍 Phóng to"):
                                    st.image(img_bytes, use_container_width=True)
                            except Exception:
                                st.text("Lỗi hiển thị ảnh")
                    st.markdown("---")
                    
                delete_submitted = st.form_submit_button("🗑️ Xóa Các Dòng Đã Tích Chọn", use_container_width=True)
                if delete_submitted:
                    selected_rows = filtered_df[filtered_df["Chọn_Xóa"] == True]
                    if not selected_rows.empty:
                        stt_to_remove = selected_rows["STT"].tolist()
                        rows_to_delete = st.session_state.input_df[st.session_state.input_df["STT"].isin(stt_to_remove)]
                        st.session_state.deleted_input_df = pd.concat([st.session_state.deleted_input_df, rows_to_delete], ignore_index=True)
                        
                        st.session_state.input_df = st.session_state.input_df[~st.session_state.input_df["STT"].isin(stt_to_remove)].reset_index(drop=True)
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
        {staff_status_lines}
    </div>
    """, unsafe_allow_html=True)

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
                new_att_stt = len(st.session_state.attendance_df) + 1
                new_att_row = {
                    "STT": new_att_stt,
                    "Ngày": str(att_date),
                    "Nhân Sự": att_staff,
                    "Giờ Vào Ca": current_time_str,
                    "Giờ Ra Ca": "Chưa kết thúc",
                    "Số Phút Làm Việc": 0,
                    "Ghi Chú": att_note
                }
                st.session_state.attendance_df = pd.concat([st.session_state.attendance_df, pd.DataFrame([new_att_row])], ignore_index=True)
                st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)
                save_data()
                st.success(f"Đã ghi nhận **Vào ca** cho **{att_staff}** lúc {current_time_str}!")
                st.rerun()
            
        if check_out_clicked:
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
    
    all_staff_current = st.session_state.staff_list
    
    if not st.session_state.input_df.empty:
        df_in = st.session_state.input_df
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
    
    if not st.session_state.attendance_df.empty:
        att_summary = st.session_state.attendance_df.groupby("Nhân Sự")["Số Phút Làm Việc"].sum().reset_index()
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
    st.subheader("Biểu Đồ & Chi Tiết Tỷ Lệ Đóng Góp")
    
    with st.expander("🎨 Tùy Chỉnh Màu Sắc Biểu Đồ", expanded=False):
        while len(st.session_state.chart_colors) < len(all_staff_current):
            st.session_state.chart_colors.append("#3b82f6")
        
        color_cols = st.columns(min(len(all_staff_current), 4))
        for i, staff_name in enumerate(all_staff_current):
            col_idx = i % len(color_cols)
            with color_cols[col_idx]:
                st.session_state.chart_colors[i] = st.color_picker(f"Màu: {staff_name}", st.session_state.chart_colors[i], key=f"color_pick_{i}")
        if st.button("Lưu Màu Biểu Đồ", use_container_width=True):
            save_data()
            st.success("Đã cập nhật màu sắc biểu đồ!")
            st.rerun()

    chart_size = 3.0
    col_pie, col_details = st.columns([1, 1])
    
    with col_pie:
        fig, ax = plt.subplots(figsize=(chart_size, chart_size), dpi=300)
        current_colors = st.session_state.chart_colors[:len(summary)]
        
        max_pts = summary["Tổng_Điểm"].max()
        explode_values = [0.02 + 0.05 * (pts / max_pts) if max_pts > 0 else 0.0 for pts in summary["Tổng_Điểm"]]

        wedges, texts = ax.pie(
            summary["Tổng_Điểm"], 
            labels=None, 
            autopct=None, 
            startangle=90, 
            colors=current_colors,
            explode=explode_values,
            shadow=False
        )
        
        ax.axis('equal')
        st.pyplot(fig)
        
    with col_details:
        st.markdown("#### 📌 Chi Tiết Điểm Số & Tỷ Lệ")
        current_colors = st.session_state.chart_colors[:len(summary)]
        for i, row in summary.iterrows():
            color_box = current_colors[i] if i < len(current_colors) else "#3b82f6"
            staff_name = row["Nhân Sự"]
            staff_pts = row["Tổng_Điểm"]
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
    st.markdown("Chỉnh sửa trực tiếp tên công việc, đơn vị hoặc hệ số điểm ngay trên bảng dưới đây.")
    
    if not st.session_state.rules_df.empty:
        st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
        
    current_items = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else []
    deleted_items_list = [r for r in master_rules if r["Hạng Mục Công Việc"] not in current_items]
    
    if deleted_items_list:
        deleted_names = [item["Hạng Mục Công Việc"] for item in deleted_items_list]
        selected_to_restore = st.multiselect("Khôi phục hạng mục đã xóa:", deleted_names)
        if st.button("📥 Khôi Phục Đã Chọn", use_container_width=True):
            if selected_to_restore:
                items_to_add = [item for item in deleted_items_list if item["Hạng Mục Công Việc"] in selected_to_restore]
                restored_df = pd.DataFrame(items_to_add)
                st.session_state.rules_df = pd.concat([st.session_state.rules_df, restored_df], ignore_index=True)
                st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
                save_data()
                st.success("Đã khôi phục thành công!")
                st.rerun()

    if st.button("🔄 Khôi Phục Toàn Bộ Mặc Định", use_container_width=True):
        st.session_state.rules_df = pd.DataFrame(master_rules)
        st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
        save_data()
        st.success("Đã khôi phục danh mục mặc định thành công!")
        st.rerun()

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
    st.header(menu)
    st.markdown("Các bản ghi sản lượng đã xóa sẽ được lưu ở đây kèm theo ảnh đính kèm. Bạn có thể khôi phục lại (giữ nguyên ảnh) hoặc xóa vĩnh viễn.")
    
    if not st.session_state.deleted_input_df.empty:
        st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
        
        trash_zoom = st.slider("🔍 Kích thước ảnh trong thùng rác:", min_value=50, max_value=200, value=80, step=10, key="trash_zoom")
        
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
                    img_b64_val = row.get("Hình Ảnh", "")
                    if img_b64_val and isinstance(img_b64_val, str) and len(img_b64_val) > 10:
                        try:
                            pure_b64 = img_b64_val.split(",")[1] if "," in img_b64_val else img_b64_val
                            pure_b64 += "=" * (-len(pure_b64) % 4)
                            img_bytes = base64.b64decode(pure_b64)
                            
                            st.image(img_bytes, width=trash_zoom)
                            with st.popover("🔍 Phóng to"):
                                st.image(img_bytes, use_container_width=True)
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
                    st.success("Đã khôi phục các dòng đã chọn (kèm theo hình ảnh) thành công!")
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
            st.success("Đã làm sạch hoàn toàn thùng rác và xóa bỏ toàn bộ hình ảnh lưu trữ!")
            st.rerun()
    else:
        st.info("Thùng rác hiện tại đang trống.")

# ==================== QUẢN LÝ THƯ MỤC & MENU ====================
elif feature == "manage_folders":
    st.header("📁 Quản Lý Thư Mục & Mục Menu Tùy Chỉnh")
    st.markdown("Bạn có thể chỉnh sửa, thay đổi tên thư mục hoặc tên các mục bên trong trực tiếp tại đây.")

    with st.form("manage_folders_form"):
        updated_folders = []
        for f_idx, folder in enumerate(st.session_state.folders):
            st.markdown(f"### Thư mục #{f_idx + 1}")
            f_name = st.text_input(f"Tên Thư Mục #{f_idx + 1}", value=folder["folder_name"], key=f"fname_{f_idx}")
            
            updated_items = []
            st.markdown("Các mục con trong thư mục này:")
            for i_idx, item in enumerate(folder["items"]):
                i_name = st.text_input(f"Tên mục #{i_idx + 1}", value=item["name"], key=f"item_name_{f_idx}_{i_idx}")
                if i_name.strip():
                    updated_items.append({"id": item["id"], "name": i_name.strip()})

            if f_name.strip():
                updated_folders.append({
                    "folder_name": f_name.strip(),
                    "items": updated_items
                })
            st.markdown("---")

        save_folders_btn = st.form_submit_button("💾 Xác Nhận Lưu Thay Đổi", use_container_width=True)
        if save_folders_btn:
            if not updated_folders:
                st.error("Cần phải giữ lại ít nhất một thư mục và một mục!")
            else:
                st.session_state.folders = updated_folders
                save_data()
                st.success("Đã cập nhật cấu trúc thư mục thành công!")
                st.rerun()

# ==================== CÀI ĐẶT GIAO DIỆN ====================
elif feature == "settings_ui":
    st.header("Cài Đặt Giao Diện & Nhân Sự")
    
    st.subheader("Quản Lý Nhân Sự")
    with st.form("staff_form"):
        staff_df = pd.DataFrame({"Nhân Sự": st.session_state.staff_list})
        edited_staff_df = st.data_editor(
            staff_df,
            num_rows="dynamic",
            use_container_width=True,
            key="staff_editor",
            hide_index=True
        )
        save_staff_btn = st.form_submit_button("💾 Lưu Danh Sách Nhân Sự", use_container_width=True)
        if save_staff_btn:
            new_staff_list = [str(x).strip() for x in edited_staff_df["Nhân Sự"].tolist() if str(x).strip() != ""]
            if new_staff_list:
                st.session_state.staff_list = new_staff_list
                save_data()
                st.success("Đã cập nhật danh sách nhân sự!")
                st.rerun()
            else:
                st.warning("Danh sách nhân sự không được để trống.")

    st.markdown("---")
    
    st.subheader("Màu Sắc Giao Diện")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        new_primary = st.color_picker("Màu chủ đạo", st.session_state.primary_color, key="picker_primary")
        new_bg = st.color_picker("Màu nền trang", st.session_state.bg_color, key="picker_bg")
    with col_c2:
        new_sidebar_bg = st.color_picker("Màu nền thanh bên", st.session_state.sidebar_bg, key="picker_sidebar")
        new_text_color = st.color_picker("Màu chữ", st.session_state.text_color, key="picker_text")
        
    new_opacity = st.slider("Độ trong suốt thanh Sidebar", min_value=0.0, max_value=1.0, value=float(st.session_state.sidebar_opacity), step=0.05, key="slider_opacity")

    if st.button("💾 Lưu Thay Đổi Màu Sắc", use_container_width=True):
        st.session_state.primary_color = new_primary
        st.session_state.bg_color = new_bg
        st.session_state.sidebar_bg = new_sidebar_bg
        st.session_state.text_color = new_text_color
        st.session_state.sidebar_opacity = new_opacity
        save_data()
        st.success("Đã lưu và cập nhật màu sắc giao diện thành công!")
        st.rerun()

    st.markdown("---")
    st.subheader("🖼️ Quản Lý Hình Nền (Tải lên / Xóa / Tắt nền)")

    if st.session_state.bg_image_base64:
        if st.button("👁️ Tắt / Ẩn Hình Nền (Dùng màu đơn)", use_container_width=True):
            st.session_state.bg_image_base64 = None
            save_data()
            st.success("Đã ẩn hình nền, chuyển về màu nền trang đơn sắc!")
            st.rerun()

    bg_file = st.file_uploader("Tải ảnh hình nền mới (PNG, JPG)", type=["png", "jpg", "jpeg"], key="bg_uploader_standalone")
    if bg_file is not None:
        compressed_bg = compress_image_to_base64(bg_file, max_size=(1024, 1024), quality=70)
        if compressed_bg:
            st.session_state.bg_image_base64 = compressed_bg
            save_data()
            st.success("Đã cập nhật hình nền chính thành công!")
            st.rerun()

    if st.session_state.bg_image_base64:
        st.markdown("---")
        st.markdown("#### 📂 Hình Nền Đang Sử Dụng")
        try:
            pure_b64 = st.session_state.bg_image_base64.split(",")[1] if "," in st.session_state.bg_image_base64 else st.session_state.bg_image_base64
            img_bytes = base64.b64decode(pure_b64)
            st.image(img_bytes, width=150, caption="Ảnh nền hiện tại")
            if st.button("🗑️ Xóa Vĩnh Viễn Hình Nền", use_container_width=True):
                st.session_state.bg_image_base64 = None
                save_data()
                st.success("Đã xóa hình nền!")
                st.rerun()
        except Exception:
            pass
    else:
        st.text("Chưa có hình nền nào được chọn.")

# ==================== LÀM SẠCH DỮ LIỆU ====================
elif feature == "clean_data":
    st.header("Làm Sạch & Tối Ưu Dữ Liệu")
    
    file_size_kb = 0
    if os.path.exists(STORAGE_FILE):
        file_size_kb = os.path.getsize(STORAGE_FILE) / 1024

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("📦 Tổng bản ghi sản lượng", len(st.session_state.input_df))
    with m_col2:
        st.metric("🗑️ Bản ghi trong thùng rác", len(st.session_state.deleted_input_df))
    with m_col3:
        st.metric("💾 Dung lượng tệp lưu trữ", f"{file_size_kb:.2f} KB")

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
