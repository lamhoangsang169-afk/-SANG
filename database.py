import streamlit as st
import pandas as pd
import datetime
from utils import VN_TIMEZONE

# Thử import supabase
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False

SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]

def init_supabase_client():
    if not HAS_SUPABASE_LIB:
        return None, False
    try:
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase_client.table("staff").select("id").limit(1).execute()
        return supabase_client, True
    except Exception as e:
        st.error(f"Lỗi kết nối Supabase: {e}")
        return None, False

supabase, is_supabase_connected = init_supabase_client()

# Dữ liệu mặc định phòng hờ
default_staff_list = ["Nguyễn Hữu Khang Tôn Đức", "Nguyễn Đức Anh Tiến", "Trần Gia Bảo"]
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
    except Exception:
        pass

@st.cache_data(ttl=300, show_spinner=False)
def get_staff_df_db():
    if supabase is None:
        return pd.DataFrame({"id": range(1, len(default_staff_list)+1), "Nhân Sự": default_staff_list})
    try:
        res = supabase.table("staff").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            if "name" in df.columns:
                df = df.rename(columns={"name": "Nhân Sự"})
            if "id" not in df.columns:
                df.insert(0, "id", range(1, len(df) + 1))
            return df[["id", "Nhân Sự"]]
    except Exception:
        pass
    return pd.DataFrame({"id": range(1, len(default_staff_list)+1), "Nhân Sự": default_staff_list})

def get_staff_list_db():
    df = get_staff_df_db()
    if not df.empty and "Nhân Sự" in df.columns:
        return [str(x).strip() for x in df["Nhân Sự"].tolist() if str(x).strip()]
    return default_staff_list

@st.cache_data(ttl=300, show_spinner=False)
def get_rules_df_db():
    if supabase is None:
        df = pd.DataFrame(master_rules)
    else:
        try:
            res = supabase.table("rules").select("*").order("stt").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                df = df.rename(columns={"hang_muc": "Hạng Mục Công Việc", "don_vi": "Đơn Vị", "he_so_diem": "Hệ Số Điểm", "ghi_chu": "Ghi Chú"})
            else:
                df = pd.DataFrame(master_rules)
        except Exception:
            df = pd.DataFrame(master_rules)
    if not df.empty:
        df["stt"] = range(1, len(df) + 1)
    return df

@st.cache_data(ttl=150, show_spinner=False)
def get_production_logs_db(is_deleted=False, limit_rows=100):
    if supabase is None:
        return pd.DataFrame()
    try:
        res = supabase.table("production_logs").select("*").eq("is_deleted", is_deleted).order("id", desc=True).limit(limit_rows).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id", "ngay": "Ngày", "thoi_gian": "Thời Gian", "nhan_su": "Nhân Sự",
                "hang_muc_cong_viec": "Hạng Mục Công Việc", "hinh_anh_url": "Hình Ảnh", "don_vi": "Đơn Vị",
                "so_luong": "Số Lượng", "he_so_diem": "Hệ Số Điểm", "tong_diem": "Tổng Điểm", "ghi_chu": "Ghi Chú"
            })
            df.insert(0, "STT", range(len(df), 0, -1))
            return df
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=150, show_spinner=False)
def get_production_logs_by_date_range(start_date, end_date):
    if supabase is None:
        return pd.DataFrame()
    try:
        res = supabase.table("production_logs")\
            .select("*")\
            .eq("is_deleted", False)\
            .gte("ngay", str(start_date))\
            .lte("ngay", str(end_date))\
            .order("id", desc=True)\
            .limit(2000)\
            .execute()
            
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id", "ngay": "Ngày", "thoi_gian": "Thời Gian", "nhan_su": "Nhân Sự",
                "hang_muc_cong_viec": "Hạng Mục Công Việc", "hinh_anh_url": "Hình Ảnh", "don_vi": "Đơn Vị",
                "so_luong": "Số Lượng", "he_so_diem": "Hệ Số Điểm", "tong_diem": "Tổng Điểm", "ghi_chu": "Ghi Chú"
            })
            df.insert(0, "STT", range(len(df), 0, -1))
            return df
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=150, show_spinner=False)
def get_total_production_count_db():
    if supabase is None:
        return 0
    try:
        res = supabase.table("production_logs").select("id", count="exact").eq("is_deleted", False).execute()
        if res.count is not None:
            return res.count
    except Exception:
        pass
    return 0

@st.cache_data(ttl=150, show_spinner=False)
def get_attendance_db():
    if supabase is None:
        return pd.DataFrame()
    try:
        res = supabase.table("attendance").select("*").order("id", desc=True).limit(100).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id", "ngay": "Ngày", "nhan_su": "Nhân Sự", "gio_vao_ca": "Giờ Vào Ca",
                "gio_ra_ca": "Giờ Ra Ca", "so_phut_lam_viec": "Số Phút Làm Việc", "ghi_chu": "Ghi Chú"
            })
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_app_settings_db():
    if supabase is None:
        return {}
    try:
        res = supabase.table("app_settings").select("*").eq("id", 1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception:
        pass
    return {}

@st.cache_data(ttl=300, show_spinner=False)
def load_folders_db():
    default_folders = [{
        "folder_name": "📌 Quản Lý Nghiệp Vụ",
        "items": [
            {"id": "menu_1", "name": "1. Nhập Sản Lượng"},
            {"id": "menu_2", "name": "2. Báo Cáo & Biểu Đồ"},
            {"id": "menu_3", "name": "3. Tham Chiếu Công Việc"},
            {"id": "menu_4", "name": "4. Thùng Rác Sản Lượng"},
            {"id": "menu_5", "name": "5. Thư Mục Báo Cáo"}
        ]
    }]
    if supabase is None:
        return default_folders
    try:
        res = supabase.table("app_folders").select("folders_json").eq("id", 1).execute()
        if res.data and len(res.data) > 0 and res.data[0].get("folders_json"):
            return res.data[0]["folders_json"]
    except Exception:
        pass
    return default_folders

# ==================== CÁC HÀM XỬ LÝ BÌNH LUẬN ====================
@st.cache_data(ttl=60, show_spinner=False)
def get_comments_by_log_id(log_id):
    if supabase is None:
        return []
    try:
        res = supabase.table("comments").select("*").eq("production_log_id", log_id).order("id", desc=False).execute()
        return res.data if res.data else []
    except Exception:
        return []

def add_comment_db(log_id, nguoi_binh_luan, noi_dung):
    if supabase is None:
        return
    try:
        current_time = datetime.datetime.now(VN_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "production_log_id": int(log_id),
            "nguoi_binh_luan": str(nguoi_binh_luan),
            "noi_dung": str(noi_dung),
            "ngay_gio": current_time
        }
        supabase.table("comments").insert(payload).execute()
        st.cache_data.clear()
    except Exception:
        pass
