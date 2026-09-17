import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Khởi tạo kết nối Supabase an toàn từ st.secrets
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["SUPABASE_URL"]
        key = st.secrets["supabase"]["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối Supabase: {e}")
        return None

supabase = init_supabase()

@st.cache_data(ttl=60)
def get_staff_list_db():
    if not supabase: return []
    try:
        res = supabase.table("staff").select("name").execute()
        return [row["name"] for row in res.data] if res.data else []
    except: return []

@st.cache_data(ttl=60)
def get_staff_df_db():
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("staff").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def get_rules_df_db():
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("rules").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except: return pd.DataFrame()

@st.cache_data(ttl=30)
def get_production_logs_db(is_deleted=False, limit_rows=50):
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("production_logs").select("*").eq("is_deleted", is_deleted).order("id", desc=True).limit(limit_rows).execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)
        if "id" in df.columns:
            df.rename(columns={"id": "db_id"}, inplace=True)
            df.insert(0, "STT", range(len(df), 0, -1))
        return df
    except: return pd.DataFrame()

def get_production_logs_by_date_range(start_date, end_date):
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("production_logs").select("*").eq("is_deleted", False).gte("ngay", str(start_date)).lte("ngay", str(end_date)).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_production_log_db(ngay, gio, nhan_su, hang_muc, hinh_anh, don_vi, so_luong, he_so, tong_diem, ghi_chu):
    if not supabase: return
    try:
        supabase.table("production_logs").insert({
            "ngay": ngay, "gio": gio, "nhan_su": nhan_su, "hang_muc_cong_viec": hang_muc,
            "hinh_anh": hinh_anh, "don_vi": don_vi, "so_luong": so_luong, "he_so": he_so,
            "tong_diem": tong_diem, "ghi_chu": ghi_chu, "is_deleted": False
        }).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi ghi dữ liệu sản lượng: {e}")

def update_production_log_deleted_status(ids, is_deleted):
    if not supabase: return
    try:
        for db_id in ids:
            supabase.table("production_logs").update({"is_deleted": is_deleted}).eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi cập nhật trạng thái xóa: {e}")

@st.cache_data(ttl=30)
def get_attendance_db():
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("attendance").select("*").order("id", desc=True).limit(50).execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)
        if "id" in df.columns:
            df.rename(columns={"id": "db_id"}, inplace=True)
            df.insert(0, "STT", range(len(df), 0, -1))
        return df
    except: return pd.DataFrame()

def add_attendance_db(ngay, nhan_su, gio_vao_ca, gio_ra_ca, so_phut_lam_viec, ghi_chu):
    if not supabase: return
    try:
        supabase.table("attendance").insert({
            "ngay": str(ngay), "nhan_su": nhan_su, "gio_vao_ca": gio_vao_ca,
            "gio_ra_ca": gio_ra_ca, "so_phut_lam_viec": so_phut_lam_viec, "ghi_chu": ghi_chu
        }).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi chấm công: {e}")

# Hàm bổ sung để khắc phục triệt để lỗi thiếu hàm chấm công
def delete_attendance_db(record_id):
    if not supabase: return
    try:
        supabase.table("attendance").delete().eq("id", record_id).execute()
        st.cache_data.clear()
    except Exception as e:
        print(f"Error deleting attendance: {e}")

@st.cache_data(ttl=30)
def get_export_reports_db(is_deleted=False):
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("export_reports").select("*").eq("is_deleted", is_deleted).order("id", desc=True).execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)
        if "id" in df.columns:
            df.rename(columns={"id": "db_id"}, inplace=True)
            df.insert(0, "STT", range(len(df), 0, -1))
        return df
    except: return pd.DataFrame()

def update_export_report_deleted_status(ids, is_deleted):
    if not supabase: return
    try:
        for db_id in ids:
            supabase.table("export_reports").update({"is_deleted": is_deleted}).eq("id", db_id).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi cập nhật thư mục báo cáo: {e}")
