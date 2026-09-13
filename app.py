import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io
import base64
import os
from PIL import Image

# Thử import supabase
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False

st.set_page_config(page_title="POSS", page_icon="📊", layout="wide")

# ==================== KẾT NỐI SUPABASE ====================
SUPABASE_URL = "https://xbozutjkiywnaoiluahq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhib3p1dGpraXl3bmFvaWx1YWhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwMjUwODIsImV4cCI6MjEwNDYwMTA4Mn0.ByzJ_xC9Cl3uUACmiIYD1xrHtDEs-fQBKZ4wSX-nlWc"

supabase = None
if HAS_SUPABASE_LIB and SUPABASE_KEY != "YOUR_SUPABASE_ANON_KEY":
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

class VietnamTz(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=7)
    def tzname(self, dt):
        return "ICT"
    def dst(self, dt):
        return datetime.timedelta(0)

VN_TIMEZONE = VietnamTz()

master_rules = [
    {"stt": 1, "hang_muc": "Lấy hộp có sẵn", "don_vi": "Cái", "he_so_diem": 0.5, "ghi_chu": "Kho / Vận hành"},
    {"stt": 3, "hang_muc": "Lấy đế có sẵn", "don_vi": "Cái", "he_so_diem": 0.5, "ghi_chu": "Kho / Vận hành"},
    {"stt": 5, "hang_muc": "Lấy phụ kiện có sẵn", "don_vi": "Cái", "he_so_diem": 0.5, "ghi_chu": "Kho / Vận hành"},
    {"stt": 7, "hang_muc": "Lấy mặt có sẵn", "don_vi": "Cái", "he_so_diem": 1.0, "ghi_chu": "Kho / Vận hành"},
    {"stt": 9, "hang_muc": "Vệ sinh + kiểm tra ,+ cắt hàng", "don_vi": "Cái", "he_so_diem": 1.5, "ghi_chu": "Kiểm tra chất lượng"},
    {"stt": 10, "hang_muc": "Kiểm tra BTP + cắt hàng", "don_vi": "Cái", "he_so_diem": 1.0, "ghi_chu": "Kiểm tra chất lượng"},
    {"stt": 11, "hang_muc": "Kiểm tra hộp + cất hàng", "don_vi": "Cái", "he_so_diem": 1.0, "ghi_chu": "Kiểm tra chất lượng"},
    {"stt": 12, "hang_muc": "Kiểm tra pha lê + cất hàng", "don_vi": "Cái", "he_so_diem": 2.0, "ghi_chu": "Kiểm tra chất lượng"},
    {"stt": 13, "hang_muc": "Giao hàng shiper", "don_vi": "Cái", "he_so_diem": 1.0, "ghi_chu": "Vận chuyển / Giao nhận"},
    {"stt": 14, "hang_muc": "tự đi giao hàng", "don_vi": "Cái", "he_so_diem": 2.0, "ghi_chu": "Vận chuyển / Giao nhận"},
    {"stt": 15, "hang_muc": "Nhận hàng gia công ngoài", "don_vi": "Cái", "he_so_diem": 0.1, "ghi_chu": "Vận chuyển / Giao nhận"},
    {"stt": 16, "hang_muc": "Cắp pha lê tấm", "don_vi": "Cái", "he_so_diem": 2.0, "ghi_chu": "Sản xuất / Gia công"},
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

# Hàm nén ảnh Avatar
def compress_image_to_base64(uploaded_file, max_size=(300, 300), quality=60):
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

# Hàm tính số phút thực tế từ giờ vào và giờ ra
def calculate_minutes(time_in_str, time_out_str):
    try:
        t1 = datetime.datetime.strptime(time_in_str, "%H:%M:%S")
        t2 = datetime.datetime.strptime(time_out_str, "%H:%M:%S")
        delta = t2 - t1
        minutes = int(delta.total_seconds() / 60)
        return max(0, minutes)
    except Exception:
        return 0

# Khởi tạo dữ liệu an toàn
def init_db_data():
    if supabase is None:
        return
    try:
        res_staff = supabase.table("staff").select("id").limit(1).execute()
        if not res_staff.data:
            for name in default_staff_list:
                supabase.table("staff").insert({"name": name}).execute()
        
        res_rules = supabase.table("rules").select("id").limit(1).execute()
        if not res_rules.data:
            for r in master_rules:
                supabase.table("rules").insert(r).execute()
    except Exception as e:
        st.warning(f"⚠️ Cảnh báo kết nối Supabase: {e}")

init_db_data()

# ==================== CÁC HÀM CRUD SUPABASE ====================
def get_staff_list_db():
    if supabase is None:
        return default_staff_list
    try:
        res = supabase.table("staff").select("name").execute()
        if res.data:
            return [row["name"] for row in res.data]
    except Exception:
        pass
    return default_staff_list

def save_staff_list_db(new_staffs):
    if supabase is None:
        return
    try:
        supabase.table("staff").delete().neq("id", 0).execute()
        for s in new_staffs:
            supabase.table("staff").insert({"name": s}).execute()
    except Exception:
        pass

def get_rules_df_db():
    if supabase is None:
        return pd.DataFrame(master_rules)
    try:
        res = supabase.table("rules").select("*").order("stt").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={"hang_muc": "Hạng Mục Công Việc", "don_vi": "Đơn Vị", "he_so_diem": "Hệ Số Điểm", "ghi_chu": "Ghi Chú"})
            return df
    except Exception:
        pass
    return pd.DataFrame(master_rules)

