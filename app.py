import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import io
import base64
import os
from PIL import Image
import json

# Thử import supabase
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False

st.set_page_config(page_title="POSS - Quản Lý Sản Xuất", page_icon="📊", layout="wide")

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
            {"id": "menu_4", "name": "4. Thùng Rác Sản Lượng"},
            {"id": "menu_5", "name": "5. Thư Mục Báo Cáo"}
        ]
    }
]

# ==================== KIỂM TRA ĐĂNG NHẬP SESSION & QUERY PARAMS ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

params = st.query_params
if not st.session_state.logged_in and "auth_user" in params:
    st.session_state.logged_in = True
    st.session_state.user_email = params["auth_user"]

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.9); padding: 30px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.15); border: 1px solid #e2e8f0;">
            <h2 style="text-align: center; color: #ff4b4b; margin-bottom: 20px;">🔐 ĐĂNG NHẬP HỆ THỐNG POSS</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email_input = st.text_input("📧 Email tài khoản", placeholder="Nhập email của bạn...")
            password_input = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
            submitted_login = st.form_submit_button("🚀 Đăng Nhập", use_container_width=True)
            
            if submitted_login:
                if not email_input or not password_input:
                    st.error("⚠️ Vui lòng nhập đầy đủ Email và Mật khẩu!")
                elif supabase is None:
                    st.error("⚠️ Chưa kết nối được tới Supabase!")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({
                            "email": email_input.strip(),
                            "password": password_input.strip()
                        })
                        if res and res.user:
                            st.session_state.logged_in = True
                            st.session_state.user_email = res.user.email
                            st.query_params["auth_user"] = res.user.email
                            st.success("✅ Đăng nhập thành công!")
                            st.rerun()
                        else:
                            st.error("❌ Email hoặc mật khẩu không chính xác!")
                    except Exception as e:
                        st.error(f"❌ Đăng nhập thất bại: Vui lòng kiểm tra lại thông tin.")
    st.stop()

# ==================== PHẦN CHỨC NĂNG SAU KHI ĐĂNG NHẬP ====================

def compress_image_to_base64(uploaded_file, max_size=(800, 800), quality=60):
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

def calculate_exact_minutes(date_in_str, time_in_str, date_out_str, time_out_str):
    try:
        dt1 = datetime.datetime.strptime(f"{date_in_str} {time_in_str}", "%Y-%m-%d %H:%M:%S")
        dt2 = datetime.datetime.strptime(f"{date_out_str} {time_out_str}", "%Y-%m-%d %H:%M:%S")
        delta = dt2 - dt1
        minutes = int(delta.total_seconds() / 60)
        return max(0, minutes)
    except Exception:
        return 0

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

init_db_data()

# ==================== CÁC HÀM CRUD & CACHING SUPABASE (ĐÃ TỐI ƯU TTL) ====================
@st.cache_data(ttl=600, show_spinner=False)
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

def save_staff_list_db(edited_df):
    if supabase is None:
        return
    try:
        res_old = supabase.table("staff").select("id, name").execute()
        old_staffs = {row["id"]: row["name"] for row in res_old.data} if res_old.data else {}
        old_ids = list(old_staffs.keys())
        
        current_ids_in_editor = []
        for _, row in edited_df.iterrows():
            name = str(row.get("Nhân Sự", "")).strip()
            row_id = row.get("id")
            
            if not name:
                continue
                
            if pd.notna(row_id) and int(row_id) in old_ids:
                supabase.table("staff").update({"name": name}).eq("id", int(row_id)).execute()
                current_ids_in_editor.append(int(row_id))
            else:
                res_ins = supabase.table("staff").insert({"name": name}).execute()
                if res_ins.data:
                    current_ids_in_editor.append(res_ins.data[0]["id"])
                    
        ids_to_delete = [oid for oid in old_ids if oid not in current_ids_in_editor]
        for del_id in ids_to_delete:
            deleted_name = old_staffs.get(del_id)
            supabase.table("staff").delete().eq("id", del_id).execute()
            if deleted_name:
                supabase.table("production_logs").delete().eq("nhan_su", deleted_name).execute()
                supabase.table("attendance").delete().eq("nhan_su", deleted_name).execute()
        
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi khi xóa nhân sự và dữ liệu liên quan: {e}")

@st.cache_data(ttl=600, show_spinner=False)
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

