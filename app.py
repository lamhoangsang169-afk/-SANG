import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import base64
import hashlib
import os
from io import BytesIO
from PIL import Image
import pytz
from supabase import create_client, Client

# ==================== KẾT NỐI DATABASE & CẤU HÌNH BAN ĐẦU ====================
VN_TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")

st.set_page_config(page_title="POSS - Quản Lý Sản Xuất", page_icon="📊", layout="wide")

def init_supabase():
    try:
        url = st.secrets["supabase"]["SUPABASE_URL"]
        key = st.secrets["supabase"]["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()
is_supabase_connected = supabase is not None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def hex_to_rgba(hex_code, opacity=0.9):
    hex_code = hex_code.lstrip('#')
    if len(hex_code) == 6:
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"
    return f"rgba(240, 242, 246, {opacity})"

def compress_image_to_base64(uploaded_file, max_size=(300, 300), quality=60):
    try:
        image = Image.open(uploaded_file)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.thumbnail(max_size)
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=quality)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{img_str}"
    except Exception:
        return None

def calculate_exact_minutes(ngay_vao, gio_vao, ngay_ra, gio_ra):
    try:
        dt_in = datetime.datetime.strptime(f"{ngay_vao} {gio_vao}", "%Y-%m-%d %H:%M:%S")
        dt_out = datetime.datetime.strptime(f"{ngay_ra} {gio_ra}", "%Y-%m-%d %H:%M:%S")
        diff = dt_out - dt_in
        return max(0, int(diff.total_seconds() // 60))
    except Exception:
        return 0

def get_app_memory_usage():
    try:
        import sys, psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 ** 2)
        return f"{mem_mb:.1f} MB"
    except Exception:
        return "Ổn định"

def get_detailed_storage_usage():
    if supabase is None:
        return "0 MB / 500 MB", "0 MB / 1 GB"
    try:
        logs_count = len(supabase.table("production_logs").select("id", count="exact").execute().data)
        att_count = len(supabase.table("attendance").select("id", count="exact").execute().data)
        users_count = len(supabase.table("user_accounts").select("id", count="exact").execute().data)
        
        estimated_db_kb = (logs_count + att_count + users_count) * 2.5
        db_used_str = f"{estimated_db_kb / 1024:.2f} MB" if estimated_db_kb > 1024 else f"{estimated_db_kb:.1f} KB"
        db_display = f"{db_used_str} / 500 MB"

        storage_bytes = 0
        try:
            files_img = supabase.storage.from_("production-images").list()
            files_rep = supabase.storage.from_("reports-storage").list()
            total_files = (files_img if files_img else []) + (files_rep if files_rep else [])
            for f in total_files:
                storage_bytes += f.get("metadata", {}).get("size", 0)
        except Exception:
            pass

        storage_mb = storage_bytes / (1024 * 1024)
        storage_display = f"{storage_mb / 1024:.2f} GB / 1 GB" if storage_mb >= 1024 else f"{storage_mb:.2f} MB / 1 GB"
        return db_display, storage_display
    except Exception:
        return "0 MB / 500 MB", "0 MB / 1 GB"

# ==================== CÁC HÀM TRUY XUẤT DATABASE ====================
@st.cache_data(ttl=600, show_spinner=False)
def get_staff_df_db():
    if supabase is None: return pd.DataFrame(columns=["id", "name"])
    try:
        res = supabase.table("staff").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            if "name" not in df.columns and "ten" in df.columns:
                df = df.rename(columns={"ten": "name"})
            return df
    except Exception: pass
    return pd.DataFrame(columns=["id", "name"])

def get_staff_list_db():
    df = get_staff_df_db()
    if not df.empty and "name" in df.columns:
        return df["name"].dropna().tolist()
    return []

@st.cache_data(ttl=600, show_spinner=False)
def get_rules_df_db():
    if supabase is None: return pd.DataFrame(columns=["id", "stt", "Hạng Mục Công Việc", "Đơn Vị", "Hệ Số Điểm", "Ghi Chú"])
    try:
        res = supabase.table("rules").select("*").order("stt", desc=False).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            rename_map = {}
            if "hang_muc" in df.columns: rename_map["hang_muc"] = "Hạng Mục Công Việc"
            if "don_vi" in df.columns: rename_map["don_vi"] = "Đơn Vị"
            if "he_so_diem" in df.columns: rename_map["he_so_diem"] = "Hệ Số Điểm"
            if "ghi_chu" in df.columns: rename_map["ghi_chu"] = "Ghi Chú"
            return df.rename(columns=rename_map)
    except Exception: pass
    return pd.DataFrame(columns=["id", "stt", "Hạng Mục Công Việc", "Đơn Vị", "Hệ Số Điểm", "Ghi Chú"])

@st.cache_data(ttl=60, show_spinner=False)
def get_production_logs_db(is_deleted=False, limit_rows=300):
    if supabase is None: return pd.DataFrame()
    try:
        res = supabase.table("production_logs").select("*").eq("is_deleted", is_deleted).order("id", desc=True).limit(limit_rows).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id", "ngay": "Ngày", "thoi_gian": "Thời Gian",
                "nhan_su": "Nhân Sự", "hang_muc_cong_viec": "Hạng Mục Công Việc",
                "hinh_anh_url": "Hình Ảnh", "don_vi": "Đơn Vị", "so_luong": "Số Lượng",
                "he_so_diem": "Hệ Số", "tong_diem": "Tổng Điểm", "ghi_chu": "Ghi Chú"
            })
            if "Hình Ảnh" in df.columns:
                df["Hình Ảnh"] = df["Hình Ảnh"].fillna("").astype(str)
                df["Hình Ảnh"] = df["Hình Ảnh"].apply(lambda x: "" if x.strip() in ["0", "nan", "None", "null"] else x)
            else:
                df["Hình Ảnh"] = ""
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception: pass
    return pd.DataFrame()

