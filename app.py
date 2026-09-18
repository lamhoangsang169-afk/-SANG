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

def calculate_exact_minutes(ngay_vao, gio_vao, ngay_ra, gio_ra):
    try:
        dt_in = datetime.datetime.strptime(f"{ngay_vao} {gio_vao}", "%Y-%m-%d %H:%M:%S")
        dt_out = datetime.datetime.strptime(f"{ngay_ra} {gio_ra}", "%Y-%m-%d %H:%M:%S")
        diff = dt_out - dt_in
        return max(0, int(diff.total_seconds() // 60))
    except Exception:
        return 0

# ==================== CÁC HÀM TRUY XUẤT DATABASE ====================
@st.cache_data(ttl=60, show_spinner=False)
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
    return ["Nguyễn Văn A", "Trần Thị B"]

@st.cache_data(ttl=60, show_spinner=False)
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
    return pd.DataFrame([
        {"id": 1, "stt": 1, "Hạng Mục Công Việc": "Sản xuất chung", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": ""}
    ])

@st.cache_data(ttl=10, show_spinner=False)
def get_production_logs_db(is_deleted=False, limit_rows=500):
    if supabase is None: return pd.DataFrame()
    try:
        # Lấy toàn bộ dữ liệu không giới hạn cứng theo ngày
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
            return df
    except Exception: pass
    return pd.DataFrame()

@st.cache_data(ttl=10, show_spinner=False)
def get_attendance_db():
    if supabase is None: return pd.DataFrame()
    try:
        res = supabase.table("attendance").select("*").order("id", desc=True).limit(200).execute()
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
    except Exception as e:
        st.error(f"Lỗi ghi dữ liệu: {e}")

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

# ==================== ĐĂNG NHẬP SESSION ====================
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

# ==================== TRANG CHÍNH UNG DỤNG ====================
st.session_state.staff_list = get_staff_list_db()
st.session_state.rules_df = get_rules_df_db()
if "current_menu" not in st.session_state: st.session_state.current_menu = "1. Nhập Sản Lượng"

with st.sidebar:
    st.markdown("### 📌 QUẢN LÝ NGHIỆP VỤ")
    st.markdown(f"👤 Đang đăng nhập: **{st.session_state.user_identifier}**")
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_identifier = ""
        if "auth_user" in st.query_params: del st.query_params["auth_user"]
        st.rerun()
    st.markdown("---")
    
    menus = ["1. Nhập Sản Lượng", "2. Chấm Công Ca Làm Việc", "3. Báo Cáo Thống Kê", "4. Tham Chiếu Định Mức"]
    for m in menus:
        if st.button(m, use_container_width=True, key=f"btn_{m}"):
            st.session_state.current_menu = m
            st.rerun()
            
    st.markdown("---")
    if st.button("🔄 Làm mới dữ liệu", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

menu = st.session_state.current_menu

# ==================== 1. NHẬP SẢN LƯỢNG ====================
if menu == "1. Nhập Sản Lượng":
    now_vn = datetime.datetime.now(VN_TIMEZONE)
    today_str = str(now_vn.date())
    st.header(f"📋 Nhập Sản Lượng ({today_str})")

    # Form nhập sản lượng
    with st.expander("➕ Form Báo Cáo Sản Lượng Mới", expanded=True):
        with st.form("entry_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1: ngay = st.date_input("Ngày làm việc", now_vn.date())
            with f_col2: nhan_su = st.selectbox("Nhân sự thực hiện", st.session_state.staff_list)
            with f_col3:
                raw_tasks = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else ["Sản xuất chung"]
                hang_muc = st.selectbox("Hạng mục công việc", raw_tasks)
                
            record_images = st.file_uploader("Tải ảnh đính kèm (Tối đa 4 ảnh)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            f_col4, f_col5 = st.columns(2)
            with f_col4: so_luong = st.number_input("Số lượng thực tế", min_value=1, value=10, step=1)
            with f_col5: ghi_chu = st.text_input("Ghi chú", "")
            
            submitted = st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True)
            if submitted:
                row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
                he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
                don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
                tong_diem = so_luong * he_so
                img_urls = upload_multiple_images_to_storage(record_images) if record_images else ""
                current_time_str = datetime.datetime.now(VN_TIMEZONE).strftime("%H:%M:%S")
                
                add_production_log_db(str(ngay), current_time_str, nhan_su, hang_muc, img_urls, don_vi, so_luong, he_so, tong_diem, ghi_chu)
                st.success(f"✅ Ghi nhận thành công cho {nhan_su}!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Danh Sách Nhật Ký Sản Lượng")
    
    input_df = get_production_logs_db(is_deleted=False, limit_rows=500)
    if not input_df.empty:
        st.dataframe(input_df, use_container_width=True, hide_index=True)
        
        # Hiển thị thẻ chi tiết ảnh
        st.markdown("##### 🖼️ Hình Ảnh Đính Kèm")
        for idx, row in input_df.iterrows():
            img_url_val = str(row.get("Hình Ảnh", "")).strip()
            if img_url_val and img_url_val not in ["0", "nan", "None", ""]:
                urls = [u.strip() for u in img_url_val.split(",") if u.strip().startswith("http")]
                if urls:
                    st.markdown(f"**STT {row['STT']} - {row['Nhân Sự']} - {row['Hạng Mục Công Việc']} ({row['Ngày']}):**")
                    cols = st.columns(min(len(urls), 4))
                    for i, u in enumerate(urls):
                        with cols[i]:
                            st.image(u, width=120)
    else:
        st.info("Chưa có dữ liệu sản lượng trong hệ thống. Bạn hãy nhập sản lượng ở form trên để kiểm tra.")

# ==================== 2. CHẤM CÔNG CA LÀM VIỆC ====================
elif menu == "2. Chấm Công Ca Làm Việc":
    st.header("⏱️ Chấm Công Ca Làm Việc")
    now_vn = datetime.datetime.now(VN_TIMEZONE)
    
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
            add_attendance_db(str(att_date), att_staff, time_str, "Chưa kết thúc", 0, att_note)
            st.success(f"✅ Check-in thành công cho {att_staff}!")
            st.rerun()
            
        if check_out:
            if supabase is not None:
                res_check = supabase.table("attendance").select("*").eq("nhan_su", att_staff).eq("gio_ra_ca", "Chưa kết thúc").execute()
                if res_check and res_check.data:
                    target_row = res_check.data[0]
                    so_phut = calculate_exact_minutes(target_row["ngay"], target_row.get("gio_vao_ca", "00:00:00"), str(att_date), time_str)
                    supabase.table("attendance").update({"gio_ra_ca": time_str, "so_phut_lam_viec": int(so_phut)}).eq("id", target_row["id"]).execute()
                    st.cache_data.clear()
                    st.success(f"✅ Check-out thành công cho {att_staff}!")
                    st.rerun()

    st.markdown("---")
    st.subheader("📋 Lịch Sử Chấm Công")
    att_df = get_attendance_db()
    if not att_df.empty:
        st.dataframe(att_df.drop(columns=["db_id"], errors="ignore"), use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu chấm công.")

# ==================== 3. BÁO CÁO THỐNG KÊ ====================
elif menu == "3. Báo Cáo Thống Kê":
    st.header("📊 Báo Cáo Thống Kê")
    col_date1, col_date2 = st.columns(2)
    with col_date1: report_start_date = st.date_input("Từ ngày", datetime.date.today().replace(day=1))
    with col_date2: report_end_date = st.date_input("Đến ngày", datetime.date.today())

    input_df = get_production_logs_by_date_range(report_start_date, report_end_date)
    
    if not input_df.empty:
        summary = input_df.groupby("Nhân Sự").agg(Tổng_Số_Lượng=("Số Lượng", "sum"), Tổng_Điểm=("Tổng Điểm", "sum")).reset_index()
        st.subheader("Bảng Tổng Kết Theo Nhân Sự")
        st.dataframe(summary, use_container_width=True, hide_index=True)
        
        chart_col1, chart_col2 = st.columns([1, 1])
        with chart_col1:
            fig_plotly = px.pie(summary, names="Nhân Sự", values="Tổng_Điểm", title="Tỷ Lệ Điểm Sản Lượng")
            st.plotly_chart(fig_plotly, use_container_width=True)
        with chart_col2:
            fig_bar = px.bar(summary, x="Nhân Sự", y="Tổng_Số_Lượng", title="Tổng Số Lượng Hoàn Thành")
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu báo cáo trong khoảng thời gian này.")

# ==================== 4. THAM CHIẾU ĐỊNH MỨC ====================
elif menu == "4. Tham Chiếu Định Mức":
    st.header("📋 Tham Chiếu Định Mức")
    st.dataframe(st.session_state.rules_df, use_container_width=True, hide_index=True)
