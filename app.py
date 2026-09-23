import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import base64
import hashlib
import os

from utils import (
    VN_TIMEZONE, 
    compress_image_to_base64, 
    calculate_exact_minutes, 
    hex_to_rgba
)
from database import (
    supabase, 
    is_supabase_connected, 
    init_db_data,
    get_staff_df_db, 
    get_staff_list_db, 
    get_rules_df_db,
    get_production_logs_db, 
    get_production_logs_by_date_range,
    get_total_production_count_db, 
    get_attendance_db,
    load_app_settings_db, 
    load_folders_db
)

st.set_page_config(page_title="POSS - Quản Lý Sản Xuất", page_icon="📊", layout="wide")

init_db_data()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_app_memory_usage():
    try:
        import sys
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 ** 2)
        return f"{mem_mb:.1f} MB"
    except Exception:
        try:
            import resource
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform == "darwin":
                mem_mb = rss / (1024 ** 2)
            else:
                mem_mb = rss / 1024
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
        if estimated_db_kb > 1024:
            db_used_str = f"{estimated_db_kb / 1024:.2f} MB"
        else:
            db_used_str = f"{estimated_db_kb:.1f} KB"
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
        if storage_mb >= 1024:
            storage_display = f"{storage_mb / 1024:.2f} GB / 1 GB"
        else:
            storage_display = f"{storage_mb:.2f} MB / 1 GB"
            
        return db_display, storage_display
    except Exception:
        return "0 MB / 500 MB", "0 MB / 1 GB"

# ==================== KHỞI TẠO CSDL CHO QUẢN LÝ LỖI ====================
def add_error_log_db(ngay, nhan_su, loai_loi, so_luong_loi, ghi_chu):
    if supabase is None:
        return
    try:
        payload = {
            "ngay": str(ngay),
            "thoi_gian": datetime.datetime.now(VN_TIMEZONE).strftime("%H:%M:%S"),
            "nhan_su": nhan_su,
            "loai_loi": loai_loi,
            "so_luong_loi": int(so_luong_loi),
            "ghi_chu": ghi_chu
        }
        supabase.table("error_logs").insert(payload).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi khi lưu báo cáo lỗi: {e}")

@st.cache_data(ttl=300, show_spinner=False)
def get_error_logs_db():
    if supabase is None:
        return pd.DataFrame()
    try:
        res = supabase.table("error_logs").select("*").order("id", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id", "ngay": "Ngày", "thoi_gian": "Thời Gian", 
                "nhan_su": "Nhân Sự", "loai_loi": "Loại Lỗi", 
                "so_luong_loi": "Số Lượng Lỗi", "ghi_chu": "Ghi Chú"
            })
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception:
        pass
    return pd.DataFrame()

def delete_error_log_db(db_ids):
    if supabase is None:
        return
    try:
        for db_id in db_ids:
            supabase.table("error_logs").delete().eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception:
        pass

# ==================== KIỂM TRA ĐĂNG NHẬP SESSION & QUERY PARAMS ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_identifier" not in st.session_state:
    st.session_state.user_identifier = ""

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
            st.markdown("<div style='padding: 10px 0px;'>", unsafe_allow_html=True)
            with st.form("login_admin_form"):
                email_input = st.text_input("📧 Email Admin", placeholder="lamhoangsang169@gmail.com")
                password_admin = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...", key="pw_admin")
                remember_admin = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_admin")
                
                submitted_admin = st.form_submit_button("🚀 Đăng Nhập Quản Trị Viên", use_container_width=True)
                
                if submitted_admin:
                    if not email_input or not password_admin:
                        st.error("⚠️ Vui lòng nhập đầy đủ Email và Mật khẩu!")
                    elif supabase is None:
                        st.error("⚠️ Chưa kết nối được tới cơ sở dữ liệu!")
                    else:
                        try:
                            clean_email = email_input.strip()
                            res = supabase.auth.sign_in_with_password({
                                "email": clean_email,
                                "password": password_admin.strip()
                            })
                            if res and res.user:
                                st.session_state.logged_in = True
                                st.session_state.user_identifier = res.user.email
                                if remember_admin:
                                    st.query_params["auth_user"] = res.user.email
                                st.success("✅ Đăng nhập Admin thành công!")
                                st.rerun()
                            else:
                                st.error("❌ Email hoặc mật khẩu Admin không chính xác!")
                        except Exception as e:
                            st.error(f"❌ Lỗi đăng nhập: {e}")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with tab_staff:
            st.markdown("<div style='padding: 10px 0px;'>", unsafe_allow_html=True)
            with st.form("login_staff_form"):
                staff_list_opt = ["--- Chọn họ và tên ---"] + get_staff_list_db()
                login_name = st.selectbox("👤 Họ và tên nhân sự", staff_list_opt)
                password_staff = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...", key="pw_staff")
                remember_staff = st.checkbox("📌 Ghi nhớ đăng nhập", value=True, key="rem_staff")
                
                submitted_staff = st.form_submit_button("🚀 Đăng Nhập Nhân Viên", use_container_width=True)
                
                if submitted_staff:
                    if login_name == "--- Chọn họ và tên ---" or not password_staff:
                        st.error("⚠️ Vui lòng chọn họ tên và nhập mật khẩu!")
                    elif supabase is None:
                        st.error("⚠️ Chưa kết nối được tới cơ sở dữ liệu!")
                    else:
                        try:
                            res = supabase.table("user_accounts").select("*").eq("name", login_name).execute()
                            if res.data and len(res.data) > 0:
                                user_record = res.data[0]
                                if user_record["password_hash"] == hash_password(password_staff):
                                    st.session_state.logged_in = True
                                    st.session_state.user_identifier = login_name
                                    if remember_staff:
                                        st.query_params["auth_user"] = login_name
                                    st.success("✅ Đăng nhập thành công!")
                                    st.rerun()
                                else:
                                    st.error("❌ Mật khẩu không chính xác!")
                            else:
                                st.error("❌ Tài khoản chưa được Quản trị viên cấp mật khẩu!")
                        except Exception as e:
                            st.error(f"❌ Lỗi đăng nhập: {e}")
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
            
    st.stop()

# ==================== HỆ THỐNG PHÂN QUYỀN TÀI KHOẢN ====================
def get_user_permissions(identifier):
    default_perms = {
        "role": "Staff",
        "perm_input": False,
        "perm_report": False,
        "perm_attendance": True,
        "perm_rules": False
    }
    if not identifier or supabase is None:
        return default_perms
    
    clean_id = str(identifier).strip().lower()
    
    if clean_id == "lamhoangsang169@gmail.com":
        return {
            "role": "Admin",
            "perm_input": True,
            "perm_report": True,
            "perm_attendance": True,
            "perm_rules": True
        }

    try:
        res = supabase.table("user_accounts").select("*").eq("name", identifier).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            return {
                "role": row.get("role", "Staff"),
                "perm_input": row.get("perm_input", False),
                "perm_report": row.get("perm_report", False),
                "perm_attendance": row.get("perm_attendance", True),
                "perm_rules": row.get("perm_rules", False)
            }
    except Exception:
        pass
    return default_perms

user_perms = get_user_permissions(st.session_state.user_identifier)
current_user_role = user_perms["role"]

# ==================== CÁC HÀM CRUD BỔ SUNG TRONG APP ====================
def save_staff_list_db(edited_df):
    if supabase is None or current_user_role != "Admin":
        st.warning("⚠️ Bạn không có quyền thực hiện thao tác này!")
        return
    try:
        res_old = supabase.table("staff").select("id, name").execute()
        old_staffs = {row["id"]: row["name"] for row in res_old.data} if res_old.data else {}
        old_ids = list(old_staffs.keys())
        
        current_ids_in_editor = []
        for _, row in edited_df.iterrows():
            name = str(row.get("Nhân Sự", "")).strip()
            row_id = row.get("id")
            
            if not name or name.lower() in ["nan", "none"]:
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