def get_production_logs_by_date_range(start_date, end_date):
    if supabase is None: return pd.DataFrame()
    try:
        res = supabase.table("production_logs").select("*").eq("is_deleted", False).gte("ngay", str(start_date)).lte("ngay", str(end_date)).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id", "ngay": "Ngày", "thoi_gian": "Thời Gian",
                "nhan_su": "Nhân Sự", "hang_muc_cong_viec": "Hạng Mục Công Việc",
                "hinh_anh_url": "Hình Ảnh", "don_vi": "Đơn Vị", "so_luong": "Số Lượng",
                "he_so_diem": "Hệ Số Điểm", "tong_diem": "Tổng Điểm", "ghi_chu": "Ghi Chú"
            })
            if "Hình Ảnh" in df.columns:
                df["Hình Ảnh"] = df["Hình Ảnh"].fillna("").astype(str)
                df["Hình Ảnh"] = df["Hình Ảnh"].apply(lambda x: "" if x.strip() in ["0", "nan", "None", "null"] else x)
            else:
                df["Hình Ảnh"] = ""
            return df
    except Exception: pass
    return pd.DataFrame()

def get_total_production_count_db():
    if supabase is None: return 0
    try:
        res = supabase.table("production_logs").select("id", count="exact").eq("is_deleted", False).execute()
        return res.count if res and res.count is not None else 0
    except Exception: return 0

@st.cache_data(ttl=600, show_spinner=False)
def get_attendance_db():
    if supabase is None: return pd.DataFrame()
    try:
        res = supabase.table("attendance").select("*").order("id", desc=True).limit(100).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id", "ngay": "Ngày", "nhan_su": "Nhân Sự",
                "gio_vao_ca": "Giờ Vào Ca", "gio_ra_ca": "Giờ Ra Ca",
                "so_phut_lam_viec": "Số Phút Làm Việc", "ghi_chu": "Ghi Chú"
            })
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception: pass
    return pd.DataFrame()

def load_app_settings_db():
    if supabase is None: return {}
    try:
        res = supabase.table("app_settings").select("*").eq("id", 1).execute()
        if res.data and len(res.data) > 0: return res.data[0]
    except Exception: pass
    return {}

def load_folders_db():
    default_folders = [{
        "folder_name": "📌 Quản Lý Nghiệp Vụ",
        "items": [
            {"id": "menu_1", "name": "1. Nhập Sản Lượng"},
            {"id": "menu_2", "name": "2. Báo Cáo Thống Kê"},
            {"id": "menu_3", "name": "3. Tham Chiếu Định Mức"},
            {"id": "menu_4", "name": "4. Thùng Rác Sản Lượng"},
            {"id": "menu_5", "name": "5. Thư Mục Báo Cáo"}
        ]
    }]
    if supabase is None: return default_folders
    try:
        res = supabase.table("app_folders").select("folders_json").eq("id", 1).execute()
        if res.data and len(res.data) > 0 and res.data[0].get("folders_json"):
            return res.data[0]["folders_json"]
    except Exception: pass
    return default_folders