def save_rules_df_db(df):
    if supabase is None:
        return
    try:
        supabase.table("rules").delete().neq("id", 0).execute()
        for _, row in df.iterrows():
            payload = {
                "stt": int(row.get("STT", 1)),
                "hang_muc": row.get("Hạng Mục Công Việc", ""),
                "don_vi": row.get("Đơn Vị", "Cái"),
                "he_so_diem": float(row.get("Hệ Số Điểm", 1.0)),
                "ghi_chu": row.get("Ghi Chú", "")
            }
            supabase.table("rules").insert(payload).execute()
    except Exception:
        pass

def upload_image_to_storage(uploaded_file):
    if supabase is None or uploaded_file is None:
        return ""
    try:
        file_bytes = uploaded_file.getvalue()
        file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uploaded_file.name}"
        supabase.storage.from_("production-images").upload(file_name, file_bytes, {"content-type": uploaded_file.type})
        public_url_res = supabase.storage.from_("production-images").get_public_url(file_name)
        return public_url_res
    except Exception:
        return ""

def add_production_log_db(ngay, thoi_gian, nhan_su, hang_muc, hinh_anh_url, don_vi, so_luong, he_so, tong_diem, ghi_chu):
    if supabase is None:
        return
    try:
        payload = {
            "ngay": str(ngay),
            "thoi_gian": thoi_gian,
            "nhan_su": nhan_su,
            "hang_muc_cong_viec": hang_muc,
            "hinh_anh_url": hinh_anh_url,
            "don_vi": don_vi,
            "so_luong": int(so_luong),
            "he_so_diem": float(he_so),
            "tong_diem": float(tong_diem),
            "ghi_chu": ghi_chu,
            "is_deleted": False
        }
        supabase.table("production_logs").insert(payload).execute()
    except Exception:
        pass

def get_production_logs_db(is_deleted=False):
    if supabase is None:
        return pd.DataFrame(columns=["STT", "db_id", "Ngày", "Thời Gian", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"])
    try:
        res = supabase.table("production_logs").select("*").eq("is_deleted", is_deleted).order("id", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id",
                "ngay": "Ngày",
                "thoi_gian": "Thời Gian",
                "nhan_su": "Nhân Sự",
                "hang_muc_cong_viec": "Hạng Mục Công Việc",
                "hinh_anh_url": "Hình Ảnh",
                "don_vi": "Đơn Vị",
                "so_luong": "Số Lượng",
                "he_so_diem": "Hệ Số Điểm",
                "tong_diem": "Tổng Điểm",
                "ghi_chu": "Ghi Chú"
            })
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["STT", "db_id", "Ngày", "Thời Gian", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"])

def update_production_log_deleted_status(db_ids, is_deleted_val):
    if supabase is None:
        return
    try:
        for db_id in db_ids:
            supabase.table("production_logs").update({"is_deleted": is_deleted_val}).eq("id", db_id).execute()
    except Exception:
        pass

def permanent_delete_db(db_ids):
    if supabase is None:
        return
    try:
        for db_id in db_ids:
            supabase.table("production_logs").delete().eq("id", db_id).execute()
    except Exception:
        pass

def get_attendance_db():
    if supabase is None:
        return pd.DataFrame(columns=["STT", "db_id", "Ngày", "Nhân Sự", "Giờ Vào Ca", "Giờ Ra Ca", "Số Phút Làm Việc", "Ghi Chú"])
    try:
        res = supabase.table("attendance").select("*").order("id", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id",
                "ngay": "Ngày",
                "nhan_su": "Nhân Sự",
                "gio_vao_ca": "Giờ Vào Ca",
                "gio_ra_ca": "Giờ Ra Ca",
                "so_phut_lam_viec": "Số Phút Làm Việc",
                "ghi_chu": "Ghi Chú"
            })
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["STT", "db_id", "Ngày", "Nhân Sự", "Giờ Vào Ca", "Giờ Ra Ca", "Số Phút Làm Việc", "Ghi Chú"])