def save_rules_df_db(df):
    if supabase is None:
        return
    try:
        res_old = supabase.table("rules").select("id, hang_muc, he_so_diem").execute()
        old_rules_map = {row["id"]: {"hang_muc": row["hang_muc"], "he_so_diem": row["he_so_diem"]} for row in res_old.data} if res_old.data else {}
        old_ids = list(old_rules_map.keys())
        
        current_ids_in_editor = []
        thirty_days_ago = (datetime.datetime.now(VN_TIMEZONE) - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        for idx, row in df.iterrows():
            row_id = row.get("id")
            new_hang_muc = str(row.get("Hạng Mục Công Việc", "")).strip()
            new_he_so = float(row.get("Hệ Số Điểm", 1.0)) if pd.notna(row.get("Hệ Số Điểm")) else 1.0
            
            if not new_hang_muc:
                continue
                
            payload = {
                "stt": int(idx + 1),
                "hang_muc": new_hang_muc,
                "don_vi": str(row.get("Đơn Vị", "Cái")).strip() if pd.notna(row.get("Đơn Vị")) else "Cái",
                "he_so_diem": new_he_so,
                "ghi_chu": str(row.get("Ghi Chú", "")).strip() if pd.notna(row.get("Ghi Chú")) else ""
            }
            
            if pd.notna(row_id) and int(row_id) in old_ids:
                rid = int(row_id)
                old_info = old_rules_map.get(rid, {"hang_muc": "", "he_so_diem": 1.0})
                old_hang_muc = old_info["hang_muc"]
                old_he_so = old_info["he_so_diem"]
                
                supabase.table("rules").update(payload).eq("id", rid).execute()
                current_ids_in_editor.append(rid)
                
                if old_hang_muc and old_hang_muc != new_hang_muc:
                    supabase.table("production_logs").update({
                        "hang_muc_cong_viec": new_hang_muc
                    }).eq("hang_muc_cong_viec", old_hang_muc).gte("ngay", thirty_days_ago).execute()
                
                target_hang_muc_name = new_hang_muc if new_hang_muc else old_hang_muc
                if old_he_so != new_he_so:
                    res_logs = supabase.table("production_logs").select("id, so_luong").eq("hang_muc_cong_viec", target_hang_muc_name).gte("ngay", thirty_days_ago).eq("is_deleted", False).execute()
                    if res_logs.data:
                        for lg in res_logs.data:
                            lg_id = lg["id"]
                            qty = lg["so_luong"]
                            new_total_points = qty * new_he_so
                            supabase.table("production_logs").update({
                                "he_so_diem": new_he_so,
                                "tong_diem": new_total_points
                            }).eq("id", lg_id).execute()
            else:
                res_ins = supabase.table("rules").insert(payload).execute()
                if res_ins.data:
                    current_ids_in_editor.append(res_ins.data[0]["id"])
                    
        ids_to_delete = [oid for oid in old_ids if oid not in current_ids_in_editor]
        for del_id in ids_to_delete:
            supabase.table("rules").delete().eq("id", del_id).execute()
            
        st.cache_data.clear()
        st.success("Đã đồng bộ định mức, tự động cập nhật STT và tính lại điểm số 30 ngày gần nhất thành công!")
    except Exception as e:
        st.error(f"Lỗi khi đồng bộ định mức: {e}")

@st.cache_data(ttl=600, show_spinner=False)
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

def save_app_settings_db(settings_dict):
    if supabase is None:
        return
    try:
        payload = {"id": 1, **settings_dict}
        supabase.table("app_settings").upsert(payload).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi lưu cấu hình: {e}")

@st.cache_data(ttl=600, show_spinner=False)
def load_folders_db():
    if supabase is None:
        return default_folders
    try:
        res = supabase.table("app_folders").select("folders_json").eq("id", 1).execute()
        if res.data and len(res.data) > 0 and res.data[0].get("folders_json"):
            return res.data[0]["folders_json"]
    except Exception:
        pass
    return default_folders

def save_folders_db(folders_list):
    if supabase is None:
        return
    try:
        payload = {"id": 1, "folders_json": folders_list}
        supabase.table("app_folders").upsert(payload).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi lưu thư mục: {e}")

def upload_multiple_images_to_storage(uploaded_files):
    if supabase is None or not uploaded_files:
        return ""
    url_list = []
    for uploaded_file in uploaded_files[:4]:
        try:
            file_bytes = uploaded_file.getvalue()
            file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uploaded_file.name}"
            supabase.storage.from_("production-images").upload(file_name, file_bytes, {"content-type": uploaded_file.type})
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/production-images/{file_name}"
            url_list.append(public_url)
        except Exception:
            pass
    return ",".join(url_list)

def upload_report_to_storage(file_name, csv_bytes):
    if supabase is None:
        return ""
    try:
        unique_file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
        supabase.storage.from_("reports-storage").upload(unique_file_name, csv_bytes, {"content-type": "text/csv; charset=utf-8"})
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/reports-storage/{unique_file_name}"
        return public_url
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
        st.cache_data.clear()
    except Exception:
        pass

@st.cache_data(ttl=300, show_spinner=False)
def get_production_logs_db(is_deleted=False, limit_rows=200):
    if supabase is None:
        return pd.DataFrame(columns=["STT", "db_id", "Ngày", "Thời Gian", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"])
    try:
        res = supabase.table("production_logs").select("*").eq("is_deleted", is_deleted).order("id", desc=True).limit(limit_rows).execute()
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
            df.insert(0, "STT", range(len(df), 0, -1))
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
        st.cache_data.clear()
    except Exception:
        pass

def permanent_delete_db(db_ids):
    if supabase is None:
        return
    try:
        for db_id in db_ids:
            supabase.table("production_logs").delete().eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception:
        pass

@st.cache_data(ttl=300, show_spinner=False)
def get_attendance_db():
    if supabase is None:
        return pd.DataFrame(columns=["STT", "db_id", "Ngày", "Nhân Sự", "Giờ Vào Ca", "Giờ Ra Ca", "Số Phút Làm Việc", "Ghi Chú"])
    try:
        res = supabase.table("attendance").select("*").order("id", desc=True).limit(100).execute()
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
        st.cache_data.clear()
    except Exception:
        pass

def delete_attendance_db(db_ids):
    if supabase is None:
        return
    try:
        for db_id in db_ids:
            supabase.table("attendance").delete().eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception:
        pass

def save_export_report_db(ten_file, file_url):
    if supabase is None:
        st.error("Chưa kết nối Supabase!")
        return
    try:
        payload = {
            "ten_file": ten_file,
            "ngay_tao": datetime.datetime.now(VN_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
            "file_url": file_url,
            "is_deleted": False
        }
        supabase.table("export_reports").insert(payload).execute()
        st.success("Đã lưu thông tin báo cáo vào cơ sở dữ liệu thành công!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi khi lưu vào bảng export_reports: {e}")

@st.cache_data(ttl=300, show_spinner=False)
def get_export_reports_db(is_deleted=False):
    if supabase is None:
        return pd.DataFrame(columns=["STT", "db_id", "Tên File", "Ngày Tạo", "Đường Dẫn URL"])
    try:
        res = supabase.table("export_reports").select("*").eq("is_deleted", is_deleted).order("id", desc=True).limit(50).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id",
                "ten_file": "Tên File",
                "ngay_tao": "Ngày Tạo",
                "file_url": "Đường Dẫn URL"
            })
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["STT", "db_id", "Tên File", "Ngày Tạo", "Đường Dẫn URL"])