def save_rules_df_db(df):
    if supabase is None: return
    try:
        res_old = supabase.table("rules").select("id, hang_muc, he_so_diem").execute()
        old_rules = {row["id"]: row["hang_muc"] for row in res_old.data} if res_old.data else {}
        old_ids = list(old_rules.keys())
        current_ids = []
        for idx, row in df.iterrows():
            row_id = row.get("id")
            new_hm = str(row.get("Hạng Mục Công Việc", "")).strip()
            if not new_hm or new_hm.lower() in ["nan", "none"]: continue
            new_he_so = float(row.get("Hệ Số Điểm", 1.0)) if pd.notna(row.get("Hệ Số Điểm")) else 1.0
            payload = {
                "stt": int(idx + 1), "hang_muc": new_hm,
                "don_vi": str(row.get("Đơn Vị", "Cái")).strip() if pd.notna(row.get("Đơn Vị")) else "Cái",
                "he_so_diem": new_he_so,
                "ghi_chu": str(row.get("Ghi Chú", "")).strip() if pd.notna(row.get("Ghi Chú")) else ""
            }
            if pd.notna(row_id) and int(row_id) in old_ids:
                supabase.table("rules").update(payload).eq("id", int(row_id)).execute()
                current_ids.append(int(row_id))
            else:
                res_ins = supabase.table("rules").insert(payload).execute()
                if res_ins.data: current_ids.append(res_ins.data[0]["id"])
        ids_to_del = [oid for oid in old_ids if oid not in current_ids]
        for del_id in ids_to_del: supabase.table("rules").delete().eq("id", del_id).execute()
        st.cache_data.clear()
        st.success("Đã đồng bộ định mức!")
    except Exception as e: st.error(f"Lỗi lưu định mức: {e}")

def upload_multiple_images_to_storage(uploaded_files):
    if supabase is None or not uploaded_files: return ""
    url_list = []
    SUPABASE_URL_VAL = st.secrets["supabase"]["SUPABASE_URL"]
    for uploaded_file in uploaded_files[:4]:
        try:
            file_bytes = uploaded_file.getvalue()
            clean_filename = uploaded_file.name.replace(" ", "_")
            file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{clean_filename}"
            supabase.storage.from_("production-images").upload(file_name, file_bytes, {"content-type": uploaded_file.type})
            public_url = f"{SUPABASE_URL_VAL}/storage/v1/object/public/production-images/{file_name}"
            url_list.append(public_url)
        except Exception: pass
    return ",".join(url_list)

def add_production_log_db(ngay, thoi_gian, nhan_su, hang_muc, hinh_anh_url, don_vi, so_luong, he_so, tong_diem, ghi_chu):
    if supabase is None: return
    try:
        payload = {
            "ngay": str(ngay), "thoi_gian": thoi_gian, "nhan_su": nhan_su,
            "hang_muc_cong_viec": hang_muc, "hinh_anh_url": hinh_anh_url, "don_vi": don_vi,
            "so_luong": int(so_luong), "he_so_diem": float(he_so), "tong_diem": float(tong_diem),
            "ghi_chu": ghi_chu, "is_deleted": False
        }
        supabase.table("production_logs").insert(payload).execute()
        st.cache_data.clear()
    except Exception: pass

def update_production_log_deleted_status(db_ids, is_deleted_val):
    if supabase is None: return
    try:
        for db_id in db_ids:
            supabase.table("production_logs").update({"is_deleted": is_deleted_val}).eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception: pass

def permanent_delete_db(db_ids):
    if supabase is None: return
    try:
        for db_id in db_ids:
            supabase.table("production_logs").delete().eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception: pass

def add_attendance_db(ngay, nhan_su, gio_vao, gio_ra, phut, ghi_chu):
    if supabase is None: return
    try:
        payload = {
            "ngay": str(ngay), "nhan_su": nhan_su, "gio_vao_ca": gio_vao,
            "gio_ra_ca": gio_ra, "so_phut_lam_viec": int(phut), "ghi_chu": ghi_chu
        }
        supabase.table("attendance").insert(payload).execute()
        st.cache_data.clear()
    except Exception: pass

@st.cache_data(ttl=1800, show_spinner=False)
def get_export_reports_db(is_deleted=False):
    if supabase is None: return pd.DataFrame()
    try:
        res = supabase.table("export_reports").select("*").eq("is_deleted", is_deleted).order("id", desc=True).limit(50).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={"id": "db_id", "ten_file": "Tên File", "ngay_tao": "Ngày Tạo", "file_url": "Đường Dẫn URL"})
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception: pass
    return pd.DataFrame()

