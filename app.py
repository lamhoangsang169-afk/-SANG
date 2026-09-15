import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import base64

# Import từ các module đã tách
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
                    except Exception:
                        st.error("❌ Đăng nhập thất bại: Vui lòng kiểm tra lại thông tin.")
    st.stop()

# ==================== CÁC HÀM CRUD BỔ SUNG TRONG APP ====================
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
    if supabase is None:
        return
    try:
        res_old = supabase.table("rules").select("id, hang_muc, he_so_diem").execute()
        old_rules_map = {row["id"]: {"hang_muc": row["hang_muc"], "he_so_diem": row["he_so_diem"]} for row in res_old.data} if res_old.data else {}
        old_ids = list(old_rules_map.keys())
        
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
                old_info = old_rules_map.get(rid, {"hang_muc": "", "he_so_diem": 1.0})
                old_hang_muc = old_info["hang_muc"]
                old_he_so = old_info["he_so_diem"]
                
                supabase.table("rules").update(payload).eq("id", rid).execute()
                current_ids_in_editor.append(rid)
                
                if old_hang_muc and old_hang_muc != new_hang_muc:
                    supabase.table("production_logs").update({
                        "hang_muc_cong_viec": new_hang_muc
                    }).eq("hang_muc_cong_viec", old_hang_muc).eq("is_deleted", False).execute()
                
                target_hang_muc_name = new_hang_muc if new_hang_muc else old_hang_muc
                
                res_logs = supabase.table("production_logs").select("id, so_luong").eq("hang_muc_cong_viec", target_hang_muc_name).eq("is_deleted", False).execute()
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
        st.success("Đã đồng bộ định mức và cập nhật lại toàn bộ điểm số cũ thành công!")
    except Exception as e:
        st.error(f"Lỗi khi đồng bộ định mức: {e}")

def save_app_settings_db(settings_dict):
    if supabase is None:
        return
    try:
        payload = {"id": 1, **settings_dict}
        supabase.table("app_settings").upsert(payload).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi lưu cấu hình: {e}")

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
    if supabase is None:
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
        st.success("Đã lưu thông tin báo cáo thành công!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi khi lưu báo cáo: {e}")

