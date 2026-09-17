import streamlit as st
import datetime
from utils import VN_TIMEZONE, calculate_exact_minutes
from database import get_attendance_db, add_attendance_db, delete_attendance_db, get_staff_list_db, supabase

st.set_page_config(page_title="Chấm Công Ca Làm Việc", page_icon="⏱️", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ trước!")
    st.stop()

st.subheader("⏱️ Chấm Công Ca Làm Việc")
now_vn = datetime.datetime.now(VN_TIMEZONE)
staff_list = get_staff_list_db()
att_df = get_attendance_db()

with st.form("attendance_form"):
    f1, f2, f3 = st.columns(3)
    with f1: att_date = st.date_input("Ngày", now_vn.date())
    with f2: att_staff = st.selectbox("Nhân sự", ["--- Chọn ---"] + staff_list)
    with f3: att_note = st.text_input("Ghi chú", "")
    
    b1, b2 = st.columns(2)
    with b1: check_in = st.form_submit_button("🟢 Check-in (Vào ca)", use_container_width=True)
    with b2: check_out = st.form_submit_button("🔴 Check-out (Kết thúc)", use_container_width=True)
    
    time_str = now_vn.strftime("%H:%M:%S")
    if check_in and att_staff != "--- Chọn ---":
        add_attendance_db(att_date, att_staff, time_str, "Chưa kết thúc", 0, att_note)
        st.success(f"✅ Check-in thành công cho **{att_staff}**!")
        st.rerun()
    elif check_out and att_staff != "--- Chọn ---" and supabase:
        res = supabase.table("attendance").select("*").eq("nhan_su", att_staff).eq("gio_ra_ca", "Chưa kết thúc").execute()
        if res.data:
            target = res.data[0]
            minutes = calculate_exact_minutes(target["ngay"], target["gio_vao_ca"], str(att_date), time_str)
            supabase.table("attendance").update({"gio_ra_ca": time_str, "so_phut_lam_viec": int(minutes)}).eq("id", target["id"]).execute()
            st.success(f"✅ Check-out thành công ({minutes} phút)!")
            st.rerun()

st.markdown("---")
st.subheader("📋 Lịch Sử Chấm Công")
if not att_df.empty:
    st.dataframe(att_df.drop(columns=["db_id"]), use_container_width=True, hide_index=True)
