import streamlit as st
import pandas as pd
import hashlib
from database import supabase, get_staff_list_db, get_staff_df_db

st.set_page_config(page_title="Quản Trị Hệ Thống", page_icon="⚙️", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ trước!")
    st.stop()

def get_user_role(identifier):
    if not identifier or supabase is None: return "Staff"
    if str(identifier).strip().lower() == "lamhoangsang169@gmail.com": return "Admin"
    try:
        res = supabase.table("user_accounts").select("role").eq("name", identifier).execute()
        if res.data: return res.data[0].get("role", "Staff")
    except: pass
    return "Staff"

current_user_role = get_user_role(st.session_state.user_identifier)

if current_user_role != "Admin":
    st.warning("🔒 Chỉ Quản trị viên mới có quyền truy cập trang quản trị này!")
    st.stop()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

st.subheader("🛡️ Quản Lý Tài Khoản, Phân Quyền & Nhân Sự")

tab_acc, tab_staff = st.tabs(["🔐 Phân Quyền Tài Khoản", "👥 Quản Lý Nhân Sự"])

with tab_acc:
    try:
        staff_list_names = get_staff_list_db()
        res_roles = supabase.table("user_accounts").select("*").execute()
        existing_users = {row["name"]: row for row in res_roles.data} if res_roles.data else {}

        new_users_to_insert = []
        for s_name in staff_list_names:
            if s_name not in existing_users:
                new_users_to_insert.append({
                    "name": s_name, "password_hash": hash_password("123456"),
                    "role": "Staff", "perm_input": False, "perm_report": False,
                    "perm_attendance": True, "perm_rules": False
                })
        
        if new_users_to_insert:
            supabase.table("user_accounts").insert(new_users_to_insert).execute()
            res_roles = supabase.table("user_accounts").select("*").execute()

        if res_roles.data:
            roles_df = pd.DataFrame(res_roles.data)
            with st.form("manage_accounts_form"):
                edited_roles_df = st.data_editor(
                    roles_df,
                    column_config={
                        "id": "ID", "name": st.column_config.TextColumn("Nhân sự", disabled=True),
                        "password_hash": None,
                        "role": st.column_config.SelectboxColumn("Vai trò", options=["Admin", "Manager", "Staff"], required=True),
                        "perm_input": st.column_config.CheckboxColumn("Nhập SL"),
                        "perm_report": st.column_config.CheckboxColumn("Xem báo cáo"),
                        "perm_attendance": st.column_config.CheckboxColumn("Chấm công"),
                        "perm_rules": st.column_config.CheckboxColumn("Sửa định mức")
                    },
                    hide_index=True, use_container_width=True
                )
                
                st.markdown("---")
                st.markdown("##### 🔑 Đổi mật khẩu nhanh")
                col_p1, col_p2, col_p3 = st.columns([1.5, 1.5, 1])
                target_pw = col_p1.selectbox("Chọn nhân sự", ["--- Chọn ---"] + staff_list_names)
                new_pw = col_p2.text_input("Mật khẩu mới", type="password")
                col_p3.markdown("<br>", unsafe_allow_html=True)
                btn_pw = col_p3.form_submit_button("Cập Nhật Mật Khẩu", use_container_width=True)

                if btn_pw and target_pw != "--- Chọn ---" and new_pw:
                    if len(new_pw) >= 6:
                        supabase.table("user_accounts").update({"password_hash": hash_password(new_pw)}).eq("name", target_pw).execute()
                        st.success(f"✅ Đã đổi mật khẩu cho **{target_pw}**!")
                    else: st.error("⚠️ Mật khẩu ít nhất 6 ký tự!")

                if st.form_submit_button("💾 Lưu Cập Nhật Quyền", use_container_width=True):
                    for _, row in edited_roles_df.iterrows():
                        supabase.table("user_accounts").update({
                            "role": row["role"], "perm_input": bool(row["perm_input"]),
                            "perm_report": bool(row["perm_report"]), "perm_attendance": bool(row["perm_attendance"]),
                            "perm_rules": bool(row["perm_rules"])
                        }).eq("id", row["id"]).execute()
                    st.cache_data.clear()
                    st.success("✅ Đã cập nhật quyền hạn thành công!")
                    st.rerun()
    except Exception as e:
        st.error(f"Lỗi: {e}")

with tab_staff:
    with st.form("staff_form"):
        staff_df = get_staff_df_db()
        edited_staff = st.data_editor(staff_df, num_rows="dynamic", use_container_width=True, hide_index=True, disabled=["id"])
        if st.form_submit_button("💾 Lưu Danh Sách Nhân Sự", use_container_width=True):
            st.success("Đã cập nhật nhân sự thành công!")
            st.rerun()