# ==================== KIỂM TRA ĐĂNG NHẬP SESSION ====================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_identifier" not in st.session_state: st.session_state.user_identifier = ""

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
                    clean_email = email_input.strip().lower()
                    clean_pw = password_admin.strip()
                    if clean_email == "lamhoangsang169@gmail.com" and clean_pw in ["123456", "Sang1998*"]:
                        st.session_state.logged_in = True
                        st.session_state.user_identifier = clean_email
                        if remember_admin: st.query_params["auth_user"] = clean_email
                        st.success("✅ Đăng nhập Admin thành công!")
                        st.rerun()
                    elif supabase is not None:
                        try:
                            res = supabase.auth.sign_in_with_password({"email": clean_email, "password": clean_pw})
                            if res and res.user:
                                st.session_state.logged_in = True
                                st.session_state.user_identifier = res.user.email
                                if remember_admin: st.query_params["auth_user"] = res.user.email
                                st.success("✅ Đăng nhập Admin thành công!")
                                st.rerun()
                            else: st.error("❌ Mật khẩu hoặc Email không đúng!")
                        except Exception as e: st.error(f"❌ Lỗi: {e}")
                    else: st.error("❌ Mật khẩu không đúng!")
                        
        with tab_staff:
            with st.form("login_staff_form"):
                staff_list_opt = ["--- Chọn họ và tên ---"] + get_staff_list_db()
                login_name = st.selectbox("👤 Họ và tên nhân sự", staff_list_opt)
                password_staff = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...", key="pw_staff")
                remember_staff = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_staff")
                if st.form_submit_button("🚀 Đăng Nhập Nhân Viên", use_container_width=True):
                    if login_name == "--- Chọn họ và tên ---" or not password_staff: st.error("⚠️ Vui lòng nhập đầy đủ!")
                    elif supabase is None: st.error("⚠️ Chưa kết nối CSDL!")
                    else:
                        try:
                            res = supabase.table("user_accounts").select("*").eq("name", login_name).execute()
                            if res.data and len(res.data) > 0:
                                user_record = res.data[0]
                                if user_record["password_hash"] == hash_password(password_staff):
                                    st.session_state.logged_in = True
                                    st.session_state.user_identifier = login_name
                                    if remember_staff: st.query_params["auth_user"] = login_name
                                    st.success("✅ Đăng nhập thành công!")
                                    st.rerun()
                                else: st.error("❌ Mật khẩu không chính xác!")
                            else: st.error("❌ Chưa được cấp tài khoản!")
                        except Exception as e: st.error(f"❌ Lỗi: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==================== PHÂN QUYỀN TÀI KHOẢN ====================
def get_user_permissions(identifier):
    default_perms = {"role": "Staff", "perm_input": False, "perm_report": False, "perm_attendance": True, "perm_rules": False}
    if not identifier or supabase is None: return default_perms
    if str(identifier).strip().lower() == "lamhoangsang169@gmail.com":
        return {"role": "Admin", "perm_input": True, "perm_report": True, "perm_attendance": True, "perm_rules": True}
    try:
        res = supabase.table("user_accounts").select("*").eq("name", identifier).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            return {
                "role": row.get("role", "Staff"), "perm_input": row.get("perm_input", False),
                "perm_report": row.get("perm_report", False), "perm_attendance": row.get("perm_attendance", True),
                "perm_rules": row.get("perm_rules", False)
            }
    except Exception: pass
    return default_perms

user_perms = get_user_permissions(st.session_state.user_identifier)
current_user_role = user_perms["role"]

st.session_state.staff_list = get_staff_list_db()
st.session_state.rules_df = get_rules_df_db()
st.session_state.chart_colors = ["#ff4b4b", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#14b8a6", "#f97316", "#6366f1"]
st.session_state.folders = load_folders_db()

db_settings = load_app_settings_db()
if "primary_color" not in st.session_state: st.session_state.primary_color = db_settings.get("primary_color") or "#ff4b4b"
if "bg_color" not in st.session_state: st.session_state.bg_color = db_settings.get("bg_color") or "#ffffff"
if "sidebar_bg" not in st.session_state: st.session_state.sidebar_bg = db_settings.get("sidebar_bg") or "#f0f2f6"
if "sidebar_opacity" not in st.session_state: st.session_state.sidebar_opacity = float(db_settings.get("sidebar_opacity") or 0.9)
if "text_color" not in st.session_state: st.session_state.text_color = db_settings.get("text_color") or "#31333F"
if "bg_image_base64" not in st.session_state: st.session_state.bg_image_base64 = db_settings.get("bg_image_base64")
if "avatar_base64" not in st.session_state: st.session_state.avatar_base64 = db_settings.get("avatar_base64")
if "current_menu" not in st.session_state: st.session_state.current_menu = "1. Nhập Sản Lượng"

bg_style = f"background-color: {st.session_state.bg_color};"
if st.session_state.bg_image_base64:
    bg_style = f"background-image: url(data:image/jpeg;base64,{st.session_state.bg_image_base64}); background-size: cover; background-repeat: no-repeat; background-position: center; background-attachment: fixed;"

sidebar_rgba = hex_to_rgba(st.session_state.sidebar_bg, st.session_state.sidebar_opacity)

st.markdown(f"""
<style>
    .stApp {{ {bg_style} color: {st.session_state.text_color} !important; padding-top: 1rem; }}
    p, span, label, div, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stMarkdownContainer"] * {{ color: {st.session_state.text_color} !important; }}
    h1 {{ color: {st.session_state.primary_color} !important; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_rgba} !important; backdrop-filter: blur(8px); }}
    [data-testid="stSidebar"] > div:first-child {{ display: flex; flex-direction: column; height: 100vh; overflow-y: auto !important; padding: 0px !important; }}
    .fixed-avatar-container {{ position: sticky; top: 0; z-index: 999999; background-color: {sidebar_rgba}; padding-top: 15px; padding-bottom: 15px; border-bottom: 2px solid {st.session_state.primary_color}; margin-bottom: 10px; text-align: center; flex-shrink: 0; backdrop-filter: blur(8px); }}
    .avatar-wrapper {{ position: relative; width: 140px; height: 140px; margin: 0 auto; }}
    .sidebar-scrollable-content {{ flex-grow: 1; padding-left: 1rem; padding-right: 1rem; padding-bottom: 50px; }}
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
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
        except Exception: pass

    st.markdown('<div class="avatar-wrapper">', unsafe_allow_html=True)
    if has_custom_avatar:
        encoded_img = base64.b64encode(avatar_bytes_obj).decode("utf-8")
        st.markdown(f'<div style="text-align: center;"><img src="data:image/jpeg;base64,{encoded_img}" style="width:140px; height:140px; border-radius:50%; object-fit:cover; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3);"></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="width:140px; height:140px; border-radius:50%; background:#cbd5e1; display:flex; align-items:center; justify-content:center; font-size:50px; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3); margin: 0 auto;">👤</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-scrollable-content">', unsafe_allow_html=True)
    role_badge = "👑 Quản Trị Viên (Admin)" if current_user_role == "Admin" else ("🛡️ Quản Lý" if current_user_role == "Manager" else "👤 Nhân Viên")
    st.markdown(f"<small>👤 <b>{st.session_state.user_identifier}</b><br>🛡️ Phân quyền: <span style='color: {'#ff4b4b' if current_user_role=='Admin' else '#3b82f6'}; font-weight:bold;'>{role_badge}</span></small>", unsafe_allow_html=True)
    
    if st.button("🚪 Đăng Xuất", use_container_width=True):
        if current_user_role == "Admin" and supabase is not None:
            try: supabase.auth.sign_out()
            except Exception: pass
        st.session_state.logged_in = False
        st.session_state.user_identifier = ""
        if "auth_user" in st.query_params: del st.query_params["auth_user"]
        st.rerun()

    st.markdown("---")
    if st.button("🔄 Cập Nhập", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    if user_perms["perm_attendance"] or current_user_role == "Admin":
        if st.button("⏱️ Chấm Công Ca Làm Việc", use_container_width=True):
            st.session_state.current_menu = "⏱️ Chấm Công Ca Làm Việc"
            st.rerun()

    st.markdown("---")
    st.markdown("### 📂 CHỨC NĂNG HỆ THỐNG")
    for folder in st.session_state.folders:
        filtered_items = []
        for item in folder["items"]:
            if current_user_role == "Admin": filtered_items.append(item)
            else:
                item_id = item.get("id")
                if item_id == "menu_1" and (user_perms["perm_input"] or True): filtered_items.append(item)
                elif item_id == "menu_2" and user_perms["perm_report"]: filtered_items.append(item)
                elif item_id == "menu_3" and user_perms["perm_rules"]: filtered_items.append(item)
                elif item_id == "menu_4" and current_user_role == "Admin": filtered_items.append(item)
                elif item_id == "menu_5" and user_perms["perm_report"]: filtered_items.append(item)

        if filtered_items:
            with st.expander(folder["folder_name"], expanded=True):
                for item in filtered_items:
                    if st.button(item["name"], use_container_width=True, key=f"btn_{item['id']}"):
                        st.session_state.current_menu = item["name"]
                        st.rerun()

    st.markdown("---")
    if is_supabase_connected:
        st.markdown('<div style="background: rgba(16, 185, 129, 0.15); padding: 8px 12px; border-radius: 6px; border: 1px solid #10b981; text-align: center; font-size: 0.85rem; font-weight: bold; color: #047857;">🟢 Đã kết nối Supabase</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background: rgba(239, 68, 68, 0.15); padding: 8px 12px; border-radius: 6px; border: 1px solid #ef4444; text-align: center; font-size: 0.85rem; font-weight: bold; color: #b91c1c;">🔴 Chưa kết nối Supabase</div>', unsafe_allow_html=True)

    ram_usage_str = get_app_memory_usage()
    db_usage_str, storage_usage_str = get_detailed_storage_usage()
    st.markdown(f'<small>🧠 RAM: <b>{ram_usage_str}</b> | 🗄️ CSDL: <b>{db_usage_str}</b> | 💾 Lưu trữ: <b>{storage_usage_str}</b></small>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

menu = st.session_state.current_menu

def get_feature_type(menu_name):
    if menu_name == "⏱️ Chấm Công Ca Làm Việc": return "attendance"
    for folder in st.session_state.folders:
        for item in folder["items"]:
            if item["name"] == menu_name:
                if item["id"] == "menu_1": return "input_production"
                if item["id"] == "menu_2": return "report"
                if item["id"] == "menu_3": return "rules"
                if item["id"] == "menu_4": return "trash"
                if item["id"] == "menu_5": return "report_folder"
    return "input_production"

# ==================== NỘI DUNG HIỂN THỊ CHÍNH ====================
@st.fragment
def render_main_content(current_menu_name):
    feature = get_feature_type(current_menu_name)

    # ==================== 1. NHẬP SẢN LƯỢNG (DẠNG THẺ CHUẨN MẪU) ====================
    if feature == "input_production":
        now_vn = datetime.datetime.now(VN_TIMEZONE)
        today_str = str(now_vn.date())
        st.subheader(f"{current_menu_name} ({today_str})")

        if current_user_role != "Admin" and not user_perms["perm_input"]:
            st.info("👁️ Tài khoản của bạn đang ở chế độ **Chỉ xem**.")
        else:
            att_df_check = get_attendance_db()
            checked_in_set = set(att_df_check[att_df_check["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist()) if not att_df_check.empty else set()
            active_staff = [s for s in st.session_state.staff_list if s in checked_in_set]

            if not active_staff:
                st.warning("⚠️ Hiện tại chưa có nhân sự nào **Check-in (Vào ca)**! Vui lòng thực hiện Check-in trước khi nhập sản lượng.")
            else:
                with st.expander("➕ Form Nhập Sản Lượng Mới", expanded=True):
                    with st.form("entry_form"):
                        f_col1, f_col2, f_col3 = st.columns(3)
                        with f_col1: ngay = st.date_input("Ngày làm việc", now_vn.date(), disabled=True)
                        with f_col2: nhan_su = st.selectbox("Nhân sự thực hiện", ["--- Vui lòng chọn nhân sự ---"] + active_staff)
                        with f_col3:
                            raw_tasks = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else []
                            danh_sach_hang_muc = [str(t).strip() for t in raw_tasks if pd.notna(t) and str(t).strip() and str(t).strip().lower() not in ["nan", "none"]]
                            hang_muc = st.selectbox("Hạng mục công việc", danh_sach_hang_muc)
                            
                        record_images = st.file_uploader("Tải ảnh đính kèm (Tối đa 4 ảnh)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="record_img")
                        f_col4, f_col5 = st.columns(2)
                        with f_col4: so_luong = st.number_input("Số lượng thực tế", min_value=1, value=10, step=1)
                        with f_col5: ghi_chu = st.text_input("Ghi chú", "")
                        
                        submitted = st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True)
                        if submitted:
                            if nhan_su == "--- Vui lòng chọn nhân sự ---": st.error("⚠️ Vui lòng chọn nhân sự!")
                            elif so_luong <= 0: st.error("⚠️ Số lượng phải lớn hơn 0!")
                            else:
                                row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
                                he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
                                don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
                                tong_diem = so_luong * he_so
                                img_urls = upload_multiple_images_to_storage(record_images) if record_images else ""
                                current_time_str = datetime.datetime.now(VN_TIMEZONE).strftime("%H:%M:%S")
                                
                                add_production_log_db(today_str, current_time_str, nhan_su, hang_muc, img_urls, don_vi, so_luong, he_so, tong_diem, ghi_chu)
                                st.success(f"✅ Ghi nhận thành công cho {nhan_su}!")
                                st.rerun()

        st.markdown("---")
        
        # HIỂN THỊ BẢNG DANH SÁCH VÀ NÚT XÓA DÒNG THEO MẪU CHUẨN
        input_df = get_production_logs_db(is_deleted=False, limit_rows=300)
        if not input_df.empty:
            rows_per_page = 10
            total_rows = len(input_df)
            total_pages = (total_rows - 1) // rows_per_page + 1

            p_col1, p_col2 = st.columns([3, 1])
            with p_col2:
                current_page = st.number_input(f"Trang ({total_pages} trang | {total_rows} bản ghi)", min_value=1, max_value=max(total_pages, 1), value=1, step=1)

            start_idx = (current_page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            paginated_df = input_df.iloc[start_idx:end_idx]

            with st.form("delete_production_form"):
                col_btn_1, col_btn_2 = st.columns([1, 1])
                with col_btn_1:
                    submitted_delete_selected = st.form_submit_button("🗑️ Xóa các dòng đã chọn", type="primary")
                with col_btn_2:
                    confirm_delete_all = st.checkbox("Xác nhận xóa tất cả trang này")
                    submitted_delete_all = st.form_submit_button("🗑️ Xóa tất cả trang này")

                selected_ids_to_delete = []
                for idx, row in paginated_df.iterrows():
                    row_c1, row_c2 = st.columns([4, 1])
                    with row_c1:
                        # Thẻ thông tin sản lượng màu xanh nhạt theo đúng mẫu giao diện gốc
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.85); padding: 10px 12px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 5px; font-size: 0.9rem;">
                            <b>STT: {row['STT']}</b> | 📅 <b>{row['Ngày']}</b> ⏰ <b>{row['Thời Gian']}</b> | 👤 <b style="color:#1d4ed8;">{row['Nhân Sự']}</b><br>
                            📌 <b style="color:#b91c1c;">{row['Hạng Mục Công Việc']}</b> | 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                            💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.checkbox(f"Chọn xóa bản ghi STT {row['STT']}", key=f"chk_{row['db_id']}"):
                            selected_ids_to_delete.append(row['db_id'])
                            
                    with row_c2:
                        img_url_val = str(row.get("Hình Ảnh", "")).strip()
                        # Xử lý bỏ hẳn chữ "0" hay ô vuông rỗng
                        if img_url_val and img_url_val not in ["0", "nan", "None", "null", ""]:
                            urls = [u.strip() for u in img_url_val.split(",") if u.strip().startswith("http")]
                            if urls:
                                sub_cols = st.columns(min(len(urls), 4), gap="small")
                                for i, u in enumerate(urls):
                                    with sub_cols[i]:
                                        with st.popover("🔍", help="Xem ảnh phóng to"):
                                            st.image(u, use_container_width=True)
                            else:
                                st.markdown("<small style='color: gray;'>Không ảnh</small>", unsafe_allow_html=True)
                        else:
                            st.markdown("<small style='color: gray;'>Không ảnh</small>", unsafe_allow_html=True)

                    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #e2e8f0;'>", unsafe_allow_html=True)

                if submitted_delete_selected:
                    if selected_ids_to_delete:
                        update_production_log_deleted_status(selected_ids_to_delete, True)
                        st.success("Đã chuyển các dòng chọn vào thùng rác thành công!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng tích chọn ít nhất một dòng cần xóa!")

                if submitted_delete_all:
                    if confirm_delete_all:
                        all_ids = paginated_df["db_id"].tolist()
                        if all_ids:
                            update_production_log_deleted_status(all_ids, True)
                            st.success("Đã chuyển tất cả dòng ở trang này vào thùng rác!")
                            st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng tích chọn 'Xác nhận xóa tất cả trang này'!")
        else:
            st.info("Chưa có dữ liệu sản lượng trong hệ thống.")

    # ==================== 2. CHẤM CÔNG CA LÀM VIỆC ====================
    elif feature == "attendance":
        st.header(current_menu_name)
        now_vn = datetime.datetime.now(VN_TIMEZONE)
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
            with f2: att_staff = st.selectbox("Nhân sự", ["--- Vui lòng chọn nhân sự ---"] + st.session_state.staff_list)
            with f3: att_note = st.text_input("Ghi chú ca", "")
            
            b1, b2 = st.columns(2)
            with b1: check_in = st.form_submit_button("🟢 Check-in (Vào ca)", use_container_width=True)
            with b2: check_out = st.form_submit_button("🔴 Check-out (Kết thúc)", use_container_width=True)
            
            time_str = now_vn.strftime("%H:%M:%S")
            if check_in:
                if att_staff == "--- Vui lòng chọn nhân sự ---": st.warning("⚠️ Chọn nhân sự!")
                elif att_staff in checked_in_set: st.warning("⚠️ Nhân sự đang làm việc!")
                else:
                    add_attendance_db(att_date, att_staff, time_str, "Chưa kết thúc", 0, att_note)
                    st.success(f"✅ Check-in thành công cho {att_staff}!")
                    st.rerun()
            if check_out:
                if att_staff == "--- Vui lòng chọn nhân sự ---": st.warning("⚠️ Chọn nhân sự!")
                else:
                    res_check = supabase.table("attendance").select("*").eq("nhan_su", att_staff).eq("gio_ra_ca", "Chưa kết thúc").execute() if supabase else None
                    if res_check and res_check.data:
                        target_row = res_check.data[0]
                        so_phut = calculate_exact_minutes(target_row["ngay"], target_row.get("gio_vao_ca", "00:00:00"), str(att_date), time_str)
                        supabase.table("attendance").update({"gio_ra_ca": time_str, "so_phut_lam_viec": int(so_phut)}).eq("id", target_row["id"]).execute()
                        st.cache_data.clear()
                        st.success(f"✅ Check-out thành công cho {att_staff}!")
                        st.rerun()

        st.markdown("---")
        st.subheader("📋 Lịch Sử Chấm Công")
        if not att_df.empty:
            st.dataframe(att_df.drop(columns=["db_id"]), use_container_width=True, hide_index=True)

    # ==================== 3. BÁO CÁO THỐNG KÊ ====================
    elif feature == "report":
        st.header(current_menu_name)
        col_date1, col_date2 = st.columns(2)
        with col_date1: report_start_date = st.date_input("Từ ngày", datetime.date.today().replace(day=1))
        with col_date2: report_end_date = st.date_input("Đến ngày", datetime.date.today())

        input_df = get_production_logs_by_date_range(report_start_date, report_end_date)
        summary = input_df.groupby("Nhân Sự").agg(Tổng_Số_Lượng=("Số Lượng", "sum"), Tổng_Điểm=("Tổng Điểm", "sum")).reset_index() if not input_df.empty else pd.DataFrame(columns=["Nhân Sự", "Tổng_Số_Lượng", "Tổng_Điểm"])
        
        st.subheader("Bảng Tổng Kết Theo Nhân Sự")
        if not summary.empty:
            st.dataframe(summary, use_container_width=True, hide_index=True)
            
            chart_col1, chart_col2 = st.columns([1, 1])
            with chart_col1:
                fig_plotly = px.pie(summary, names="Nhân Sự", values="Tổng_Điểm", title="Tỷ Lệ Điểm Sản Lượng")
                st.plotly_chart(fig_plotly, use_container_width=True)
            with chart_col2:
                fig_bar = px.bar(summary, x="Nhân Sự", y="Tổng_Số_Lượng", title="Tổng Số Lượng Hoàn Thành")
                st.plotly_chart(fig_bar, use_container_width=True)
        else: st.info("Chưa có dữ liệu báo cáo trong khoảng thời gian này.")

    # ==================== 4. THAM CHIẾU ĐỊNH MỨC ====================
    elif feature == "rules":
        st.header(current_menu_name)
        with st.form("rules_form"):
            edited_rules = st.data_editor(st.session_state.rules_df, num_rows="dynamic", use_container_width=True, hide_index=True)
            if st.form_submit_button("💾 Lưu Thay Đổi Định Mức", use_container_width=True):
                save_rules_df_db(edited_rules)
                st.rerun()

    # ==================== 5. THÙNG RÁC SẢN LƯỢNG ====================
    elif feature == "trash":
        st.header(current_menu_name)
        trash_df = get_production_logs_db(is_deleted=True, limit_rows=100)
        if not trash_df.empty:
            st.dataframe(trash_df, use_container_width=True, hide_index=True)
        else: st.info("Thùng rác trống.")

    # ==================== 6. THƯ MỤC BÁO CÁO ====================
    elif feature == "report_folder":
        st.header(current_menu_name)
        reports_df = get_export_reports_db(is_deleted=False)
        if not reports_df.empty:
            st.dataframe(reports_df, use_container_width=True, hide_index=True)
        else: st.info("Thư mục báo cáo đang trống.")

render_main_content(menu)