def add_attendance_db(ngay, nhan_su, gio_vao, gio_ra, phut, ghi_chu):
    if supabase is None:
        return
    try:
        payload = {
            "ngay": str(ngay),
            "nhan_su": nhan_su,
            "gio_vao_ca": gio_vao,
            "gio_ra_ca": gio_ra,
            "so_phut_lam_viec": int(phut),
            "ghi_chu": ghi_chu
        }
        supabase.table("attendance").insert(payload).execute()
    except Exception:
        pass

def update_attendance_checkout_db(nhan_su, ngay, gio_ra, phut, ghi_chu_moi):
    if supabase is None:
        return
    try:
        res = supabase.table("attendance").select("*").eq("nhan_su", nhan_su).eq("ngay", str(ngay)).eq("gio_ra_ca", "Chưa kết thúc").execute()
        if res.data:
            row_id = res.data[0]["id"]
            old_note = res.data[0].get("ghi_chu", "")
            final_note = f"{old_note} | {ghi_chu_moi}" if old_note else ghi_chu_moi
            supabase.table("attendance").update({
                "gio_ra_ca": gio_ra,
                "so_phut_lam_viec": int(phut),
                "ghi_chu": final_note
            }).eq("id", row_id).execute()
    except Exception:
        pass

def delete_attendance_db(db_ids):
    if supabase is None:
        return
    try:
        for db_id in db_ids:
            supabase.table("attendance").delete().eq("id", db_id).execute()
    except Exception:
        pass

# ==================== GÁN SESSION STATE & GIAO DIỆN ====================
st.session_state.staff_list = get_staff_list_db()
st.session_state.rules_df = get_rules_df_db()
st.session_state.chart_colors = default_chart_colors

if "folders" not in st.session_state or not st.session_state.folders:
    st.session_state.folders = default_folders