@st.cache_data(ttl=150, show_spinner=False)
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
    if supabase is None:
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
    .avatar-popover-wrapper {{ position: absolute; bottom: 2px; right: 10px; z-index: 9999999; }}
    .avatar-popover-wrapper [data-testid="stPopover"] button {{ background-color: #ffffff !important; border: 2px solid {st.session_state.primary_color} !important; border-radius: 50% !important; width: 32px !important; height: 32px !important; padding: 0px !important; display: flex !important; align-items: center !important; justify-content: center !important; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
    .avatar-popover-wrapper [data-testid="stPopover"] button p {{ display: none !important; }}
    .avatar-popover-wrapper [data-testid="stPopover"] button::after {{ content: "⋮"; font-size: 16px; font-weight: bold; color: #333333; line-height: 1; }}
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
    st.markdown(f"<small>👤 <b>{st.session_state.user_email}</b></small>", unsafe_allow_html=True)
    if st.button("🚪 Đăng Xuất", use_container_width=True):
        if supabase is not None:
            try: supabase.auth.sign_out()
            except Exception: pass
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        if "auth_user" in st.query_params: del st.query_params["auth_user"]
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

    st.markdown("---")
    if is_supabase_connected:
        st.markdown('<div style="background: rgba(16, 185, 129, 0.15); padding: 8px 12px; border-radius: 6px; border: 1px solid #10b981; text-align: center; font-size: 0.85rem; font-weight: bold; color: #047857; margin-bottom: 6px;">🟢 Đã kết nối Supabase</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background: rgba(239, 68, 68, 0.15); padding: 8px 12px; border-radius: 6px; border: 1px solid #ef4444; text-align: center; font-size: 0.85rem; font-weight: bold; color: #b91c1c; margin-bottom: 6px;">🔴 Chưa kết nối Supabase</div>', unsafe_allow_html=True)

    current_loaded_df = get_production_logs_db(is_deleted=False, limit_rows=200)
    current_shown_count = len(current_loaded_df) if not current_loaded_df.empty else 0
    total_db_count = get_total_production_count_db()

    st.markdown(f'<div style="background: rgba(59, 130, 246, 0.12); padding: 8px 12px; border-radius: 6px; border: 1px solid #3b82f6; text-align: center; font-size: 0.85rem; font-weight: bold; color: #1d4ed8;">📊 Tải tối đa: <span style="color: #ff4b4b;">{current_shown_count}</span> / {total_db_count} bản ghi</div>', unsafe_allow_html=True)
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

# ==================== KHU VỰC NỘI DUNG TỐI ƯU BẰNG ST.FRAGMENT ====================
@st.fragment
def render_main_content(current_menu_name):
    feature = get_feature_type(current_menu_name)

    # ==================== 1. NHẬP SẢN LƯỢNG ====================
    if feature == "input_production":
        now_vn = datetime.datetime.now(VN_TIMEZONE)
        today_str = str(now_vn.date())
        
        att_df_check = get_attendance_db()
        checked_in_set = set()
        if not att_df_check.empty:
            checked_in_set = set(att_df_check[att_df_check["Giờ Ra Ca"] == "Chưa kết thúc"]["Nhân Sự"].tolist())

        active_staff = [s for s in st.session_state.staff_list if s in checked_in_set]

        st.subheader(f"{current_menu_name} ({today_str})")

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
                        st.session_state["form_msg"] = ("error", "⚠️ Bắt buộc phải nhập nội dung vào phần Ghi chú khi chọn 'Công việc phát sinh ( TP_xác nhận )'!")

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
        st.subheader("Danh Sách Sản Lượng & Hình Ảnh")
        
        input_df = get_production_logs_db(is_deleted=False, limit_rows=500)
        if not input_df.empty:
            # --- THU GỌN KÍCH THƯỚC CÁC Ô LỌC BẰNG CÁCH ĐIỀU CHỈNH TỶ LỆ CỘT ---
            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([0.8, 1.2, 0.9, 0.9, 0.8])
            
            with f_col1:
                all_dates = ["Tất cả"] + sorted(input_df["Ngày"].unique().tolist())
                default_index = all_dates.index(today_str) if today_str in all_dates else 0
                filter_date = st.selectbox("Lọc theo Ngày", all_dates, index=default_index)
                
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
            if filter_date != "Tất cả": 
                temp_filtered_df = temp_filtered_df[temp_filtered_df["Ngày"] == filter_date]
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
            total_pages = (total_rows - 1) // rows_per_page + 1

            with f_col5:
                current_page = st.number_input(f"Trang hiển thị ({total_pages} tr | {total_rows} bản ghi)", min_value=1, max_value=max(total_pages, 1), value=1, step=1, key="pagination_page_num")

            start_idx = (current_page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            paginated_df = filtered_df.iloc[start_idx:end_idx]

            if filter_task != "Tất cả":
                total_qty_task = filtered_df["Số Lượng"].sum() if not filtered_df.empty else 0
                unit_name = filtered_df["Đơn Vị"].values[0] if not filtered_df.empty and "Đơn Vị" in filtered_df.columns else "Cái"
                st.markdown(f'<div style="background: rgba(59, 130, 246, 0.15); padding: 12px 18px; border-radius: 8px; border: 2px solid #3b82f6; margin-bottom: 15px; font-size: 1rem; font-weight: bold; text-align: center;">📊 Tổng số lượng của hạng mục <span style="color: #ff4b4b;">"{filter_task}"</span>: <span style="font-size: 1.2rem; color: #1d4ed8;">{total_qty_task:,.0f}</span> {unit_name}</div>', unsafe_allow_html=True)

            if not paginated_df.empty:
                col_del_all_1, col_del_all_2 = st.columns([2.5, 1.5])
                with col_del_all_2:
                    del_c1, del_c2 = st.columns([1, 1])
                    with del_c1: confirm_delete_all = st.checkbox("Xác nhận xóa tất cả trang này", key="chk_confirm_delete_all")
                    with del_c2:
                        if st.button("🗑️ Xóa tất cả trang này", use_container_width=True, type="primary"):
                            if confirm_delete_all:
                                all_paginated_ids = paginated_df["db_id"].tolist()
                                if all_paginated_ids:
                                    update_production_log_deleted_status(all_paginated_ids, True)
                                    st.success("Đã chuyển toàn bộ bản ghi đang hiển thị ở trang này vào thùng rác!")
                                    st.rerun()
                            else:
                                st.warning("⚠️ Vui lòng tích chọn xác nhận trước khi bấm!")

                selected_ids_to_delete = []
                for idx, row in paginated_df.iterrows():
                    row_c1, row_c2 = st.columns([4, 1])
                    with row_c1:
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 4px; font-size: 0.85rem;">
                            <b>STT: {row['STT']}</b> &nbsp;|&nbsp; 📅 {row['Ngày']} ⏰ {row['Thời Gian']} &nbsp;|&nbsp; 👤 <b>{row['Nhân Sự']}</b><br>
                            📌 {row['Hạng Mục Công Việc']} &nbsp;|&nbsp; 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ <b>{row['Tổng Điểm']}</b> điểm)<br>
                            💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.checkbox(f"Chọn xóa bản ghi STT {row['STT']}", key=f"chk_{row['db_id']}"):
                            selected_ids_to_delete.append(row['db_id'])
                            
                    with row_c2:
                        img_url_val = row.get("Hình Ảnh", "")
                        if img_url_val and isinstance(img_url_val, str):
                            urls = [u.strip() for u in img_url_val.split(",") if u.strip()]
                            if urls:
                                sub_cols = st.columns(min(len(urls), 4), gap="small")
                                for i, u in enumerate(urls):
                                    with sub_cols[i]:
                                        with st.popover("🔍", help="Xem ảnh lớn"): st.image(u, use_container_width=True)
                                        st.image(u, width=40)
                        else:
                            st.markdown("<small style='color: gray;'>Không ảnh</small>", unsafe_allow_html=True)

                    st.markdown("---")
                
                if st.button("🗑️ Chuyển Các Dòng Đã Chọn Vào Thùng Rác", use_container_width=True, type="secondary"):
                    if selected_ids_to_delete:
                        update_production_log_deleted_status(selected_ids_to_delete, True)
                        st.success("Đã chuyển các dòng đã chọn vào thùng rác!")
                        st.rerun()
                    else:
                        st.warning("Vui lòng tích chọn ít nhất một dòng cần xóa!")
            else:
                st.info("Không tìm thấy bản ghi nào khớp bộ lọc.")
        else:
            st.info("Chưa có dữ liệu sản lượng.")

    # ==================== CHẤM CÔNG CA LÀM VIỆC ====================
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
            with st.form("delete_att_form"):
                st.markdown("##### 🗑️ Xóa Bản Ghi Chấm Công Lỗi")
                
                st.markdown("---")
                confirm_del_all_att = st.checkbox("⚠️ Tôi chắc chắn muốn xóa TOÀN BỘ lịch sử chấm công", key="chk_confirm_del_all_att")
                
                att_col1, att_col2 = st.columns(2)
                with att_col1:
                    submitted_delete_selected = st.form_submit_button("Xóa Các Dòng Đã Chọn", use_container_width=True)
                with att_col2:
                    submitted_delete_all = st.form_submit_button("🔥 Xóa Toàn Bộ Lịch Sử Chấm Công", use_container_width=True, type="primary")

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
        st.header(current_menu_name)
        
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
                comparison_df["Tỷ_Lệ_Thời_Gian"] = comparison_df["Tổng Phút Làm Việc"].apply(lambda x: (x / total_minutes_all) if total_minutes_all > 0 else 0)
                comparison_df["Tỷ_Lệ_Đóng_Góp"] = comparison_df["Tổng_Điểm"].apply(lambda x: (x / total_pts_all) if (total_pts_all := comparison_df["Tổng_Điểm"].sum()) > 0 else 0)
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

            chart_col1, chart_col2 = st.columns([0.45, 1.35])
            with chart_col1:
                fig_plotly = px.pie(summary, names="Nhân Sự", values="Tổng_Điểm", hole=0, color_discrete_sequence=st.session_state.chart_colors)
                fig_plotly.update_traces(textposition='inside', textinfo='percent', textfont=dict(size=20, color='white', family='Arial Black'), pull=[0.03] * len(summary))
                fig_plotly.update_layout(margin=dict(t=30, b=30, l=30, r=30), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=320)
                st.plotly_chart(fig_plotly, use_container_width=True)
                
            with chart_col2:
                st.markdown("### 📌 Chi Tiết Điểm Số & Tỷ Lệ")
                for idx, row in summary.iterrows():
                    staff_name = row["Nhân Sự"]
                    short_name = staff_name.split()[-1] if len(staff_name.split()) > 1 else staff_name
                    pts, pct = row["Tổng_Điểm"], row["Tỷ_Lệ_Đóng_Góp"] * 100
                    color_code = st.session_state.chart_colors[idx % len(st.session_state.chart_colors)]
                    st.markdown(f'<div style="background-color: #f8fafc; padding: 6px 10px; border-radius: 6px; margin-bottom: 6px; border-left: 4px solid {color_code}; border: 1px solid #e2e8f0; font-size: 0.85rem;"><span style="display:inline-block; width:7px; height:7px; background-color:{color_code}; border-radius:2px; margin-right:4px;"></span><b>{short_name}</b>: {pts:,.1f} điểm (<b style="color: {color_code};">{pct:.1f}%</b>)</div>', unsafe_allow_html=True)

    # ==================== 5. THƯ MỤC BÁO CÁO ====================
    elif feature == "report_folder":
        st.header(current_menu_name)
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

    # ==================== THAM CHIẾU CÔNG VIỆC ====================
    elif feature == "rules":
        st.header(current_menu_name)
        with st.form("rules_form"):
            edited_rules = st.data_editor(st.session_state.rules_df, num_rows="dynamic", use_container_width=True, hide_index=True, disabled=["stt"])
            
            st.markdown("---")
            st.markdown("##### ⚙️ Thao Tác Nâng Cao")
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
        st.header(current_menu_name)
        trash_df = get_production_logs_db(is_deleted=True, limit_rows=100)
        trash_reports_df = get_export_reports_db(is_deleted=True)
        
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
        st.header("Quản Lý Thư Mục & Menu")
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
        st.header("Cài Đặt Giao Diện & Nhân Sự")
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

    # ==================== LÀM SẠCH DỮ LIỆU ====================
    elif feature == "clean_data":
        st.header("Làm Sạch Dữ Liệu")
        if st.button("🔥 Xóa Toàn Bộ Dữ Liệu Thùng Rác Vĩnh Viễn", use_container_width=True):
            trash_df = get_production_logs_db(is_deleted=True, limit_rows=500)
            if not trash_df.empty:
                permanent_delete_db(trash_df["db_id"].tolist())
                st.success("Đã làm sạch thùng rác!")
                st.rerun()

# Gọi fragment chính để hiển thị mượt mà không load lại sidebar
render_main_content(menu)