def update_export_report_deleted_status(db_ids, is_deleted_val):
    if supabase is None:
        return
    try:
        for db_id in db_ids:
            supabase.table("export_reports").update({"is_deleted": is_deleted_val}).eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception:
        pass

def permanent_delete_export_report_db(db_ids):
    if supabase is None:
        return
    try:
        for db_id in db_ids:
            supabase.table("export_reports").delete().eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception:
        pass

# ==================== GÁN SESSION STATE TỪ DATABASE ====================
st.session_state.staff_list = get_staff_list_db()
st.session_state.rules_df = get_rules_df_db()
st.session_state.chart_colors = default_chart_colors
st.session_state.folders = load_folders_db()

db_settings = load_app_settings_db()

if "primary_color" not in st.session_state: 
    st.session_state.primary_color = db_settings.get("primary_color") or "#ff4b4b"
if "bg_color" not in st.session_state: 
    st.session_state.bg_color = db_settings.get("bg_color") or "#ffffff"
if "sidebar_bg" not in st.session_state: 
    st.session_state.sidebar_bg = db_settings.get("sidebar_bg") or "#f0f2f6"
if "sidebar_opacity" not in st.session_state: 
    st.session_state.sidebar_opacity = float(db_settings.get("sidebar_opacity") or 0.9)
if "text_color" not in st.session_state: 
    st.session_state.text_color = db_settings.get("text_color") or "#31333F"
if "bg_image_base64" not in st.session_state: 
    st.session_state.bg_image_base64 = db_settings.get("bg_image_base64")