if "primary_color" not in st.session_state: st.session_state.primary_color = "#ff4b4b"
if "bg_color" not in st.session_state: st.session_state.bg_color = "#ffffff"
if "sidebar_bg" not in st.session_state: st.session_state.sidebar_bg = "#f0f2f6"
if "sidebar_opacity" not in st.session_state: st.session_state.sidebar_opacity = 0.9
if "text_color" not in st.session_state: st.session_state.text_color = "#31333F"
if "require_image" not in st.session_state: st.session_state.require_image = True
if "require_quantity" not in st.session_state: st.session_state.require_quantity = True
if "bg_image_base64" not in st.session_state: st.session_state.bg_image_base64 = None
if "avatar_base64" not in st.session_state: st.session_state.avatar_base64 = None
if "current_menu" not in st.session_state: st.session_state.current_menu = "1. Nhập Sản Lượng"

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
        padding-top: 1rem;
    }}
    p, span, label, div, h1, h2, h3, h4, h5, h6, 
    .stMarkdown, [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"], [data-testid="stMetricValue"], [data-testid="stMetricLabel"],
    [data-testid="stWidgetLabel"] *, .streamlit-expanderHeader *,
    [data-testid="stDataEditor"] *, [data-testid="stDataFrame"] *, [data-testid="stTable"] *,
    .stSelectbox *, .stDateInput *, .stNumberInput *, .stTextInput *, .stTimeInput *,
    table, th, td, tr {{
        color: {st.session_state.text_color} !important;
    }}
    h1 {{ color: {st.session_state.primary_color} !important; }}
    [data-testid="stSidebar"] {{
        background-color: {sidebar_rgba} !important;
        backdrop-filter: blur(8px);
    }}
    [data-testid="stSidebar"] > div:first-child {{
        display: flex; flex-direction: column; height: 100vh; overflow-y: auto !important; padding: 0px !important;
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

    .sidebar-scrollable-content {{ flex-grow: 1; padding-left: 1rem; padding-right: 1rem; padding-bottom: 50px; }}
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
        avatar_file = st.file_uploader("Tải ảnh", type=["png", "jpg", "jpeg"], key="avatar_uploader_popover_unique", label_visibility="collapsed")
        
        if avatar_file is not None:
            current_file_sig = f"{avatar_file.name}_{avatar_file.size}"
            if st.session_state.get("last_processed_avatar") != current_file_sig:
                compressed_avatar = compress_image_to_base64(avatar_file, max_size=(300, 300), quality=60)
                if compressed_avatar:
                    st.session_state.avatar_base64 = compressed_avatar
                    st.session_state["last_processed_avatar"] = current_file_sig
                    st.success("Đã cập nhật ảnh đại diện!")
                    st.rerun()
            
        if st.session_state.avatar_base64:
            st.markdown("---")
            if st.button("🗑️ Xóa Ảnh Đại Diện", use_container_width=True, key="btn_remove_avatar_unique"):
                st.session_state.avatar_base64 = None
                st.session_state["last_processed_avatar"] = None
                st.success("Đã xóa ảnh đại diện!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-scrollable-content">', unsafe_allow_html=True)
    if st.button("🔄 Cập Nhập", use_container_width=True):
        st.rerun()
    if st.button("⏱️ Chấm Công Ca Làm Việc", use_container_width=True):
        st.session_state.current_menu = "⏱️ Chấm Công Ca Làm Việc"
        st.rerun()

    st.markdown("---")
    st.markdown("### 📂 CHỨC NĂNG HỆ THỐNG")
    for folder in st.session_state.folders:
        with st.expander(folder["folder_name"], expanded=True):
            for item in folder["items"]:
                if st.button(item["name"], use_container_width=True, key=f"btn_{item['id']}"):
                    st.session_state.current_menu = item["name"]
                    st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Cấu Hình Hệ Thống")
    if st.button("📁 Quản Lý Thư Mục & Menu", use_container_width=True):
        st.session_state.current_menu = "📁 Quản Lý Thư Mục & Menu"
        st.rerun()
    if st.button("🎨 Cài Đặt Giao Diện", use_container_width=True):
        st.session_state.current_menu = "🎨 Cài Đặt Giao Diện"
        st.rerun()
    if st.button("🧹 Làm Sạch & Tối Ưu Dữ Liệu", use_container_width=True):
        st.session_state.current_menu = "🧹 Làm Sạch Dữ Liệu"
        st.rerun()

    st.markdown("---")
    st.markdown(f"<small>🟢 Supabase Cloud DB (Đã tối ưu)</small>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

menu = st.session_state.current_menu

def get_feature_type(menu_name):
    if menu_name == "⏱️ Chấm Công Ca Làm Việc": return "attendance"
    if menu_name == "📁 Quản Lý Thư Mục & Menu": return "manage_folders"
    if menu_name == "🎨 Cài Đặt Giao Diện": return "settings_ui"
    if menu_name == "🧹 Làm Sạch Dữ Liệu": return "clean_data"
    for folder in st.session_state.folders:
        for item in folder["items"]:
            if item["name"] == menu_name:
                if item["id"] == "menu_1": return "input_production"
                if item["id"] == "menu_2": return "report"
                if item["id"] == "menu_3": return "rules"
                if item["id"] == "menu_4": return "trash"
                return "input_production"
    return "input_production"

feature = get_feature_type(menu)

# ==================== 1. NHẬP SẢN LƯỢNG ====================
if feature == "input_production":
    now_vn = datetime.datetime.now(VN_TIMEZONE)
    today_str = str(now_vn.date())
    
    att_df_check = get_attendance_db()
    checked_in_set = set()
    if not att_df_check.empty:
        today_att = att_df_check[att_df_check["Ngày"] == today_str]
        checked_in_set = set(today_att[today_att["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist())

    active_staff = [s for s in st.session_state.staff_list if s in checked_in_set]

    st.subheader(f"{menu} ({today_str})")

    if not active_staff:
        st.warning(f"⚠️ Hôm nay ({today_str}) chưa có nhân sự nào **Check-in (Vào ca)** hoặc đã Check-out. Vui lòng thực hiện Check-in trước khi nhập sản lượng!")
    else:
        req_img = st.session_state.get("require_image", True)
        req_qty = st.session_state.get("require_quantity", True)
        
        with st.form("entry_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                ngay = st.date_input("Ngày làm việc", now_vn.date(), disabled=True)
            with f_col2:
                nhan_su = st.selectbox("Nhân sự thực hiện", active_staff)
            with f_col3:
                danh_sach_hang_muc = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else []
                hang_muc = st.selectbox("Hạng mục công việc", danh_sach_hang_muc)
                
            record_image = st.file_uploader("Tải ảnh đính kèm", type=["png", "jpg", "jpeg"], key="record_img")
                    
            f_col4, f_col5 = st.columns(2)
            with f_col4:
                so_luong = st.number_input("Số lượng thực tế", min_value=0, value=0, step=1)
            with f_col5:
                ghi_chu = st.text_input("Ghi chú", "")
                
            submitted = st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True)

            if submitted:
                is_valid = True
                if req_img and record_image is None: is_valid = False
                if req_qty and so_luong <= 0: is_valid = False

                if not is_valid:
                    st.session_state["form_msg"] = ("error", "⚠️ Vui lòng điền đủ ảnh đính kèm và số lượng > 0 theo cấu hình!")
                else:
                    row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
                    he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
                    don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
                    tong_diem = so_luong * he_so
                    
                    img_url = upload_image_to_storage(record_image) if record_image else ""
                    current_time_str = datetime.datetime.now(VN_TIMEZONE).strftime("%H:%M:%S")
                    
                    add_production_log_db(today_str, current_time_str, nhan_su, hang_muc, img_url, don_vi, so_luong, he_so, tong_diem, ghi_chu)
                    st.session_state["form_msg"] = ("success", f"✅ Ghi nhận thành công cho **{nhan_su}**! Tổng điểm: **{tong_diem} điểm**")

        # Hiển thị thông báo ngay bên dưới nút Báo Cáo Sản Lượng
        if "form_msg" in st.session_state:
            m_type, m_text = st.session_state["form_msg"]
            if m_type == "success":
                st.success(m_text)
            else:
                st.error(m_text)
            del st.session_state["form_msg"]

    st.markdown("---")
    st.subheader("Danh Sách Sản Lượng & Hình Ảnh")
    
    input_df = get_production_logs_db(is_deleted=False)
    if not input_df.empty:
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            all_dates = ["Tất cả"] + sorted(input_df["Ngày"].unique().tolist())
            filter_date = st.selectbox("Lọc theo Ngày", all_dates)
        with s_col2:
            all_staff = ["Tất cả"] + sorted(input_df["Nhân Sự"].unique().tolist())
            filter_staff = st.selectbox("Lọc theo Nhân Sự", all_staff)
        
        filtered_df = input_df.copy()
        if filter_date != "Tất cả": filtered_df = filtered_df[filtered_df["Ngày"] == filter_date]
        if filter_staff != "Tất cả": filtered_df = filtered_df[filtered_df["Nhân Sự"] == filter_staff]
            
        if not filtered_df.empty:
            with st.form("input_delete_form"):
                for idx, row in filtered_df.iterrows():
                    row_c1, row_c2 = st.columns([4, 1])
                    with row_c1:
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;">
                            <b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} ⏰ {row['Thời Gian']} &nbsp;|&nbsp; 👤 <b>{row['Nhân Sự']}</b><br>
                            📌 {row['Hạng Mục Công Việc']} &nbsp;|&nbsp; 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                            💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                        </div>
                        """, unsafe_allow_html=True)
                        is_selected = st.checkbox(f"Xóa bản ghi STT {row['STT']}", key=f"chk_{row['db_id']}")
                        filtered_df.loc[idx, "Chọn_Xóa"] = is_selected
                    with row_c2:
                        img_url_val = row.get("Hình Ảnh", "")
                        if img_url_val:
                            st.image(img_url_val, width=60)
                        else:
                            st.text("Không có ảnh")
                    st.markdown("---")
                    
                if st.form_submit_button("🗑️ Chuyển Các Dòng Đã Chọn Vào Thùng Rác", use_container_width=True):
                    selected_db_ids = filtered_df[filtered_df["Chọn_Xóa"] == True]["db_id"].tolist()
                    if selected_db_ids:
                        update_production_log_deleted_status(selected_db_ids, True)
                        st.success("Đã chuyển các dòng đã chọn vào thùng rác!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn dòng cần xóa!")
        else:
            st.info("Không tìm thấy bản ghi nào khớp bộ lọc.")
    else:
        st.info("Chưa có dữ liệu sản lượng.")

# ==================== CHẤM CÔNG CA LÀM VIỆC ====================
elif feature == "attendance":
    st.header(menu)
    now_vn = datetime.datetime.now(VN_TIMEZONE)
    today_str = str(now_vn.date())
    
    att_df = get_attendance_db()
    checked_in_set = set(att_df[(att_df["Ngày"] == today_str) & (att_df["Giờ Ra Ca"] == "Chưa kết thúc")]["Nhân Sự"].tolist()) if not att_df.empty else set()

    staff_lines = ""
    for s in st.session_state.staff_list:
        if s in checked_in_set: staff_lines += f"🟢 <b>{s}</b> - Đang Làm Việc<br>"
        else: staff_lines += f"🔴 <b>{s}</b> - Không hoạt động<br>"
    st.markdown(f"<div style='background: rgba(255,255,255,0.7); padding: 10px; border-radius: 6px; margin-bottom: 15px;'>{staff_lines}</div>", unsafe_allow_html=True)

    with st.form("attendance_form"):
        f1, f2, f3 = st.columns(3)
        with f1: att_date = st.date_input("Ngày", now_vn.date())
        with f2: att_staff = st.selectbox("Nhân sự", st.session_state.staff_list)
        with f3: att_note = st.text_input("Ghi chú ca", "")
        
        b1, b2 = st.columns(2)
        with b1: check_in = st.form_submit_button("🟢 Check-in (Vào ca)", use_container_width=True)
        with b2: check_out = st.form_submit_button("🔴 Check-out (Kết thúc)", use_container_width=True)
        
        time_str = now_vn.strftime("%H:%M:%S")
        if check_in:
            if att_staff in checked_in_set:
                st.session_state["att_msg"] = ("warning", f"Nhân sự {att_staff} đang trong ca làm việc!")
            else:
                add_attendance_db(att_date, att_staff, time_str, "Chưa kết thúc", 0, att_note)
                st.session_state["att_msg"] = ("success", f"Đã Vào ca cho {att_staff} lúc {time_str}!")
                st.rerun()
        if check_out:
            res_check = supabase.table("attendance").select("*").eq("nhan_su", att_staff).eq("ngay", str(att_date)).eq("gio_ra_ca", "Chưa kết thúc").execute() if supabase else None
            
            if res_check and res_check.data:
                gio_vao_ca = res_check.data[0].get("gio_vao_ca", "00:00:00")
                so_phut_thuc_te = calculate_minutes(gio_vao_ca, time_str)
                
                update_attendance_checkout_db(att_staff, att_date, time_str, so_phut_thuc_te, att_note)
                st.session_state["att_msg"] = ("success", f"Đã Kết thúc ca cho {att_staff} lúc {time_str} (Tổng thời gian: {so_phut_thuc_te} phút)!")
            else:
                update_attendance_checkout_db(att_staff, att_date, time_str, 0, att_note)
                st.session_state["att_msg"] = ("warning", f"Đã kết thúc ca nhưng không tìm thấy mốc Vào ca tương ứng trong ngày!")
            st.rerun()

    # Hiển thị thông báo chấm công ngay dưới form
    if "att_msg" in st.session_state:
        m_type, m_text = st.session_state["att_msg"]
        if m_type == "success": st.success(m_text)
        else: st.warning(m_text)
        del st.session_state["att_msg"]

    st.markdown("---")
    st.subheader("📋 Lịch Sử Chấm Công")
    if not att_df.empty:
        st.dataframe(att_df.drop(columns=["db_id"]), use_container_width=True, hide_index=True)

# ==================== BÁO CÁO & BIỂU ĐỒ ====================
elif feature == "report":
    st.header(menu)
    
    all_staff_current = st.session_state.staff_list
    
    input_df = get_production_logs_db(is_deleted=False)
    if not input_df.empty:
        summary = input_df.groupby("Nhân Sự").agg(
            Tổng_Số_Lượng=("Số Lượng", "sum"),
            Tổng_Điểm=("Tổng Điểm", "sum")
        ).reset_index()
    else:
        summary = pd.DataFrame(columns=["Nhân Sự", "Tổng_Số_Lượng", "Tổng_Điểm"])

    if not summary.empty:
        summary = summary[summary["Nhân Sự"].isin(all_staff_current)]
        summary = summary[summary["Tổng_Điểm"] > 0]
    
    total_all_points = summary["Tổng_Điểm"].sum() if not summary.empty else 0
    if not summary.empty:
        summary["Tỷ_Lệ_Đóng_Góp"] = summary["Tổng_Điểm"].apply(lambda x: (x / total_all_points) if total_all_points > 0 else 0)
        
        def rank_func(pts):
            if pts >= 700: return "Xuất Sắc"
            elif pts >= 400: return "Đạt"
            else: return "Cần Cố Gắn"
                
        summary["Xếp_Loại"] = summary["Tổng_Điểm"].apply(rank_func)
        summary_display = summary[["Nhân Sự", "Tổng_Số_Lượng", "Tổng_Điểm", "Tỷ_Lệ_Đóng_Góp", "Xếp_Loại"]].copy()
        summary_display.columns = ["Nhân Sự", "Số Lượng Thực Tế", "Tổng Điểm", "Tỷ Lệ Đóng Góp", "Xếp Loại"]
    else:
        summary_display = pd.DataFrame(columns=["Nhân Sự", "Số Lượng Thực Tế", "Tổng Điểm", "Tỷ Lệ Đóng Góp", "Xếp Loại"])
    
    st.subheader("Bảng Tổng Kết Theo Nhân Sự")
    if not summary_display.empty:
        st.dataframe(
            summary_display.style.format({
                "Số Lượng Thực Tế": "{:,.0f}",
                "Tổng Điểm": "{:,.1f}",
                "Tỷ Lệ Đóng Góp": "{:.2%}"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Chưa có dữ liệu sản lượng từ nhân sự nào.")
    
    st.markdown("---")
    st.subheader("⚖️ Bảng Đối Chiếu Thời Gian Làm Việc & Sản Lượng")
    
    att_df = get_attendance_db()
    if not att_df.empty:
        att_summary = att_df.groupby("Nhân Sự")["Số Phút Làm Việc"].sum().reset_index()
        att_summary.columns = ["Nhân Sự", "Tổng Phút Làm Việc"]
    else:
        att_summary = pd.DataFrame(columns=["Nhân Sự", "Tổng Phút Làm Việc"])
        
    if not summary.empty or not att_summary.empty:
        comparison_df = pd.merge(summary, att_summary, on="Nhân Sự", how="outer").fillna(0)
        
        comparison_df = comparison_df[comparison_df["Nhân Sự"].isin(all_staff_current)]
        comparison_df = comparison_df[(comparison_df["Tổng_Điểm"] > 0) | (comparison_df["Tổng Phút Làm Việc"] > 0)]
        
        if not comparison_df.empty:
            comparison_df = comparison_df.sort_values(by="Tổng_Điểm", ascending=False).reset_index(drop=True)
            
            rank_badges = []
            current_rank_num = 1
            for idx in range(len(comparison_df)):
                if idx > 0 and comparison_df.loc[idx, "Tổng_Điểm"] == comparison_df.loc[idx - 1, "Tổng_Điểm"]:
                    rank_badges.append(rank_badges[-1])
                else:
                    if idx > 0: current_rank_num += 1
                    else: current_rank_num = 1
                        
                    if current_rank_num == 1: rank_badges.append("🥇 Hạng 1")
                    elif current_rank_num == 2: rank_badges.append("🥈 Hạng 2")
                    elif current_rank_num == 3: rank_badges.append("🥉 Hạng 3")
                    else: rank_badges.append(f"Top {current_rank_num}")
                    
            comparison_df.insert(0, "Xếp Hạng", rank_badges)
            
            total_minutes_all = comparison_df["Tổng Phút Làm Việc"].sum()
            comparison_df["Tỷ_Lệ_Thời_Gian"] = comparison_df["Tổng Phút Làm Việc"].apply(lambda x: (x / total_minutes_all) if total_minutes_all > 0 else 0)
            
            total_pts_all = comparison_df["Tổng_Điểm"].sum()
            comparison_df["Tỷ_Lệ_Đóng_Góp"] = comparison_df["Tổng_Điểm"].apply(lambda x: (x / total_pts_all) if total_pts_all > 0 else 0)
            
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
        else:
            st.info("Chưa có dữ liệu chấm công hoặc sản lượng hợp lệ từ nhân sự trong danh sách.")
    else:
        st.info("Chưa có dữ liệu đối chiếu.")

# ==================== THAM CHIẾU CÔNG VIỆC ====================
elif feature == "rules":
    st.header(menu)
    with st.form("rules_form"):
        edited_rules = st.data_editor(st.session_state.rules_df, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.form_submit_button("💾 Lưu Thay Đổi Định Mức", use_container_width=True):
            save_rules_df_db(edited_rules)
            st.success("Đã lưu định mức thành công!")
            st.rerun()

# ==================== THÙNG RÁC SẢN LƯỢNG ====================
elif feature == "trash":
    st.header(menu)
    trash_df = get_production_logs_db(is_deleted=True)
    if not trash_df.empty:
        with st.form("trash_form"):
            for idx, row in trash_df.iterrows():
                st.markdown(f"**{row['Nhân Sự']}** - {row['Hạng Mục Công Việc']} - {row['Số Lượng']} {row['Đơn Vị'] if 'Đơn Vị' in row else ''}")
                is_sel = st.checkbox(f"Chọn STT {row['STT']}", key=f"t_{row['db_id']}")
                trash_df.loc[idx, "Chọn"] = is_sel
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📥 Khôi Phục Đã Chọn", use_container_width=True):
                    ids = trash_df[trash_df["Chọn"] == True]["db_id"].tolist()
                    if ids:
                        update_production_log_deleted_status(ids, False)
                        st.success("Đã khôi phục thành công!")
                        st.rerun()
            with c2:
                if st.form_submit_button("🔥 Xóa Vĩnh Viễn", use_container_width=True):
                    ids = trash_df[trash_df["Chọn"] == True]["db_id"].tolist()
                    if ids:
                        permanent_delete_db(ids)
                        st.success("Đã xóa vĩnh viễn!")
                        st.rerun()
    else:
        st.info("Thùng rác trống.")

# ==================== QUẢN LÝ THƯ MỤC & MENU ====================
elif feature == "manage_folders":
    st.header("Quản Lý Thư Mục & Menu")
    
    with st.form("manage_menu_form"):
        st.markdown("##### Tên thư mục")
        new_folder_name = st.text_input("Tên thư mục", value=st.session_state.folders[0]["folder_name"], label_visibility="collapsed")
        
        st.markdown("##### Danh sách mục menu bên trong:")
        
        updated_items = []
        for i_idx, item in enumerate(st.session_state.folders[0]["items"]):
            new_name = st.text_input(f"Tên hiển thị {i_idx+1}", value=item["name"], key=f"edit_name_{i_idx}")
            updated_items.append({"id": item["id"], "name": new_name})
            
        submitted_menu = st.form_submit_button("💾 Lưu Thay Đổi", use_container_width=True)
        if submitted_menu:
            st.session_state.folders[0]["folder_name"] = new_folder_name
            st.session_state.folders[0]["items"] = updated_items
            st.success("Đã cập nhật tên thư mục và tên hiển thị menu thành công!")
            st.rerun()

# ==================== CÀI ĐẶT GIAO DIỆN ====================
elif feature == "settings_ui":
    st.header("Cài Đặt Giao Diện & Nhân Sự")
    with st.form("staff_form"):
        staff_df = pd.DataFrame({"Nhân Sự": st.session_state.staff_list})
        edited_staff = st.data_editor(staff_df, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.form_submit_button("💾 Lưu Danh Sách Nhân Sự", use_container_width=True):
            new_list = [str(x).strip() for x in edited_staff["Nhân Sự"].tolist() if str(x).strip()]
            save_staff_list_db(new_list)
            st.success("Đã lưu danh sách nhân sự!")
            st.rerun()

# ==================== LÀM SẠCH DỮ LIỆU ====================
elif feature == "clean_data":
    st.header("Làm Sạch Dữ Liệu")
    if st.button("🔥 Xóa Toàn Bộ Dữ Liệu Thùng Rác Vĩnh Viễn", use_container_width=True):
        trash_df = get_production_logs_db(is_deleted=True)
        if not trash_df.empty:
            permanent_delete_db(trash_df["db_id"].tolist())
            st.success("Đã làm sạch thùng rác!")
            st.rerun()