def save_rules_df_db(df):
    if supabase is None or (not user_perms["perm_rules"] and current_user_role != "Admin"):
        st.warning("⚠️ Bạn không có quyền thay đổi định mức!")
        return
    try:
        res_old = supabase.table("rules").select("id, hang_muc, he_so_diem").execute()
        old_rules_map = {row["id"]: {"hang_muc": row["hang_muc"], "he_so_diem": row["he_so_diem"]} for row in res_old.data} if res_old.data else {}
        old_ids = list(old_rules_map.keys())
        
        inserts_rules = []
        current_ids_in_editor = []
        
        for idx, row in df.iterrows():
            row_id = row.get("id")
            new_hang_muc = str(row.get("Hạng Mục Công Việc", "")).strip()
            
            if not new_hang_muc or new_hang_muc.lower() in ["nan", "none"]:
                continue
                
            new_he_so = float(row.get("Hệ Số Điểm", 1.0)) if pd.notna(row.get("Hệ Số Điểm")) else 1.0
            
            payload = {
                "stt": int(idx + 1),
                "hang_muc": new_hang_muc,
                "don_vi": str(row.get("Đơn Vị", "Cái")).strip() if pd.notna(row.get("Đơn Vị")) else "Cái",
                "he_so_diem": new_he_so,
                "ghi_chu": str(row.get("Ghi Chú", "")).strip() if pd.notna(row.get("Ghi Chú")) else ""
            }
            
            if pd.notna(row_id) and int(row_id) in old_ids:
                rid = int(row_id)
                current_ids_in_editor.append(rid)
                
                old_info = old_rules_map.get(rid, {})
                if old_info.get("hang_muc") != new_hang_muc or old_info.get("he_so_diem") != new_he_so:
                    supabase.table("rules").update(payload).eq("id", rid).execute()
                    
                    old_hang_muc = old_info.get("hang_muc")
                    if old_hang_muc and old_hang_muc != new_hang_muc:
                        supabase.table("production_logs").update({"hang_muc_cong_viec": new_hang_muc}).eq("hang_muc_cong_viec", old_hang_muc).execute()
            else:
                inserts_rules.append(payload)
                
        if inserts_rules:
            res_ins = supabase.table("rules").insert(inserts_rules).execute()
            if res_ins.data:
                current_ids_in_editor.extend([r["id"] for r in res_ins.data])
                
        ids_to_delete = [oid for oid in old_ids if oid not in current_ids_in_editor]
        if ids_to_delete:
            supabase.table("rules").delete().in_("id", ids_to_delete).execute()
            
        st.cache_data.clear()
        st.success("⚡ Đã đồng bộ định mức thành công!")
    except Exception as e:
        st.error(f"Lỗi khi đồng bộ định mức: {e}")

def save_app_settings_db(settings_dict):
    if supabase is None or current_user_role != "Admin":
        return
    try:
        payload = {"id": 1, **settings_dict}
        supabase.table("app_settings").upsert(payload).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi lưu cấu hình: {e}")

def save_folders_db(folders_list):
    if supabase is None or current_user_role != "Admin":
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
    SUPABASE_URL_VAL = st.secrets["supabase"]["SUPABASE_URL"]
    for uploaded_file in uploaded_files[:4]:
        try:
            file_bytes = uploaded_file.getvalue()
            file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uploaded_file.name}"
            supabase.storage.from_("production-images").upload(file_name, file_bytes, {"content-type": uploaded_file.type})
            public_url = f"{SUPABASE_URL_VAL}/storage/v1/object/public/production-images/{file_name}"
            url_list.append(public_url)
        except Exception:
            pass
    return ",".join(url_list)

def upload_report_to_storage(file_name, csv_bytes):
    if supabase is None:
        return ""
    try:
        SUPABASE_URL_VAL = st.secrets["supabase"]["SUPABASE_URL"]
        unique_file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
        supabase.storage.from_("reports-storage").upload(unique_file_name, csv_bytes, {"content-type": "text/csv; charset=utf-8"})
        public_url = f"{SUPABASE_URL_VAL}/storage/v1/object/public/reports-storage/{unique_file_name}"
        return public_url
    except Exception:
        return ""

def add_production_log_db(ngay, thoi_gian, nhan_su, hang_muc, hinh_anh_url, don_vi, so_luong, he_so, tong_diem, ghi_chu):
    if supabase is None:
        return
    try:
        payload = {
            "ngay": str(ngay), "thoi_gian": thoi_gian, "nhan_su": nhan_su,
            "hang_muc_cong_viec": hang_muc, "hinh_anh_url": hinh_anh_url, "don_vi": don_vi,
            "so_luong": int(so_luong), "he_so_diem": float(he_so), "tong_diem": float(tong_diem),
            "ghi_chu": ghi_chu, "is_deleted": False
        }
        supabase.table("production_logs").insert(payload).execute()
        st.cache_data.clear()
    except Exception:
        pass

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
    if supabase is None or current_user_role != "Admin":
        return
    try:
        for db_id in db_ids:
            supabase.table("production_logs").delete().eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception:
        pass