if "avatar_base64" not in st.session_state: 
    st.session_state.avatar_base64 = db_settings.get("avatar_base64")

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
                    
                    save_app_settings_db({
                        "primary_color": st.session_state.primary_color,
                        "bg_color": st.session_state.bg_color,
                        "sidebar_bg": st.session_state.sidebar_bg,
                        "sidebar_opacity": st.session_state.sidebar_opacity,
                        "text_color": st.session_state.text_color,
                        "bg_image_base64": st.session_state.bg_image_base64,
                        "avatar_base64": st.session_state.avatar_base64
                    })
                    
                    st.success("Đã cập nhật ảnh đại diện!")
                    st.rerun()
            
        if st.session_state.avatar_base64:
            st.markdown("---")
            if st.button("🗑️ Xóa Ảnh Đại Diện", use_container_width=True, key="btn_remove_avatar_unique"):
                st.session_state.avatar_base64 = None
                st.session_state["last_processed_avatar"] = None
                
                save_app_settings_db({
                    "primary_color": st.session_state.primary_color,
                    "bg_color": st.session_state.bg_color,
                    "sidebar_bg": st.session_state.sidebar_bg,
                    "sidebar_opacity": st.session_state.sidebar_opacity,
                    "text_color": st.session_state.text_color,
                    "bg_image_base64": None,
                    "avatar_base64": st.session_state.avatar_base64
                })
                
                st.success("Đã xóa ảnh đại diện!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-scrollable-content">', unsafe_allow_html=True)
    
    st.markdown(f"<small>👤 <b>{st.session_state.user_email}</b></small>", unsafe_allow_html=True)
    if st.button("🚪 Đăng Xuất", use_container_width=True):
        if supabase is not None:
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        if "auth_user" in st.query_params:
            del st.query_params["auth_user"]
        st.rerun()

    st.markdown("---")
    if st.button("🔄 Cập Nhập", use_container_width=True):
        st.cache_data.clear()
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
                if item["id"] == "menu_5": return "report_folder"
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
        checked_in_set = set(att_df_check[att_df_check["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist())

    active_staff = [s for s in st.session_state.staff_list if s in checked_in_set]

    st.subheader(f"{menu} ({today_str})")

    if not active_staff:
        st.warning(f"⚠️ Hiện tại chưa có nhân sự nào **Check-in (Vào ca)** hoặc các ca trước chưa kết thúc. Vui lòng thực hiện Check-in trước khi nhập sản lượng!")
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
                
            record_images = st.file_uploader("Tải ảnh đính kèm (Tối đa 4 ảnh)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="record_img")
                    
            f_col4, f_col5 = st.columns(2)
            with f_col4:
                so_luong = st.number_input("Số lượng thực tế", min_value=0, value=0, step=1)
            with f_col5:
                ghi_chu = st.text_input("Ghi chú", "")
                
            submitted = st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True)

            if submitted:
                is_valid = True
                if req_img and not record_images: is_valid = False
                if req_qty and so_luong <= 0: is_valid = False
                if record_images and len(record_images) > 4:
                    is_valid = False
                    st.session_state["form_msg"] = ("error", "⚠️ Bạn chỉ được phép đính kèm tối đa 4 ảnh!")

                if not is_valid and "form_msg" not in st.session_state:
                    st.session_state["form_msg"] = ("error", "⚠️ Vui lòng điền đủ ảnh đính kèm và số lượng > 0 theo cấu hình!")

                if is_valid:
                    row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
                    he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
                    don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
                    tong_diem = so_luong * he_so
                    
                    img_urls = upload_multiple_images_to_storage(record_images) if record_images else ""
                    current_time_str = datetime.datetime.now(VN_TIMEZONE).strftime("%H:%M:%S")
                    
                    add_production_log_db(today_str, current_time_str, nhan_su, hang_muc, img_urls, don_vi, so_luong, he_so, tong_diem, ghi_chu)
                    st.session_state["form_msg"] = ("success", f"✅ Ghi nhận thành công cho **{nhan_su}**! Tổng điểm: **{tong_diem} điểm**")
                    st.rerun()

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
        s_col1, s_col2, s_col3, s_col4 = st.columns(4)
        with s_col1:
            all_dates = ["Tất cả"] + sorted(input_df["Ngày"].unique().tolist())
            default_index = all_dates.index(today_str) if today_str in all_dates else 0
            filter_date = st.selectbox("Lọc theo Ngày", all_dates, index=default_index)
        with s_col2:
            enable_hour_filter = st.checkbox("Lọc theo Khoảng Giờ", value=False)
            if enable_hour_filter:
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    start_t = st.time_input("Từ giờ", datetime.time(7, 30), label_visibility="collapsed")
                with t_col2:
                    end_t = st.time_input("Đến giờ", datetime.time(17, 0), label_visibility="collapsed")
            else:
                start_t, end_t = None, None
        with s_col3:
            all_staff = ["Tất cả"] + sorted(input_df["Nhân Sự"].unique().tolist())
            filter_staff = st.selectbox("Lọc theo Nhân Sự", all_staff)
            
        temp_filtered_df = input_df.copy()
        if filter_date != "Tất cả": 
            temp_filtered_df = temp_filtered_df[temp_filtered_df["Ngày"] == filter_date]
        if filter_staff != "Tất cả": 
            temp_filtered_df = temp_filtered_df[temp_filtered_df["Nhân Sự"] == filter_staff]

        with s_col4:
            available_tasks = ["Tất cả"] + sorted(temp_filtered_df["Hạng Mục Công Việc"].unique().tolist())
            filter_task = st.selectbox("Lọc theo Hạng Mục", available_tasks)
        
        filtered_df = temp_filtered_df.copy()
        
        if enable_hour_filter and start_t and end_t:
            def check_time_in_range(t_str):
                try:
                    t_val = datetime.datetime.strptime(str(t_str).strip(), "%H:%M:%S").time()
                    return start_t <= t_val <= end_t
                except:
                    return True
            filtered_df = filtered_df[filtered_df["Thời Gian"].apply(check_time_in_range)]
            
        if filter_task != "Tất cả": 
            filtered_df = filtered_df[filtered_df["Hạng Mục Công Việc"] == filter_task]
            
        # ==================== Ô HIỂN THỊ TỔNG SỐ LƯỢNG DỰA THEO HẠNG MỤC ====================
        if filter_task != "Tất cả":
            total_qty_task = filtered_df["Số Lượng"].sum() if not filtered_df.empty else 0
            unit_name = filtered_df["Đơn Vị"].values[0] if not filtered_df.empty and "Đơn Vị" in filtered_df.columns else "Cái"
            st.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.15); padding: 12px 18px; border-radius: 8px; border: 2px solid #3b82f6; margin-bottom: 15px; font-size: 1rem; font-weight: bold; text-align: center;">
                📊 Tổng số lượng của hạng mục <span style="color: #ff4b4b;">"{filter_task}"</span>: <span style="font-size: 1.2rem; color: #1d4ed8;">{total_qty_task:,.0f}</span> {unit_name}
            </div>
            """, unsafe_allow_html=True)

        if not filtered_df.empty:
            col_del_all_1, col_del_all_2 = st.columns([2.5, 1.5])
            with col_del_all_2:
                del_c1, del_c2 = st.columns([1, 1])
                with del_c1:
                    confirm_delete_all = st.checkbox("Xác nhận xóa tất cả", key="chk_confirm_delete_all")
                with del_c2:
                    if st.button("🗑️ Xóa tất cả", use_container_width=True, type="primary"):
                        if confirm_delete_all:
                            all_filtered_ids = filtered_df["db_id"].tolist()
                            if all_filtered_ids:
                                update_production_log_deleted_status(all_filtered_ids, True)
                                st.success("Đã chuyển toàn bộ bản ghi đang hiển thị vào thùng rác!")
                                st.rerun()
                        else:
                            st.warning("⚠️ Vui lòng tích chọn 'Xác nhận xóa tất cả' trước khi bấm!")

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
                        if isinstance(img_url_val, dict):
                            img_url_val = img_url_val.get("publicUrl") or img_url_val.get("url", "")
                        
                        if img_url_val and isinstance(img_url_val, str):
                            urls = [u.strip() for u in img_url_val.split(",") if u.strip()]
                            if urls:
                                sub_cols = st.columns(min(len(urls), 4), gap="small")
                                for i, u in enumerate(urls):
                                    with sub_cols[i]:
                                        with st.popover("🔍", help="Xem ảnh lớn"):
                                            st.image(u, use_container_width=True)
                                        st.image(u, width=40)
                        else:
                            st.markdown("<small style='color: gray;'>Không ảnh</small>", unsafe_allow_html=True)
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
    checked_in_set = set(att_df[att_df["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist()) if not att_df.empty else set()

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
                st.session_state["att_msg"] = ("warning", f"⚠️ Nhân sự {att_staff} đang trong ca làm việc, không thể Check-in thêm!")
            else:
                add_attendance_db(att_date, att_staff, time_str, "Chưa kết thúc", 0, att_note)
                st.session_state["att_msg"] = ("success", f"✅ Check-in thành công cho **{att_staff}** lúc **{time_str}**!")
                st.rerun()
        if check_out:
            res_check = supabase.table("attendance").select("*").eq("nhan_su", att_staff).eq("gio_ra_ca", "Chưa kết thúc").execute() if supabase else None
            
            if res_check and res_check.data:
                target_row = res_check.data[0]
                row_id = target_row["id"]
                ngay_vao = target_row["ngay"]
                gio_vao_ca = target_row.get("gio_vao_ca", "00:00:00")
                
                so_phut_thuc_te = calculate_exact_minutes(ngay_vao, gio_vao_ca, str(att_date), time_str)
                
                old_note = target_row.get("ghi_chu", "")
                final_note = f"{old_note} | {att_note}" if old_note and att_note else (old_note or att_note)
                
                supabase.table("attendance").update({
                    "gio_ra_ca": time_str,
                    "so_phut_lam_viec": int(so_phut_thuc_te),
                    "ghi_chu": final_note
                }).eq("id", row_id).execute()
                
                st.cache_data.clear()
                st.session_state["att_msg"] = ("success", f"✅ Check-out thành công cho **{att_staff}** lúc **{time_str}** (Tổng thời gian: **{so_phut_thuc_te} phút**)!")
            else:
                st.session_state["att_msg"] = ("warning", f"⚠️ Không tìm thấy mốc Vào ca nào đang mở (Chưa kết thúc) cho **{att_staff}**!")
            st.rerun()

    if "att_msg" in st.session_state:
        m_type, m_text = st.session_state["att_msg"]
        if m_type == "success": st.success(m_text)
        else: st.warning(m_text)
        del st.session_state["att_msg"]

    st.markdown("---")
    st.subheader("📋 Lịch Sử Chấm Công")
    if not att_df.empty:
        st.dataframe(att_df.drop(columns=["db_id"]), use_container_width=True, hide_index=True)
        
        with st.form("delete_att_form"):
            st.markdown("##### 🗑️ Xóa Bản Ghi Chấm Công Lỗi")
            att_ids_to_del = []
            for idx, r in att_df.iterrows():
                if st.checkbox(f"Xóa dòng STT {r['STT']} - {r['Nhân Sự']} ({r['Ngày']} | {r['Giờ Vào Ca']} -> {r['Giờ Ra Ca']})", key=f"del_att_{r['db_id']}"):
                    att_ids_to_del.append(r['db_id'])
            if st.form_submit_button("Xóa Các Dòng Chấm Công Đã Chọn", use_container_width=True):
                if att_ids_to_del:
                    delete_attendance_db(att_ids_to_del)
                    st.success("Đã xóa các bản ghi chấm công thành công!")
                    st.rerun()
                else:
                    st.warning("Vui lòng tích chọn dòng cần xóa!")

# ==================== BÁO CÁO & BIỂU ĐỒ ====================
elif feature == "report":
    st.header(menu)
    
    all_staff_current = st.session_state.staff_list
    
    input_df = get_production_logs_db(is_deleted=False, limit_rows=1000)
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
            
            comparison_df["Số_Ngày_Làm_Việc"] = comparison_df["Tổng Phút Làm Việc"] / 480.0
            
            comparison_table = comparison_df[["Xếp Hạng", "Nhân Sự", "Tổng Phút Làm Việc", "Số_Ngày_Làm_Việc", "Tỷ_Lệ_Thời_Gian", "Tổng_Điểm", "Tỷ_Lệ_Đóng_Góp", "Chênh_Lệch_%"]].copy()
            comparison_table.columns = ["Xếp Hạng", "Nhân Sự", "Tổng Thời Gian (Phút)", "Số ngày làm việc", "Tỷ Lệ Thời Gian (%)", "Tổng Điểm", "Tỷ Lệ Sản Lượng (%)", "Chênh Lệch (Sản Lượng - Thời Gian)"]
            
            st.dataframe(
                comparison_table.style.format({
                    "Tổng Thời Gian (Phút)": "{:,.0f}",
                    "Số ngày làm việc": "{:,.2f}",
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

    st.markdown("---")
    
    if not summary.empty and total_all_points > 0:
        export_csv_df = summary_display.copy()
        if not input_df.empty:
            task_details = []
            for staff_name in export_csv_df["Nhân Sự"]:
                staff_logs = input_df[input_df["Nhân Sự"] == staff_name]
                if not staff_logs.empty:
                    grouped_tasks = staff_logs.groupby("Hạng Mục Công Việc")["Số Lượng"].sum()
                    task_str_list = [f"{task}: {qty}" for task, qty in grouped_tasks.items()]
                    task_details.append(" | ".join(task_str_list))
                else:
                    task_details.append("")
            export_csv_df["Chi Tiết Hạng Mục Công Việc"] = task_details
        else:
            export_csv_df["Chi Tiết Hạng Mục Công Việc"] = ""

        exp_col1, exp_col2 = st.columns([1, 3])
        with exp_col1:
            csv_str = export_csv_df.to_csv(index=False)
            csv_bytes = csv_str.encode('utf-8-sig')
            file_name_val = f"bao_cao_san_luong_{datetime.date.today()}.csv"
            
            if st.button("📥 Xuất File & Lưu Vào Thư Mục", use_container_width=True):
                file_url = upload_report_to_storage(file_name_val, csv_bytes)
                if file_url:
                    save_export_report_db(file_name_val, file_url)
                else:
                    st.error("Lỗi khi tải file lên Storage. Vui lòng kiểm tra lại bucket 'reports-storage'!")

            st.download_button(
                label="💾 Tải File Về Máy",
                data=csv_bytes,
                file_name=file_name_val,
                mime="text/csv",
                use_container_width=True
            )

        chart_col1, chart_col2 = st.columns([0.45, 1.35])
        
        with chart_col1:
            fig_plotly = px.pie(
                summary, 
                names="Nhân Sự", 
                values="Tổng_Điểm", 
                hole=0,
                color_discrete_sequence=default_chart_colors
            )
            fig_plotly.update_traces(
                textposition='inside', 
                textinfo='percent',
                textfont=dict(size=20, color='white', family='Arial Black'),
                pull=[0.03] * len(summary)
            )
            fig_plotly.update_layout(
                margin=dict(t=30, b=30, l=30, r=30),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                height=320
            )
            st.plotly_chart(fig_plotly, use_container_width=True)
            
        with chart_col2:
            st.markdown("### 📌 Chi Tiết Điểm Số & Tỷ Lệ")
            for idx, row in summary.iterrows():
                staff_name = row["Nhân Sự"]
                short_name = staff_name.split()[-1] if len(staff_name.split()) > 1 else staff_name
                pts = row["Tổng_Điểm"]
                pct = row["Tỷ_Lệ_Đóng_Góp"] * 100
                color_code = default_chart_colors[idx % len(default_chart_colors)]
                
                st.markdown(f"""
                <div style="background-color: #f8fafc; padding: 6px 10px; border-radius: 6px; margin-bottom: 6px; border-left: 4px solid {color_code}; border: 1px solid #e2e8f0; font-size: 0.85rem;">
                    <span style="display:inline-block; width:7px; height:7px; background-color:{color_code}; border-radius:2px; margin-right:4px;"></span>
                    <b>{short_name}</b>: {pts:,.1f} điểm (<b style="color: {color_code};">{pct:.1f}%</b>)
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Chưa đủ dữ liệu để vẽ biểu đồ.")

# ==================== 5. THƯ MỤC BÁO CÁO ====================
elif feature == "report_folder":
    st.header(menu)
    st.markdown("📂 Kho lưu trữ các file báo cáo trên Cloud Storage. Bạn có thể tải lại file trực tiếp từ đường dẫn, chuyển vào thùng rác hoặc xóa vĩnh viễn.")
    
    reports_df = get_export_reports_db(is_deleted=False)
    if not reports_df.empty:
        col_del_all_1, col_del_all_2 = st.columns([3, 1])
        with col_del_all_2:
            if st.button("🗑️ Chuyển Tất Cả Vào Thùng Rác", use_container_width=True, type="primary"):
                all_ids = reports_df["db_id"].tolist()
                if all_ids:
                    update_export_report_deleted_status(all_ids, True)
                    st.success("Đã chuyển toàn bộ báo cáo vào thùng rác!")
                    st.rerun()

        with st.form("reports_folder_form"):
            for idx, row in reports_df.iterrows():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;">
                    <b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📁 Tên File: <b>{row['Tên File']}</b> &nbsp;|&nbsp; 📅 Ngày tạo: {row['Ngày Tạo']}<br>
                    🔗 <a href="{row['Đường Dẫn URL']}" target="_blank">Mở liên kết trực tiếp trên Storage</a>
                </div>
                """, unsafe_allow_html=True)
                is_sel = st.checkbox(f"Chọn báo cáo STT {row['STT']} ({row['Tên File']})", key=f"rep_{row['db_id']}")
                reports_df.loc[idx, "Chọn"] = is_sel
                st.markdown("---")
            
            if st.form_submit_button("🗑️ Chuyển Các Báo Cáo Đã Chọn Vào Thùng Rác", use_container_width=True):
                selected_ids = reports_df[reports_df["Chọn"] == True]["db_id"].tolist()
                if selected_ids:
                    update_export_report_deleted_status(selected_ids, True)
                    st.success("Đã chuyển các báo cáo đã chọn vào thùng rác!")
                    st.rerun()
                else:
                    st.warning("Vui lòng tích chọn báo cáo cần chuyển!")
                    
        st.markdown("### 📥 Tải Nhanh Các Báo Cáo Đã Lưu")
        for _, row in reports_df.iterrows():
            st.markdown(f"📥 [{row['Tên File']} - Tạo ngày {row['Ngày Tạo']}]({row['Đường Dẫn URL']})")
    else:
        st.info("Thư mục báo cáo đang trống. Hãy vào mục '2. Báo Cáo & Biểu Đồ' để xuất và lưu báo cáo mới.")

# ==================== THAM CHIẾU CÔNG VIỆC ====================
elif feature == "rules":
    st.header(menu)
    with st.form("rules_form"):
        edited_rules = st.data_editor(st.session_state.rules_df, num_rows="dynamic", use_container_width=True, hide_index=True, disabled=["stt"])
        if st.form_submit_button("💾 Lưu Thay Đổi Định Mức", use_container_width=True):
            save_rules_df_db(edited_rules)
            st.success("Đã lưu định mức thành công!")
            st.rerun()

# ==================== THÙNG RÁC SẢN LƯỢNG ====================
elif feature == "trash":
    st.header(menu)
    trash_df = get_production_logs_db(is_deleted=True, limit_rows=100)
    trash_reports_df = get_export_reports_db(is_deleted=True)
    
    st.subheader("🗑️ Thùng Rác: Bản Ghi Sản Lượng")
    if not trash_df.empty:
        with st.container():
            col_t_all_1, col_t_all_2 = st.columns(2)
            with col_t_all_1:
                confirm_restore_all = st.checkbox("Xác nhận khôi phục tất cả", key="chk_confirm_restore_all")
                if st.button("📥 Khôi phục tất cả", use_container_width=True):
                    if confirm_restore_all:
                        all_trash_ids = trash_df["db_id"].tolist()
                        if all_trash_ids:
                            update_production_log_deleted_status(all_trash_ids, False)
                            st.success("Đã khôi phục toàn bộ bản ghi thành công!")
                            st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng tích chọn 'Xác nhận khôi phục tất cả' trước khi bấm!")
            with col_t_all_2:
                confirm_perm_del_all = st.checkbox("Xác nhận xóa vĩnh viễn tất cả", key="chk_confirm_perm_del_all")
                if st.button("🔥 Xóa vĩnh viễn tất cả", use_container_width=True, type="primary"):
                    if confirm_perm_del_all:
                        all_trash_ids = trash_df["db_id"].tolist()
                        if all_trash_ids:
                            permanent_delete_db(all_trash_ids)
                            st.success("Đã xóa vĩnh viễn toàn bộ bản ghi trong thùng rác!")
                            st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng tích chọn 'Xác nhận xóa vĩnh viễn tất cả' trước khi bấm!")

        st.markdown("---")
        with st.form("trash_form"):
            for idx, row in trash_df.iterrows():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;">
                    <b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} &nbsp;|&nbsp; 👤 <b>{row['Nhân Sự']}</b> &nbsp;|&nbsp; 📌 {row['Hạng Mục Công Việc']} ({row['Số Lượng']} {row['Đơn Vị']})
                </div>
                """, unsafe_allow_html=True)
                is_sel = st.checkbox(f"Chọn sản lượng STT {row['STT']}", key=f"t_{row['db_id']}")
                trash_df.loc[idx, "Chọn"] = is_sel
                
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📥 Khôi Phục Sản Lượng Đã Chọn", use_container_width=True):
                    ids = trash_df[trash_df["Chọn"] == True]["db_id"].tolist()
                    if ids:
                        update_production_log_deleted_status(ids, False)
                        st.success("Đã khôi phục thành công!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn dòng cần khôi phục!")
            with c2:
                if st.form_submit_button("🔥 Xóa Vĩnh Viễn Sản Lượng Đã Chọn", use_container_width=True):
                    ids = trash_df[trash_df["Chọn"] == True]["db_id"].tolist()
                    if ids:
                        permanent_delete_db(ids)
                        st.success("Đã xóa vĩnh viễn!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn dòng cần xóa vĩnh viễn!")
    else:
        st.info("Thùng rác sản lượng trống.")

    st.markdown("---")
    st.subheader("🗑️ Thùng Rác: Báo Cáo Đã Xóa")
    if not trash_reports_df.empty:
        with st.form("trash_reports_form"):
            for idx, row in trash_reports_df.iterrows():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;">
                    📁 File: <b>{row['Tên File']}</b> &nbsp;|&nbsp; Ngày tạo: {row['Ngày Tạo']}
                </div>
                """, unsafe_allow_html=True)
                is_sel_rep = st.checkbox(f"Chọn báo cáo {row['Tên File']}", key=f"tr_rep_{row['db_id']}")
                trash_reports_df.loc[idx, "Chọn"] = is_sel_rep
                
            rc1, rc2 = st.columns(2)
            with rc1:
                if st.form_submit_button("📥 Khôi Phục Báo Cáo Đã Chọn", use_container_width=True):
                    rep_ids = trash_reports_df[trash_reports_df["Chọn"] == True]["db_id"].tolist()
                    if rep_ids:
                        update_export_report_deleted_status(rep_ids, False)
                        st.success("Đã khôi phục báo cáo thành công!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn báo cáo cần khôi phục!")
            with rc2:
                if st.form_submit_button("🔥 Xóa Vĩnh Viễn Báo Cáo Đã Chọn", use_container_width=True):
                    rep_ids = trash_reports_df[trash_reports_df["Chọn"] == True]["db_id"].tolist()
                    if rep_ids:
                        permanent_delete_export_report_db(rep_ids)
                        st.success("Đã xóa vĩnh viễn báo cáo!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn báo cáo cần xóa vĩnh viễn!")
    else:
        st.info("Thùng rác báo cáo trống.")

# ==================== QUẢN LÝ THƯ MỤC & MENU ====================
elif feature == "manage_folders":
    st.header("Quản Lý Thư Mục & Menu")
    
    with st.form("manage_menu_form"):
        st.markdown("##### Tên thư mục")
        current_folder_name = st.session_state.folders[0]["folder_name"] if st.session_state.folders else "📌 Quản Lý Nghiệp Vụ"
        new_folder_name = st.text_input("Tên thư mục", value=current_folder_name, label_visibility="collapsed")
        
        st.markdown("##### Danh sách mục menu bên trong:")
        
        current_items = st.session_state.folders[0]["items"] if st.session_state.folders else []
        updated_items = []
        for i_idx, item in enumerate(current_items):
            item_name = item.get("name", "")
            item_id = item.get("id", f"menu_{i_idx+1}")
            new_name = st.text_input(f"Tên hiển thị {i_idx+1}", value=item_name, key=f"edit_name_{i_idx}")
            updated_items.append({"id": item_id, "name": new_name})
            
        submitted_menu = st.form_submit_button("💾 Lưu Thay Đổi", use_container_width=True)
        if submitted_menu:
            new_folders_structure = [
                {
                    "folder_name": new_folder_name,
                    "items": updated_items
                }
            ]
            st.session_state.folders = new_folders_structure
            save_folders_db(new_folders_structure)
            st.success("Đã lưu tên thư mục và menu xuống Cloud thành công!")
            st.rerun()

# ==================== CÀI ĐẶT GIAO DIỆN ====================
elif feature == "settings_ui":
    st.header("Cài Đặt Giao Diện & Nhân Sự")
    
    st.markdown("### 🎨 Tùy Chỉnh Giao Diện Ứng Dụng")
    with st.form("ui_settings_form"):
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            picker_bg = st.color_picker("Màu nền ứng dụng", value=st.session_state.bg_color)
            picker_text = st.color_picker("Màu chữ / văn bản", value=st.session_state.text_color)
        with c_col2:
            picker_primary = st.color_picker("Màu chủ đạo (Tiêu đề, điểm nhấn)", value=st.session_state.primary_color)
            picker_sidebar = st.color_picker("Màu nền thanh bên (Sidebar)", value=st.session_state.sidebar_bg)
            
        st.markdown("---")
        slider_opacity = st.slider("Độ mờ / trong suốt thanh bên (Sidebar Opacity)", min_value=0.1, max_value=1.0, value=float(st.session_state.sidebar_opacity), step=0.05)
        
        st.markdown("---")
        bg_file_upload = st.file_uploader("🖼️ Tải lên hình nền ứng dụng (Tuỳ chọn)", type=["png", "jpg", "jpeg"])
        
        submitted_ui = st.form_submit_button("💾 Lưu Cài Đặt Giao Diện", use_container_width=True)
        if submitted_ui:
            st.session_state.bg_color = picker_bg
            st.session_state.text_color = picker_text
            st.session_state.primary_color = picker_primary
            st.session_state.sidebar_bg = picker_sidebar
            st.session_state.sidebar_opacity = slider_opacity
            
            if bg_file_upload is not None:
                compressed_bg = compress_image_to_base64(bg_file_upload, max_size=(1920, 1080), quality=80)
                if compressed_bg:
                    st.session_state.bg_image_base64 = compressed_bg
            
            save_app_settings_db({
                "primary_color": st.session_state.primary_color,
                "bg_color": st.session_state.bg_color,
                "sidebar_bg": st.session_state.sidebar_bg,
                "sidebar_opacity": st.session_state.sidebar_opacity,
                "text_color": st.session_state.text_color,
                "bg_image_base64": st.session_state.bg_image_base64,
                "avatar_base64": st.session_state.avatar_base64
            })
            
            st.success("Đã lưu cài đặt giao diện thành công xuống Database!")
            st.rerun()
            
        if st.session_state.bg_image_base64:
            if st.form_submit_button("🗑️ Xóa Hình Nền Hiện Tại", use_container_width=True):
                st.session_state.bg_image_base64 = None
                
                save_app_settings_db({
                    "primary_color": st.session_state.primary_color,
                    "bg_color": st.session_state.bg_color,
                    "sidebar_bg": st.session_state.sidebar_bg,
                    "sidebar_opacity": st.session_state.sidebar_opacity,
                    "text_color": st.session_state.text_color,
                    "bg_image_base64": None,
                    "avatar_base64": st.session_state.avatar_base64
                })
                
                st.success("Đã xóa hình nền!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 👥 Quản Lý Danh Sách Nhân Sự")
    st.warning("⚠️ **Lưu ý quan trọng:** Khi bạn xóa nhân sự khỏi danh sách và bấm nút lưu, hệ thống sẽ **xóa vĩnh viễn** nhân sự đó cùng **toàn bộ dữ liệu sản lượng và chấm công** gắn liền với tên họ.")
    
    with st.form("staff_form"):
        staff_df = get_staff_df_db()
        edited_staff = st.data_editor(staff_df, num_rows="dynamic", use_container_width=True, hide_index=True, disabled=["id"])
        
        if st.form_submit_button("💾 Lưu Danh Sách Nhân Sự", use_container_width=True):
            save_staff_list_db(edited_staff)
            st.session_state.staff_list = get_staff_list_db()
            st.success("Đã cập nhật, xóa vĩnh viễn nhân sự và các dữ liệu liên quan thành công!")
            st.rerun()

# ==================== LÀM SẠCH DỮ LIỆU ====================
elif feature == "clean_data":
    st.header("Làm Sạch Dữ Liệu")
    if st.button("🔥 Xóa Toàn Bộ Dữ Liệu Thùng Rác Vĩnh Viễn", use_container_width=True):
        trash_df = get_production_logs_db(is_deleted=True, limit_rows=500)
        if not trash_df.empty:
            permanent_delete_db(trash_df["db_id"].tolist())
            st.success("Đã làm sạch thùng rác!")
            st.rerun()