def add_attendance_db(ngay, nhan_su, gio_vao, gio_ra, phut, ghi_chu):
    if supabase is None:
        return
    try:
        payload = {
            "ngay": str(ngay), "nhan_su": nhan_su, "gio_vao_ca": gio_vao,
            "gio_ra_ca": gio_ra, "so_phut_lam_viec": int(phut), "ghi_chu": ghi_chu
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
        return
    try:
        payload = {
            "ten_file": ten_file,
            "ngay_tao": datetime.datetime.now(VN_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
            "file_url": file_url,
            "is_deleted": False
        }
        supabase.table("export_reports").insert(payload).execute()
        st.success("Đã lưu thông tin báo cáo thành công!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi khi lưu báo cáo: {e}")

@st.cache_data(ttl=1800, show_spinner=False)
def get_export_reports_db(is_deleted=False):
    if supabase is None:
        return pd.DataFrame()
    try:
        res = supabase.table("export_reports").select("*").eq("is_deleted", is_deleted).order("id", desc=True).limit(50).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={"id": "db_id", "ten_file": "Tên File", "ngay_tao": "Ngày Tạo", "file_url": "Đường Dẫn URL"})
            df.insert(0, "STT", range(1, len(df) + 1))
            return df
    except Exception:
        pass
    return pd.DataFrame()

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
    if supabase is None or current_user_role != "Admin":
        return
    try:
        for db_id in db_ids:
            supabase.table("export_reports").delete().eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception:
        pass

# ==================== KHỞI TẠO BIẾN SESSION ====================
st.session_state.staff_list = get_staff_list_db()
st.session_state.rules_df = get_rules_df_db()
st.session_state.chart_colors = ["#ff4b4b", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#14b8a6", "#f97316", "#6366f1"]

# Cập nhật danh mục thư mục mặc định có thêm 6. Quản Lý Lỗi
loaded_folders = load_folders_db()
if loaded_folders:
    items = loaded_folders[0].get("items", [])
    if not any(item.get("id") == "menu_6" for item in items):
        items.append({"id": "menu_6", "name": "6. Quản Lý Lỗi"})
        loaded_folders[0]["items"] = items
    st.session_state.folders = loaded_folders
else:
    st.session_state.folders = [{
        "folder_name": "📌 Quản Lý Nghiệp Vụ",
        "items": [
            {"id": "menu_1", "name": "1. Nhập Sản Lượng"},
            {"id": "menu_2", "name": "2. Báo Cáo & Biểu Đồ"},
            {"id": "menu_3", "name": "3. Tham chiếu Định mức"},
            {"id": "menu_4", "name": "4. Thùng Rác Sản Lượng"},
            {"id": "menu_5", "name": "5. Thư Mục Báo Cáo"},
            {"id": "menu_6", "name": "6. Quản Lý Lỗi"}
        ]
    }]

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
    .avatar-popover-wrapper {{ position: absolute; bottom: 2px; right: 10px; z-index: 9999999; }}
    .avatar-popover-wrapper [data-testid="stPopover"] button {{ background-color: #ffffff !important; border: 2px solid {st.session_state.primary_color} !important; border-radius: 50% !important; width: 32px !important; height: 32px !important; padding: 0px !important; display: flex !important; align-items: center !important; justify-content: center !important; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
    .avatar-popover-wrapper [data-testid="stPopover"] button p {{ display: none !important; }}
    .avatar-popover-wrapper [data-testid="stPopover"] button::after {{ content: "⋮"; font-size: 16px; font-weight: bold; color: #333333; line-height: 1; }}
    .sidebar-scrollable-content {{ flex-grow: 1; padding-left: 1rem; padding-right: 1rem; padding-bottom: 50px; }}
    
    .img-horizontal-container {{
        display: flex;
        flex-direction: row;
        gap: 12px;
        align-items: flex-start;
        flex-wrap: wrap;
    }}
    .img-item-box {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
    }}
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
        except Exception:
            pass

    st.markdown('<div class="avatar-wrapper">', unsafe_allow_html=True)
    if has_custom_avatar:
        with st.popover(" ", use_container_width=False):
            st.markdown("##### 🔍 Xem Ảnh Đại Diện")
            st.image(avatar_bytes_obj, use_container_width=True)
        encoded_img = base64.b64encode(avatar_bytes_obj).decode("utf-8")
        st.markdown(f'<div style="cursor: pointer; text-align: center;"><img src="data:image/jpeg;base64,{encoded_img}" style="width:140px; height:140px; border-radius:50%; object-fit:cover; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3);"></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="width:140px; height:140px; border-radius:50%; background:#cbd5e1; display:flex; align-items:center; justify-content:center; font-size:50px; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3); margin: 0 auto;">👤</div>', unsafe_allow_html=True)

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
                        "primary_color": st.session_state.primary_color, "bg_color": st.session_state.bg_color,
                        "sidebar_bg": st.session_state.sidebar_bg, "sidebar_opacity": st.session_state.sidebar_opacity,
                        "text_color": st.session_state.text_color, "bg_image_base64": st.session_state.bg_image_base64,
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
                    "primary_color": st.session_state.primary_color, "bg_color": st.session_state.bg_color,
                    "sidebar_bg": st.session_state.sidebar_bg, "sidebar_opacity": st.session_state.sidebar_opacity,
                    "text_color": st.session_state.text_color, "bg_image_base64": None,
                    "avatar_base64": None
                })
                st.success("Đã xóa ảnh đại diện!")
                st.rerun()
    st.markdown('</div></div></div>', unsafe_allow_html=True)

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
            if current_user_role == "Admin":
                filtered_items.append(item)
            else:
                item_id = item.get("id")
                if item_id == "menu_1" and (user_perms["perm_input"] or True): filtered_items.append(item)
                elif item_id == "menu_2" and user_perms["perm_report"]: filtered_items.append(item)
                elif item_id == "menu_3" and user_perms["perm_rules"]: filtered_items.append(item)
                elif item_id == "menu_4" and current_user_role == "Admin": filtered_items.append(item)
                elif item_id == "menu_5" and user_perms["perm_report"]: filtered_items.append(item)
                elif item_id == "menu_6": filtered_items.append(item)

        if filtered_items:
            with st.expander(folder["folder_name"], expanded=True):
                for item in filtered_items:
                    if st.button(item["name"], use_container_width=True, key=f"btn_{item['id']}"):
                        st.session_state.current_menu = item["name"]
                        st.rerun()

    if current_user_role == "Admin":
        st.markdown("---")
        st.markdown("### ⚙️ Cấu Hình Hệ Thống (Admin)")
        if st.button("📁 Quản Lý Thư Mục & Menu", use_container_width=True):
            st.session_state.current_menu = "📁 Quản Lý Thư Mục & Menu"
            st.rerun()
        if st.button("🎨 Cài Đặt Giao Diện", use_container_width=True):
            st.session_state.current_menu = "🎨 Cài Đặt Giao Diện"
            st.rerun()
        if st.button("🛡️ Quản Lý Tài Khoản & Phân Quyền", use_container_width=True):
            st.session_state.current_menu = "🛡️ Quản Lý Tài Khoản & Phân Quyền"
            st.rerun()
        if st.button("🧹 Làm Sạch & Tối Ưu Dữ Liệu", use_container_width=True):
            st.session_state.current_menu = "🧹 Làm Sạch Dữ Liệu"
            st.rerun()

    st.markdown("---")
    if is_supabase_connected:
        st.markdown('<div style="background: rgba(16, 185, 129, 0.15); padding: 8px 12px; border-radius: 6px; border: 1px solid #10b981; text-align: center; font-size: 0.85rem; font-weight: bold; color: #047857; margin-bottom: 6px;">🟢 Đã kết nối Supabase</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background: rgba(239, 68, 68, 0.15); padding: 8px 12px; border-radius: 6px; border: 1px solid #ef4444; text-align: center; font-size: 0.85rem; font-weight: bold; color: #b91c1c; margin-bottom: 6px;">🔴 Chưa kết nối Supabase</div>', unsafe_allow_html=True)

    ram_usage_str = get_app_memory_usage()
    db_usage_str, storage_usage_str = get_detailed_storage_usage()

    st.markdown(f'<div style="background: rgba(147, 51, 234, 0.12); padding: 5px 8px; border-radius: 6px; border: 1px solid #9333ea; text-align: center; font-size: 0.78rem; font-weight: bold; color: #7e22ce; margin-bottom: 5px;">🧠 RAM App: <b>{ram_usage_str}</b></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background: rgba(245, 158, 11, 0.12); padding: 5px 8px; border-radius: 6px; border: 1px solid #f59e0b; text-align: center; font-size: 0.78rem; font-weight: bold; color: #b45309; margin-bottom: 5px;">🗄️ Database: <b>{db_usage_str}</b></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background: rgba(16, 185, 129, 0.12); padding: 5px 8px; border-radius: 6px; border: 1px solid #10b981; text-align: center; font-size: 0.78rem; font-weight: bold; color: #047857; margin-bottom: 6px;">💾 File Storage: <b>{storage_usage_str}</b></div>', unsafe_allow_html=True)

    current_loaded_df = get_production_logs_db(is_deleted=False, limit_rows=None)
    current_shown_count = len(current_loaded_df) if not current_loaded_df.empty else 0
    total_db_count = get_total_production_count_db()

    st.markdown(f'<div style="background: rgba(59, 130, 246, 0.12); padding: 8px 12px; border-radius: 6px; border: 1px solid #3b82f6; text-align: center; font-size: 0.85rem; font-weight: bold; color: #1d4ed8;">📊 Tải tối đa: <span style="color: #ff4b4b;">{current_shown_count}</span> / {total_db_count} bản ghi</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

menu = st.session_state.current_menu

def get_feature_type(menu_name):
    if menu_name == "⏱️ Chấm Công Ca Làm Việc": return "attendance"
    if menu_name == "📁 Quản Lý Thư Mục & Menu": return "manage_folders"
    if menu_name == "🎨 Cài Đặt Giao Diện": return "settings_ui"
    if menu_name == "🛡️ Quản Lý Tài Khoản & Phân Quyền": return "manage_roles"
    if menu_name == "🧹 Làm Sạch Dữ Liệu": return "clean_data"
    for folder in st.session_state.folders:
        for item in folder["items"]:
            if item["name"] == menu_name:
                if item["id"] == "menu_1": return "input_production"
                if item["id"] == "menu_2": return "report"
                if item["id"] == "menu_3": return "rules"
                if item["id"] == "menu_4": return "trash"
                if item["id"] == "menu_5": return "report_folder"
                if item["id"] == "menu_6": return "error_management"
                return "input_production"
    return "input_production"

# ==================== KHU VỰC NỘI DUNG TỐI ƯU BẰNG ST.FRAGMENT ====================
@st.fragment
def render_main_content(current_menu_name):
    feature = get_feature_type(current_menu_name)

    # ==================== 1. NHẬP SẢN LƯỢNG ====================
    if feature == "input_production":
        now_vn = datetime.datetime.now(VN_TIMEZONE)
        today_str = str(now_vn.date())
        
        st.subheader(f"{current_menu_name} ({today_str})")

        if current_user_role != "Admin" and not user_perms["perm_input"]:
            st.info("👁️ Tài khoản của bạn đang ở chế độ **Chỉ xem**. Bạn có thể theo dõi bảng danh sách bên dưới nhưng không được phép thêm hoặc chỉnh sửa dữ liệu.")
        else:
            att_df_check = get_attendance_db()
            checked_in_set = set()
            if not att_df_check.empty:
                checked_in_set = set(att_df_check[att_df_check["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist())

            active_staff = [s for s in st.session_state.staff_list if s in checked_in_set]

            if not active_staff:
                st.warning(f"⚠️ Hiện tại chưa có nhân sự nào **Check-in (Vào ca)** hoặc các ca trước chưa kết thúc. Vui lòng thực hiện Check-in trước khi nhập sản lượng!")
            else:
                req_img = st.session_state.get("require_image", True)
                req_qty = st.session_state.get("require_quantity", True)
                
                with st.form("entry_form"):
                    f_col1, f_col2, f_col3 = st.columns(3)
                    with f_col1: ngay = st.date_input("Ngày làm việc", now_vn.date(), disabled=True)
                    with f_col2:
                        staff_options = ["--- Vui lòng chọn nhân sự ---"] + active_staff
                        nhan_su = st.selectbox("Nhân sự thực hiện", staff_options)
                    with f_col3:
                        raw_tasks = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else []
                        danh_sach_hang_muc = [str(t).strip() for t in raw_tasks if pd.notna(t) and str(t).strip() and str(t).strip().lower() not in ["nan", "none"]]
                        
                        hang_muc = st.selectbox("Hạng mục công việc", danh_sach_hang_muc)
                        
                    record_images = st.file_uploader("Tải ảnh đính kèm (Tối đa 4 ảnh)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="record_img")
                            
                    f_col4, f_col5 = st.columns(2)
                    with f_col4: so_luong = st.number_input("Số lượng thực tế", min_value=0, value=0, step=1)
                    with f_col5: ghi_chu = st.text_input("Ghi chú", "")
                        
                    submitted = st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True)

                    if submitted:
                        is_valid = True
                        cleaned_hang_muc = str(hang_muc).strip()
                        cleaned_ghi_chu = str(ghi_chu).strip()

                        if nhan_su == "--- Vui lòng chọn nhân sự ---":
                            is_valid = False
                            st.session_state["form_msg"] = ("error", "⚠️ Vui lòng chọn đúng tên nhân sự thực hiện!")
                        elif req_img and not record_images: 
                            is_valid = False
                            st.session_state["form_msg"] = ("error", "⚠️ Vui lòng tải lên ảnh đính kèm!")
                        elif req_qty and so_luong <= 0: 
                            is_valid = False
                            st.session_state["form_msg"] = ("error", "⚠️ Số lượng thực tế phải lớn hơn 0!")
                        elif record_images and len(record_images) > 4:
                            is_valid = False
                            st.session_state["form_msg"] = ("error", "⚠️ Bạn chỉ được phép đính kèm tối đa 4 ảnh!")
                        elif "công việc phát sinh" in cleaned_hang_muc.lower() and not cleaned_ghi_chu:
                            is_valid = False
                            st.session_state["form_msg"] = ("error", "⚠️ Bắt buộc phải nhập nội dung vào phần Ghi chú khi chọn 'Công việc phát sinh'!")

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
                    if m_type == "success": st.success(m_text)
                    else: st.error(m_text)
                    del st.session_state["form_msg"]

        st.markdown("---")
        
        col_title_1, col_title_2 = st.columns([3, 1])
        with col_title_1:
            st.subheader("Danh Sách Sản Lượng & Hình Ảnh")
        with col_title_2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_input"):
                st.cache_data.clear()
                st.rerun()
        
        input_df = get_production_logs_db(is_deleted=False, limit_rows=None)
        if not input_df.empty:
            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1.2, 1.2, 0.9, 0.9, 0.8])
            
            with f_col1:
                sub_d1, sub_d2 = st.columns(2)
                with sub_d1:
                    filter_start_date = st.date_input("Từ ngày", value=now_vn.date(), key="f_start_date")
                with sub_d2:
                    filter_end_date = st.date_input("Đến ngày", value=now_vn.date(), key="f_end_date")
                
                start_d_str = str(filter_start_date)
                end_d_str = str(filter_end_date)
                
                count_by_date = len(input_df[(input_df["Ngày"] >= start_d_str) & (input_df["Ngày"] <= end_d_str)])
                st.markdown(f"<small style='color: #1d4ed8; font-weight: bold;'>📅 Khoảng ngày có: {count_by_date} bản ghi</small>", unsafe_allow_html=True)
                
            with f_col2:
                enable_hour_filter = st.checkbox("Lọc theo Giờ", value=False)
                if enable_hour_filter:
                    t_sub1, t_sub2 = st.columns(2)
                    with t_sub1: start_t = st.time_input("Từ", datetime.time(7, 30), label_visibility="collapsed")
                    with t_sub2: end_t = st.time_input("Đến", datetime.time(17, 0), label_visibility="collapsed")
                else:
                    start_t, end_t = None, None
                
            with f_col3:
                all_staff = ["Tất cả"] + sorted(input_df["Nhân Sự"].unique().tolist())
                filter_staff = st.selectbox("Lọc theo Nhân Sự", all_staff)
                
            temp_filtered_df = input_df.copy()
            temp_filtered_df = temp_filtered_df[(temp_filtered_df["Ngày"] >= start_d_str) & (temp_filtered_df["Ngày"] <= end_d_str)]
            
            if filter_staff != "Tất cả": 
                temp_filtered_df = temp_filtered_df[temp_filtered_df["Nhân Sự"] == filter_staff]

            if enable_hour_filter and start_t and end_t:
                def check_time_in_range(t_str):
                    try:
                        t_val = datetime.datetime.strptime(str(t_str).strip(), "%H:%M:%S").time()
                        return start_t <= t_val <= end_t
                    except:
                        return True
                temp_filtered_df = temp_filtered_df[temp_filtered_df["Thời Gian"].apply(check_time_in_range)]

            with f_col4:
                available_tasks = ["Tất cả"] + sorted(temp_filtered_df["Hạng Mục Công Việc"].unique().tolist()) if not temp_filtered_df.empty else ["Tất cả"]
                filter_task = st.selectbox("Lọc theo Hạng Mục", available_tasks)
            
            filtered_df = temp_filtered_df.copy()
            if filter_task != "Tất cả": 
                filtered_df = filtered_df[filtered_df["Hạng Mục Công Việc"] == filter_task]
                
            rows_per_page = 10
            total_rows = len(filtered_df)
            total_pages = max((total_rows - 1) // rows_per_page + 1, 1)

            with f_col5:
                current_page = st.number_input(f"Trang hiển thị ({total_pages} tr | {total_rows} bản ghi)", min_value=1, max_value=total_pages, value=1, step=1, key="pagination_page_num")

            start_idx = (current_page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            paginated_df = filtered_df.iloc[start_idx:end_idx].reset_index(drop=True)

            if filter_task != "Tất cả":
                total_qty_task = filtered_df["Số Lượng"].sum() if not filtered_df.empty else 0
                unit_name = filtered_df["Đơn Vị"].values[0] if not filtered_df.empty and "Đơn Vị" in filtered_df.columns else "Cái"
                st.markdown(f'<div style="background: rgba(59, 130, 246, 0.15); padding: 12px 18px; border-radius: 8px; border: 2px solid #3b82f6; margin-bottom: 15px; font-size: 1rem; font-weight: bold; text-align: center;">📊 Tổng số lượng của hạng mục <span style="color: #ff4b4b;">"{filter_task}"</span>: <span style="font-size: 1.2rem; color: #1d4ed8;">{total_qty_task:,.0f}</span> {unit_name}</div>', unsafe_allow_html=True)

            if not paginated_df.empty:
                can_delete_data = (current_user_role == "Admin" or user_perms["perm_input"])

                if can_delete_data:
                    with st.form("delete_production_form"):
                        st.markdown("<div style='background: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 8px; border: 1px solid #cbd5e1; margin-bottom: 15px;'>", unsafe_allow_html=True)
                        col_btn_1, col_btn_2 = st.columns(2)
                        with col_btn_1:
                            submitted_delete_selected = st.form_submit_button("🗑️ Xóa các dòng đã chọn", use_container_width=True, type="primary")
                        with col_btn_2:
                            confirm_delete_all = st.checkbox("Xác nhận xóa tất cả trang này", key="chk_confirm_delete_all")
                            submitted_delete_all = st.form_submit_button("🗑️ Xóa tất cả trang này", use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                        selected_ids_to_delete = []
                        for idx, row in paginated_df.iterrows():
                            display_stt = total_rows - (start_idx + idx)
                            
                            row_c1, row_c2 = st.columns([3.8, 1.2])
                            with row_c1:
                                st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;">
                                    <b>STT: {display_stt}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} ⏰ {row['Thời Gian']} &nbsp;|&nbsp; 👤 <b>{row['Nhân Sự']}</b><br>
                                    📌 {row['Hạng Mục Công Việc']} &nbsp;|&nbsp; 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                                    💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                                </div>
                                """, unsafe_allow_html=True)
                                if st.checkbox(f"Chọn xóa bản ghi STT {display_stt}", key=f"chk_{row['db_id']}"):
                                    selected_ids_to_delete.append(row['db_id'])
                                    
                            with row_c2:
                                img_url_val = row.get("hinh_anh_url") or row.get("Hình Ảnh") or ""
                                if img_url_val and isinstance(img_url_val, str) and img_url_val.strip():
                                    urls = [u.strip() for u in img_url_val.split(",") if u.strip()]
                                    valid_urls = [u for u in urls if u.startswith("http://") or u.startswith("https://")]
                                    if valid_urls:
                                        img_cols = st.columns(len(valid_urls))
                                        for idx_u, (u_url, col_item) in enumerate(zip(valid_urls, img_cols)):
                                            with col_item:
                                                with st.popover(" ", help="Xem ảnh phóng to & Fullscreen"):
                                                    st.image(u_url, use_container_width=True)
                                                st.image(u_url, width=60)
                                    else:
                                        st.markdown("<small style='color: gray;'>Không có ảnh hợp lệ</small>", unsafe_allow_html=True)
                                else:
                                    st.markdown("<small style='color: gray;'>Không có ảnh</small>", unsafe_allow_html=True)

                            st.markdown("---")

                        if submitted_delete_selected:
                            if selected_ids_to_delete:
                                update_production_log_deleted_status(selected_ids_to_delete, True)
                                st.success("Đã chuyển các dòng đã chọn vào thùng rác thành công!")
                                st.rerun()
                            else:
                                st.warning("⚠️ Vui lòng tích chọn ít nhất một dòng cần xóa!")

                        if submitted_delete_all:
                            if confirm_delete_all:
                                all_paginated_ids = paginated_df["db_id"].tolist()
                                if all_paginated_ids:
                                    update_production_log_deleted_status(all_paginated_ids, True)
                                    st.success("Đã chuyển toàn bộ bản ghi đang hiển thị ở trang này vào thùng rác!")
                                    st.rerun()
                            else:
                                st.warning("⚠️ Vui lòng tích chọn xác nhận trước khi bấm xóa tất cả!")
                else:
                    for idx, row in paginated_df.iterrows():
                        display_stt = total_rows - (start_idx + idx)
                        
                        row_c1, row_c2 = st.columns([3.8, 1.2])
                        with row_c1:
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;">
                                <b>STT: {display_stt}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} ⏰ {row['Thời Gian']} &nbsp;|&nbsp; 👤 <b>{row['Nhân Sự']}</b><br>
                                📌 {row['Hạng Mục Công Việc']} &nbsp;|&nbsp; 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                                💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                            </div>
                            """, unsafe_allow_html=True)
                        with row_c2:
                            img_url_val = row.get("hinh_anh_url") or row.get("Hình Ảnh") or ""
                            if img_url_val and isinstance(img_url_val, str) and img_url_val.strip():
                                urls = [u.strip() for u in img_url_val.split(",") if u.strip()]
                                valid_urls = [u for u in urls if u.startswith("http://") or u.startswith("https://")]
                                if valid_urls:
                                    img_cols = st.columns(len(valid_urls))
                                    for idx_u, (u_url, col_item) in enumerate(zip(valid_urls, img_cols)):
                                        with col_item:
                                            with st.popover(" ", help="Xem ảnh phóng to & Fullscreen"):
                                                st.image(u_url, use_container_width=True)
                                            st.image(u_url, width=60)
                                else:
                                    st.markdown("<small style='color: gray;'>Không có ảnh hợp lệ</small>", unsafe_allow_html=True)
                            else:
                                st.markdown("<small style='color: gray;'>Không có ảnh</small>", unsafe_allow_html=True)
                        st.markdown("---")
            else:
                st.info("Không tìm thấy bản ghi nào khớp bộ lọc.")
        else:
            st.info("Chưa có dữ liệu sản lượng trong CSDL.")

    # ==================== CHẤM CÔNG CA LÀM VIỆC ====================
    elif feature == "attendance":
        col_att_h1, col_att_h2 = st.columns([3, 1])
        with col_att_h1:
            st.header(current_menu_name)
        with col_att_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_att"):
                st.cache_data.clear()
                st.rerun()

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
            with f2:
                att_staff_options = ["--- Vui lòng chọn nhân sự ---"] + st.session_state.staff_list
                att_staff = st.selectbox("Nhân sự", att_staff_options)
            with f3: att_note = st.text_input("Ghi chú ca", "")
            
            b1, b2 = st.columns(2)
            with b1: check_in = st.form_submit_button("🟢 Check-in (Vào ca)", use_container_width=True)
            with b2: check_out = st.form_submit_button("🔴 Check-out (Kết thúc)", use_container_width=True)
            
            time_str = now_vn.strftime("%H:%M:%S")
            if check_in:
                if att_staff == "--- Vui lòng chọn nhân sự ---":
                    st.session_state["att_msg"] = ("warning", "⚠️ Vui lòng chọn đúng tên nhân sự!")
                elif att_staff in checked_in_set:
                    st.session_state["att_msg"] = ("warning", f"⚠️ Nhân sự {att_staff} đang trong ca làm việc!")
                else:
                    add_attendance_db(att_date, att_staff, time_str, "Chưa kết thúc", 0, att_note)
                    st.session_state["att_msg"] = ("success", f"✅ Check-in thành công cho **{att_staff}** lúc **{time_str}**!")
                    st.rerun()
            if check_out:
                if att_staff == "--- Vui lòng chọn nhân sự ---":
                    st.session_state["att_msg"] = ("warning", "⚠️ Vui lòng chọn đúng tên nhân sự!")
                else:
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
                            "gio_ra_ca": time_str, "so_phut_lam_viec": int(so_phut_thuc_te), "ghi_chu": final_note
                        }).eq("id", row_id).execute()
                        st.cache_data.clear()
                        st.session_state["att_msg"] = ("success", f"✅ Check-out thành công cho **{att_staff}** (Tổng: **{so_phut_thuc_te} phút**)!")
                    else:
                        st.session_state["att_msg"] = ("warning", f"⚠️ Không tìm thấy mốc Vào ca nào đang mở cho **{att_staff}**!")
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
            if current_user_role == "Admin":
                with st.form("delete_att_form"):
                    st.markdown("##### 🗑️ Xóa Bản Ghi Chấm Công Lỗi")
                    confirm_del_all_att = st.checkbox("⚠️ Tôi chắc chắn muốn xóa TOÀN BỘ lịch sử chấm công", key="chk_confirm_del_all_att")
                    
                    att_col1, att_col2 = st.columns(2)
                    with att_col1: submitted_delete_selected = st.form_submit_button("Xóa Các Dòng Đã Chọn", use_container_width=True)
                    with att_col2: submitted_delete_all = st.form_submit_button("🔥 Xóa Toàn Bộ Lịch Sử Chấm Công", use_container_width=True, type="primary")

                    att_ids_to_del = []
                    for idx, r in att_df.iterrows():
                        if st.checkbox(f"Xóa dòng STT {r['STT']} - {r['Nhân Sự']} ({r['Ngày']} | {r['Giờ Vào Ca']} -> {r['Giờ Ra Ca']})", key=f"del_att_{r['db_id']}"):
                            att_ids_to_del.append(r['db_id'])

                    if submitted_delete_selected:
                        if att_ids_to_del:
                            delete_attendance_db(att_ids_to_del)
                            st.success("Đã xóa các bản ghi chấm công đã chọn thành công!")
                            st.rerun()
                        else:
                            st.warning("Vui lòng tích chọn ít nhất một dòng cần xóa!")

                    if submitted_delete_all:
                        if confirm_del_all_att:
                            all_att_ids = att_df["db_id"].tolist()
                            if all_att_ids:
                                delete_attendance_db(all_att_ids)
                                st.success("Đã xóa toàn bộ lịch sử chấm công thành công!")
                                st.rerun()
                        else:
                            st.warning("⚠️ Vui lòng tích chọn hộp xác nhận an toàn trước khi bấm Xóa Toàn Bộ!")

    # ==================== BÁO CÁO & BIỂU ĐỒ ====================
    elif feature == "report":
        col_rep_h1, col_rep_h2 = st.columns([3, 1])
        with col_rep_h1:
            st.header(current_menu_name)
        with col_rep_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_report"):
                st.cache_data.clear()
                st.rerun()
        
        col_date1, col_date2 = st.columns(2)
        default_start = datetime.date.today().replace(day=1)
        default_end = datetime.date.today()
        
        with col_date1:
            report_start_date = st.date_input("Từ ngày", default_start)
        with col_date2:
            report_end_date = st.date_input("Đến ngày", default_end)

        all_staff_current = st.session_state.staff_list
        input_df = get_production_logs_by_date_range(report_start_date, report_end_date)
        
        if not input_df.empty:
            summary = input_df.groupby("Nhân Sự").agg(Tổng_Số_Lượng=("Số Lượng", "sum"), Tổng_Điểm=("Tổng Điểm", "sum")).reset_index()
        else:
            summary = pd.DataFrame(columns=["Nhân Sự", "Tổng_Số_Lượng", "Tổng_Điểm"])

        if not summary.empty:
            summary = summary[summary["Nhân Sự"].isin(all_staff_current)]
            summary = summary[summary["Tổng_Điểm"] > 0]
        
        total_all_points = summary["Tổng_Điểm"].sum() if not summary.empty else 0
        if not summary.empty:
            summary["Tỷ_Lệ_Đóng_Góp"] = summary["Tổng_Điểm"].apply(lambda x: (x / total_all_points) if total_all_points > 0 else 0)
            summary["Xếp_Loại"] = summary["Tổng_Điểm"].apply(lambda pts: "Xuất Sắc" if pts >= 700 else ("Đạt" if pts >= 400 else "Cần Cố Gắn"))
            summary_display = summary[["Nhân Sự", "Tổng_Số_Lượng", "Tổng_Điểm", "Tỷ_Lệ_Đóng_Góp", "Xếp_Loại"]].copy()
            summary_display.columns = ["Nhân Sự", "Số Lượng Thực Tế", "Tổng Điểm", "Tỷ Lệ Đóng Góp", "Xếp Loại"]
        else:
            summary_display = pd.DataFrame(columns=["Nhân Sự", "Số Lượng Thực Tế", "Tổng Điểm", "Tỷ Lệ Đóng Góp", "Xếp Loại"])
        
        st.subheader("Bảng Tổng Kết Theo Nhân Sự")
        if not summary_display.empty:
            st.dataframe(summary_display.style.format({"Số Lượng Thực Tế": "{:,.0f}", "Tổng Điểm": "{:,.1f}", "Tỷ Lệ Đóng Góp": "{:.2%}"}), use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu sản lượng trong khoảng thời gian này.")

        st.markdown("---")
        st.subheader("⚖️ Bảng Đối Chiếu Thời Gian Làm Việc & Sản Lượng")
        att_df = get_attendance_db()
        att_summary = att_df.groupby("Nhân Sự")["Số Phút Làm Việc"].sum().reset_index() if not att_df.empty else pd.DataFrame(columns=["Nhân Sự", "Tổng Phút Làm Việc"])
        att_summary.columns = ["Nhân Sự", "Tổng Phút Làm Việc"]
            
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
                        current_rank_num = current_rank_num + 1 if idx > 0 else 1
                        if current_rank_num == 1: rank_badges.append("🥇 Hạng 1")
                        elif current_rank_num == 2: rank_badges.append("🥈 Hạng 2")
                        elif current_rank_num == 3: rank_badges.append("🥉 Hạng 3")
                        else: rank_badges.append(f"Top {current_rank_num}")
                comparison_df.insert(0, "Xếp Hạng", rank_badges)
                
                total_minutes_all = comparison_df["Tổng Phút Làm Việc"].sum()
                total_pts_all = comparison_df["Tổng_Điểm"].sum()
                comparison_df["Tỷ_Lệ_Thời_Gian"] = comparison_df["Tổng Phút Làm Việc"].apply(lambda x: (x / total_minutes_all) if total_minutes_all > 0 else 0)
                comparison_df["Tỷ_Lệ_Đóng_Góp"] = comparison_df["Tổng_Điểm"].apply(lambda x: (x / total_pts_all) if total_pts_all > 0 else 0)
                comparison_df["Chênh_Lệch_%"] = comparison_df["Tỷ_Lệ_Đóng_Góp"] - comparison_df["Tỷ_Lệ_Thời_Gian"]
                comparison_df["Số_Ngày_Làm_Việc"] = comparison_df["Tổng Phút Làm Việc"] / 480.0
                
                comparison_table = comparison_df[["Xếp Hạng", "Nhân Sự", "Tổng Phút Làm Việc", "Số_Ngày_Làm_Việc", "Tỷ_Lệ_Thời_Gian", "Tổng_Điểm", "Tỷ_Lệ_Đóng_Góp", "Chênh_Lệch_%"]].copy()
                comparison_table.columns = ["Xếp Hạng", "Nhân Sự", "Tổng Thời Gian (Phút)", "Số ngày làm việc", "Tỷ Lệ Thời Gian (%)", "Tổng Điểm", "Tỷ Lệ Sản Lượng (%)", "Chênh Lệch"]
                
                st.dataframe(comparison_table.style.format({
                    "Tổng Thời Gian (Phút)": "{:,.0f}", "Số ngày làm việc": "{:,.2f}", "Tỷ Lệ Thời Gian (%)": "{:.2%}",
                    "Tổng Điểm": "{:,.1f}", "Tỷ Lệ Sản Lượng (%)": "{:.2%}", "Chênh Lệch": "{:+.2%}"
                }), use_container_width=True, hide_index=True)
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
                        task_details.append(" | ".join([f"{t}: {q}" for t, q in grouped_tasks.items()]))
                    else:
                        task_details.append("")
                export_csv_df["Chi Tiết Hạng Mục"] = task_details

            exp_col1, exp_col2 = st.columns([1, 3])
            with exp_col1:
                csv_bytes = export_csv_df.to_csv(index=False).encode('utf-8-sig')
                file_name_val = f"bao_cao_san_luong_{report_start_date}_den_{report_end_date}.csv"
                if st.button("📥 Xuất File & Lưu Cloud", use_container_width=True):
                    file_url = upload_report_to_storage(file_name_val, csv_bytes)
                    if file_url: save_export_report_db(file_name_val, file_url)
                st.download_button("💾 Tải File Về Máy", data=csv_bytes, file_name=file_name_val, mime="text/csv", use_container_width=True)

            summary_chart = summary.copy()
            summary_chart['Color'] = [st.session_state.chart_colors[i % len(st.session_state.chart_colors)] for i in range(len(summary_chart))]

            chart_col1, chart_col2 = st.columns([0.45, 1.35])
            with chart_col1:
                fig_plotly = px.pie(
                    summary_chart, 
                    names="Nhân Sự", 
                    values="Tổng_Điểm", 
                    hole=0, 
                    color="Nhân Sự",
                    color_discrete_map=dict(zip(summary_chart["Nhân Sự"], summary_chart["Color"]))
                )
                fig_plotly.update_traces(textposition='inside', textinfo='percent', textfont=dict(size=20, color='white', family='Arial Black'), pull=[0.03] * len(summary_chart))
                fig_plotly.update_layout(margin=dict(t=30, b=30, l=30, r=30), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=320)
                st.plotly_chart(fig_plotly, use_container_width=True)
                
            with chart_col2:
                st.markdown("### 📌 Chi Tiết Điểm Số & Tỷ Lệ")
                for idx, row in summary_chart.iterrows():
                    staff_name = row["Nhân Sự"]
                    short_name = staff_name.split()[-1] if len(staff_name.split()) > 1 else staff_name
                    pts, pct = row["Tổng_Điểm"], row["Tỷ_Lệ_Đóng_Góp"] * 100
                    color_code = row["Color"]
                    st.markdown(f'<div style="background-color: #f8fafc; padding: 6px 10px; border-radius: 6px; margin-bottom: 6px; border-left: 4px solid {color_code}; border: 1px solid #e2e8f0; font-size: 0.85rem;"><span style="display:inline-block; width:7px; height:7px; background-color:{color_code}; border-radius:2px; margin-right:4px;"></span><b>{short_name}</b>: {pts:,.1f} điểm (<b style="color: {color_code};">{pct:.1f}%</b>)</div>', unsafe_allow_html=True)

    # ==================== 5. THƯ MỤC BÁO CÁO ====================
    elif feature == "report_folder":
        col_fold_h1, col_fold_h2 = st.columns([3, 1])
        with col_fold_h1:
            st.header(current_menu_name)
        with col_fold_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_folder"):
                st.cache_data.clear()
                st.rerun()

        reports_df = get_export_reports_db(is_deleted=False)
        if not reports_df.empty:
            with st.form("reports_folder_form"):
                for idx, row in reports_df.iterrows():
                    st.markdown(f'<div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;"><b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📁 File: <b>{row['Tên File']}</b><br>🔗 <a href="{row['Đường Dẫn URL']}" target="_blank">Mở liên kết trực tiếp</a></div>', unsafe_allow_html=True)
                    reports_df.loc[idx, "Chọn"] = st.checkbox(f"Chọn báo cáo STT {row['STT']}", key=f"rep_{row['db_id']}")
                    st.markdown("---")
                if st.form_submit_button("🗑️ Chuyển Các Báo Cáo Đã Chọn Vào Thùng Rác", use_container_width=True):
                    selected_ids = reports_df[reports_df["Chọn"] == True]["db_id"].tolist()
                    if selected_ids:
                        update_export_report_deleted_status(selected_ids, True)
                        st.success("Đã chuyển vào thùng rác!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn báo cáo cần chuyển!")
        else:
            st.info("Thư mục báo cáo đang trống.")

    # ==================== 6. QUẢN LÝ LỖI ====================
    elif feature == "error_management":
        col_err_h1, col_err_h2 = st.columns([3, 1])
        with col_err_h1:
            st.header("6. Quản Lý Lỗi Sản Xuất")
        with col_err_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_error"):
                st.cache_data.clear()
                st.rerun()

        now_vn = datetime.datetime.now(VN_TIMEZONE)
        st.subheader("⚠️ Khai Báo Lỗi Phát Sinh")
        
        with st.form("error_input_form"):
            e_col1, e_col2, e_col3 = st.columns(3)
            with e_col1:
                err_date = st.date_input("Ngày phát sinh", now_vn.date())
            with e_col2:
                err_staff_options = ["--- Chọn nhân sự liên quan ---"] + st.session_state.staff_list
                err_staff = st.selectbox("Nhân sự chịu trách nhiệm/phát hiện", err_staff_options)
            with e_col3:
                err_type_options = ["Sản phẩm hỏng", "Trầy xước/Móp méo", "Sai kích thước", "Sai số lượng", "Khác"]
                err_type = st.selectbox("Phân loại lỗi", err_type_options)

            e_col4, e_col5 = st.columns([1, 2])
            with e_col4:
                err_qty = st.number_input("Số lượng sản phẩm lỗi", min_value=1, value=1, step=1)
            with e_col5:
                err_note = st.text_input("Ghi chú nguyên nhân / Biện pháp xử lý", "")

            submit_err = st.form_submit_button("🚨 Ghi Nhận Lỗi Sản Xuất", use_container_width=True)

            if submit_err:
                if err_staff == "--- Chọn nhân sự liên quan ---":
                    st.error("⚠️ Vui lòng chọn nhân sự liên quan!")
                else:
                    add_error_log_db(err_date, err_staff, err_type, err_qty, err_note)
                    st.success(f"✅ Đã lưu thông tin lỗi cho **{err_staff}**!")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 Danh Sách Lỗi Đã Khai Báo")
        
        err_df = get_error_logs_db()
        if not err_df.empty:
            st.dataframe(err_df.drop(columns=["db_id"]), use_container_width=True, hide_index=True)
            
            if current_user_role == "Admin":
                with st.form("delete_error_form"):
                    st.markdown("##### 🗑️ Xóa Bản Ghi Lỗi")
                    err_ids_to_del = []
                    for idx, r in err_df.iterrows():
                        if st.checkbox(f"Xóa bản ghi STT {r['STT']} - {r['Nhân Sự']} ({r['Ngày']} | {r['Loại Lỗi']}: {r['Số Lượng Lỗi']})", key=f"del_err_{r['db_id']}"):
                            err_ids_to_del.append(r['db_id'])
                            
                    if st.form_submit_button("🗑️ Xóa Các Dòng Đã Chọn", use_container_width=True):
                        if err_ids_to_del:
                            delete_error_log_db(err_ids_to_del)
                            st.success("Đã xóa bản ghi lỗi thành công!")
                            st.rerun()
                        else:
                            st.warning("Vui lòng tích chọn ít nhất một bản ghi cần xóa!")
        else:
            st.info("Chưa có bản ghi lỗi nào trong hệ thống.")

    # ==================== THAM CHIẾU CÔNG VIỆC ====================
    elif feature == "rules":
        col_rules_h1, col_rules_h2 = st.columns([3, 1])
        with col_rules_h1:
            st.header(current_menu_name)
        with col_rules_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_rules"):
                st.cache_data.clear()
                st.rerun()

        if current_user_role != "Admin" and not user_perms["perm_rules"]:
            st.warning("🔒 Bạn không có quyền truy cập hoặc chỉnh sửa định mức công việc!")
            st.dataframe(st.session_state.rules_df, use_container_width=True, hide_index=True)
        else:
            with st.form("rules_form"):
                edited_rules = st.data_editor(st.session_state.rules_df, num_rows="dynamic", use_container_width=True, hide_index=True, disabled=["stt"])
                
                st.markdown("---")
                st.markdown("##### ⚙️ Thao Tác Nâng Cao (Admin)")
                confirm_clear_all_rules = st.checkbox("⚠️ Tôi chắc chắn muốn xóa toàn bộ danh mục công việc trong hệ thống", key="chk_clear_rules")
                
                col_save_rule, col_clear_rule = st.columns(2)
                with col_save_rule:
                    saved_clicked = st.form_submit_button("💾 Lưu Thay Đổi Định Mức", use_container_width=True)
                with col_clear_rule:
                    clear_clicked = st.form_submit_button("🔥 Xóa Toàn Bộ Định Mức", use_container_width=True)

                if saved_clicked:
                    save_rules_df_db(edited_rules)
                    st.rerun()

                if clear_clicked:
                    if confirm_clear_all_rules:
                        if supabase is not None:
                            try:
                                supabase.table("rules").delete().neq("id", 0).execute()
                                st.cache_data.clear()
                                st.success("Đã xóa toàn bộ danh mục định mức công việc thành công!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi khi xóa toàn bộ định mức: {e}")
                    else:
                        st.warning("⚠️ Vui lòng tích chọn hộp xác nhận phía trên trước khi bấm Xóa Toàn Bộ!")

    # ==================== THÙNG RÁC SẢN LƯỢNG ====================
    elif feature == "trash":
        col_trash_h1, col_trash_h2 = st.columns([3, 1])
        with col_trash_h1:
            st.header(current_menu_name)
        with col_trash_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_trash"):
                st.cache_data.clear()
                st.rerun()

        if current_user_role != "Admin":
            st.warning("🔒 Tính năng thùng rác và xóa vĩnh viễn chỉ dành cho Quản trị viên (Admin).")
        else:
            trash_df = get_production_logs_db(is_deleted=True, limit_rows=100)
            
            st.subheader("🗑️ Thùng Rác: Bản Ghi Sản Lượng")
            if not trash_df.empty:
                with st.form("trash_form"):
                    for idx, row in trash_df.iterrows():
                        st.markdown(f'<div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;"><b>STT: {row['STT']}</b> | 📅 {row['Ngày']} | 👤 <b>{row['Nhân Sự']}</b> | 📌 {row['Hạng Mục Công Việc']} ({row['Số Lượng']} {row['Đơn Vị']})</div>', unsafe_allow_html=True)
                        trash_df.loc[idx, "Chọn"] = st.checkbox(f"Chọn sản lượng STT {row['STT']}", key=f"t_{row['db_id']}")
                        
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.form_submit_button("📥 Khôi Phục Đã Chọn", use_container_width=True):
                            ids = trash_df[trash_df["Chọn"] == True]["db_id"].tolist()
                            if ids:
                                update_production_log_deleted_status(ids, False)
                                st.success("Đã khôi phục thành công!")
                                st.rerun()
                    with c2:
                        if st.form_submit_button("🔥 Xóa Vĩnh Viễn Đã Chọn", use_container_width=True):
                            ids = trash_df[trash_df["Chọn"] == True]["db_id"].tolist()
                            if ids:
                                permanent_delete_db(ids)
                                st.success("Đã xóa vĩnh viễn!")
                                st.rerun()
            else:
                st.info("Thùng rác sản lượng trống.")

    # ==================== QUẢN LÝ THƯ MỤC & MENU ====================
    elif feature == "manage_folders":
        col_mf_h1, col_mf_h2 = st.columns([3, 1])
        with col_mf_h1:
            st.header("Quản Lý Thư Mục & Menu")
        with col_mf_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_mf"):
                st.cache_data.clear()
                st.rerun()

        if current_user_role != "Admin":
            st.warning("🔒 Bạn không có quyền truy cập trang quản lý cấu hình hệ thống này.")
        else:
            with st.form("manage_menu_form"):
                current_folder_name = st.session_state.folders[0]["folder_name"] if st.session_state.folders else "📌 Quản Lý Nghiệp Vụ"
                new_folder_name = st.text_input("Tên thư mục", value=current_folder_name)
                current_items = st.session_state.folders[0]["items"] if st.session_state.folders else []
                updated_items = []
                for i_idx, item in enumerate(current_items):
                    new_name = st.text_input(f"Tên hiển thị {i_idx+1}", value=item.get("name", ""), key=f"edit_name_{i_idx}")
                    updated_items.append({"id": item.get("id", f"menu_{i_idx+1}"), "name": new_name})
                    
                if st.form_submit_button("💾 Lưu Thay Đổi", use_container_width=True):
                    new_folders_structure = [{"folder_name": new_folder_name, "items": updated_items}]
                    st.session_state.folders = new_folders_structure
                    save_folders_db(new_folders_structure)
                    st.success("Đã lưu menu thành công!")
                    st.rerun()

    # ==================== CÀI ĐẶT GIAO DIỆN ====================
    elif feature == "settings_ui":
        col_ui_h1, col_ui_h2 = st.columns([3, 1])
        with col_ui_h1:
            st.header("Cài Đặt Giao Diện & Nhân Sự")
        with col_ui_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_ui"):
                st.cache_data.clear()
                st.rerun()

        if current_user_role != "Admin":
            st.warning("🔒 Chỉ Quản trị viên mới được phép cài đặt giao diện và danh sách nhân sự!")
        else:
            with st.form("ui_settings_form"):
                c_col1, c_col2 = st.columns(2)
                with c_col1:
                    picker_bg = st.color_picker("Màu nền ứng dụng", value=st.session_state.bg_color)
                    picker_text = st.color_picker("Màu chữ", value=st.session_state.text_color)
                with c_col2:
                    picker_primary = st.color_picker("Màu chủ đạo", value=st.session_state.primary_color)
                    picker_sidebar = st.color_picker("Màu nền sidebar", value=st.session_state.sidebar_bg)
                    
                slider_opacity = st.slider("Độ mờ sidebar", 0.1, 1.0, float(st.session_state.sidebar_opacity), 0.05)
                bg_file_upload = st.file_uploader("🖼️ Tải lên hình nền ứng dụng", type=["png", "jpg", "jpeg"])
                
                if st.form_submit_button("💾 Lưu Cài Đặt", use_container_width=True):
                    st.session_state.bg_color = picker_bg
                    st.session_state.text_color = picker_text
                    st.session_state.primary_color = picker_primary
                    st.session_state.sidebar_bg = picker_sidebar
                    st.session_state.sidebar_opacity = slider_opacity
                    if bg_file_upload is not None:
                        if compressed_bg := compress_image_to_base64(bg_file_upload, max_size=(1920, 1080), quality=80):
                            st.session_state.bg_image_base64 = compressed_bg
                    save_app_settings_db({
                        "primary_color": st.session_state.primary_color, "bg_color": st.session_state.bg_color,
                        "sidebar_bg": st.session_state.sidebar_bg, "sidebar_opacity": st.session_state.sidebar_opacity,
                        "text_color": st.session_state.text_color, "bg_image_base64": st.session_state.bg_image_base64,
                        "avatar_base64": st.session_state.avatar_base64
                    })
                    st.success("Đã lưu cài đặt giao diện!")
                    st.rerun()

            st.markdown("---")
            st.markdown("### 👥 Quản Lý Danh Sách Nhân Sự")
            with st.form("staff_form"):
                staff_df = get_staff_df_db()
                edited_staff = st.data_editor(staff_df, num_rows="dynamic", use_container_width=True, hide_index=True, disabled=["id"])
                if st.form_submit_button("💾 Lưu Nhân Sự", use_container_width=True):
                    save_staff_list_db(edited_staff)
                    st.session_state.staff_list = get_staff_list_db()
                    st.success("Đã cập nhật danh sách nhân sự!")
                    st.rerun()

    # ==================== 🛡️ QUẢN LÝ TÀI KHOẢN & PHÂN QUYỀN ====================
    elif feature == "manage_roles":
        col_mr_h1, col_mr_h2 = st.columns([3, 1])
        with col_mr_h1:
            st.header("🛡️ Quản Lý Tài Khoản & Phân Quyền Chi Tiết")
        with col_mr_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_mr"):
                st.cache_data.clear()
                st.rerun()

        if current_user_role != "Admin":
            st.warning("🔒 Chỉ Quản trị viên mới có quyền quản lý tài khoản và phân quyền!")
        else:
            st.markdown("Tại đây bạn có thể tạo tài khoản, đổi mật khẩu và cấp quyền trực tiếp cho từng nhân sự:")
            
            try:
                staff_list_names = get_staff_list_db()
                for s_name in staff_list_names:
                    chk = supabase.table("user_accounts").select("*").eq("name", s_name).execute()
                    if not chk.data:
                        supabase.table("user_accounts").insert({
                            "name": s_name,
                            "password_hash": hash_password("123456"),
                            "role": "Staff",
                            "perm_input": False,
                            "perm_report": False,
                            "perm_attendance": True,
                            "perm_rules": False
                        }).execute()

                res_roles = supabase.table("user_accounts").select("*").execute()
                if res_roles.data:
                    roles_df = pd.DataFrame(res_roles.data)
                    
                    with st.form("manage_accounts_form"):
                        edited_roles_df = st.data_editor(
                            roles_df,
                            column_config={
                                "id": "ID",
                                "name": st.column_config.TextColumn("Họ và tên nhân sự", disabled=True),
                                "password_hash": None,
                                "role": st.column_config.SelectboxColumn("Vai trò", options=["Admin", "Manager", "Staff"], required=True),
                                "perm_input": st.column_config.CheckboxColumn("Nhập sản lượng"),
                                "perm_report": st.column_config.CheckboxColumn("Xem báo cáo"),
                                "perm_attendance": st.column_config.CheckboxColumn("Chấm công"),
                                "perm_rules": st.column_config.CheckboxColumn("Sửa định mức")
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        st.markdown("---")
                        st.markdown("##### 🔑 Đổi mật khẩu nhanh cho nhân sự")
                        col_p1, col_p2, col_p3 = st.columns([1.5, 1.5, 1])
                        with col_p1:
                            target_staff_pw = st.selectbox("Chọn nhân sự cần đổi mật khẩu", ["--- Chọn nhân sự ---"] + staff_list_names)
                        with col_p2:
                            new_staff_pass = st.text_input("Mật khẩu mới", type="password", placeholder="Nhập mật khẩu mới...")
                        with col_p3:
                            st.markdown("<br>", unsafe_allow_html=True)
                            btn_update_pw = st.form_submit_button("Cập Nhật Mật Khẩu", use_container_width=True)

                        if btn_update_pw:
                            if target_staff_pw != "--- Chọn nhân sự ---" and new_staff_pass:
                                if len(new_staff_pass) >= 6:
                                    supabase.table("user_accounts").update({
                                        "password_hash": hash_password(new_staff_pass)
                                    }).eq("name", target_staff_pw).execute()
                                    st.success(f"✅ Đã đổi mật khẩu thành công cho **{target_staff_pw}**!")
                                else:
                                    st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
                            else:
                                st.warning("⚠️ Vui lòng chọn nhân sự và nhập mật khẩu mới!")

                        if st.form_submit_button("💾 Lưu Cập Nhật Quyền Hạn Hàng Loạt", use_container_width=True):
                            for _, row in edited_roles_df.iterrows():
                                r_id = row["id"]
                                supabase.table("user_accounts").update({
                                    "role": row["role"],
                                    "perm_input": bool(row["perm_input"]),
                                    "perm_report": bool(row["perm_report"]),
                                    "perm_attendance": bool(row["perm_attendance"]),
                                    "perm_rules": bool(row["perm_rules"])
                                }).eq("id", r_id).execute()
                            st.cache_data.clear()
                            st.success("✅ Đã cập nhật quyền hạn chi tiết thành công!")
                            st.rerun()
                else:
                    st.info("Chưa có tài khoản nhân sự nào trong hệ thống.")
            except Exception as e:
                st.error(f"Lỗi quản lý tài khoản: {e}")

    # ==================== LÀM SẠCH DỮ LIỆU ====================
    elif feature == "clean_data":
        col_cd_h1, col_cd_h2 = st.columns([3, 1])
        with col_cd_h1:
            st.header("Làm Sạch Dữ Liệu")
        with col_cd_h2:
            if st.button("🔄 Làm mới dữ liệu", use_container_width=True, key="btn_refresh_cd"):
                st.cache_data.clear()
                st.rerun()

        if current_user_role != "Admin":
            st.warning("🔒 Tính năng làm sạch dữ liệu chỉ dành cho Admin.")
        else:
            if st.button("🔥 Xóa Toàn Bộ Dữ Liệu Thùng Rác Vĩnh Viễn", use_container_width=True):
                trash_df = get_production_logs_db(is_deleted=True, limit_rows=500)
                if not trash_df.empty:
                    permanent_delete_db(trash_df["db_id"].tolist())
                    st.success("Đã làm sạch thùng rác!")
                    st.rerun()

render_main_content(menu)
