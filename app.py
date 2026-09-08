import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io
import base64
import json
import os

st.set_page_config(page_title="Phần Mềm Chấm Điểm Sản Lượng", page_icon="📊", layout="wide")

STORAGE_FILE = "app_storage.json"

master_rules = [
    {"STT": 1, "Hạng Mục Công Việc": "Lấy hộp có sẵn", "Đơn Vị": "Cái", "Hệ Số Điểm": 0.5, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 2, "Hạng Mục Công Việc": "Lấy hộp mới", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 3, "Hạng Mục Công Việc": "Lấy đế có sẵn", "Đơn Vị": "Cái", "Hệ Số Điểm": 0.5, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 4, "Hạng Mục Công Việc": "Lấy đế mới", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 5, "Hạng Mục Công Việc": "Lấy phụ kiện có sẵn", "Đơn Vị": "Cái", "Hệ Số Điểm": 0.5, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 6, "Hạng Mục Công Việc": "Lấy phụ kiện mới", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 7, "Hạng Mục Công Việc": "Lấy mặt có sẵn", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 8, "Hạng Mục Công Việc": "Lấy mặt mới", "Đơn Vị": "Cái", "Hệ Số Điểm": 2.0, "Ghi Chú": "Kho / Vận hành"},
    {"STT": 9, "Hạng Mục Công Việc": "Vệ sinh + kiểm tra ,+ cắt hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.5, "Ghi Chú": "Kiểm tra chất lượng"},
    {"STT": 10, "Hạng Mục Công Việc": "Kiểm tra BTP + cắt hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kiểm tra chất lượng"},
    {"STT": 11, "Hạng Mục Công Việc": "Kiểm tra hộp + cất hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Kiểm tra chất lượng"},
    {"STT": 12, "Hạng Mục Công Việc": "Kiểm tra pha lê + cất hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 2.0, "Ghi Chú": "Kiểm tra chất lượng"},
    {"STT": 13, "Hạng Mục Công Việc": "Giao hàng shiper", "Đơn Vị": "Cái", "Hệ Số Điểm": 1.0, "Ghi Chú": "Vận chuyển / Giao nhận"},
    {"STT": 14, "Hạng Mục Công Việc": "tự đi giao hàng", "Đơn Vị": "Cái", "Hệ Số Điểm": 2.0, "Ghi Chú": "Vận chuyển / Giao nhận"},
    {"STT": 15, "Hạng Mục Công Việc": "Nhận hàng gia công ngoài", "Đơn Vị": "Cái", "Hệ Số Điểm": 0.1, "Ghi Chú": "Vận chuyển / Giao nhận"},
    {"STT": 16, "Hạng Mục Công Việc": "Cắp pha lê tấm", "Đơn Vị": "Cái", "Hệ Số Điểm": 2.0, "Ghi Chú": "Sản xuất / Gia công"},
]

default_staff_list = ["Đức", "Bảo", "Tiến"]

def load_data():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except:
            pass
    return {}

def save_data():
    data = {
        "rules_df": st.session_state.rules_df.to_dict(orient="records"),
        "input_df": st.session_state.input_df.to_dict(orient="records"),
        "deleted_input_df": st.session_state.deleted_input_df.to_dict(orient="records"),
        "staff_list": st.session_state.staff_list,
        "primary_color": st.session_state.primary_color,
        "bg_color": st.session_state.bg_color,
        "sidebar_bg": st.session_state.sidebar_bg,
        "text_color": st.session_state.text_color,
        "bg_image_base64": st.session_state.bg_image_base64,
        "avatar_base64": st.session_state.avatar_base64,
        "current_menu": st.session_state.current_menu
    }
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)

saved_data = load_data()

if "rules_df" not in st.session_state:
    if "rules_df" in saved_data and saved_data["rules_df"]:
        st.session_state.rules_df = pd.DataFrame(saved_data["rules_df"])
    else:
        st.session_state.rules_df = pd.DataFrame(master_rules)

if "input_df" not in st.session_state:
    if "input_df" in saved_data:
        st.session_state.input_df = pd.DataFrame(saved_data["input_df"])
    else:
        st.session_state.input_df = pd.DataFrame(columns=["STT", "Ngày", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"])

if "deleted_input_df" not in st.session_state:
    if "deleted_input_df" in saved_data and saved_data["deleted_input_df"]:
        st.session_state.deleted_input_df = pd.DataFrame(saved_data["deleted_input_df"])
    else:
        st.session_state.deleted_input_df = pd.DataFrame(columns=st.session_state.input_df.columns)

if "staff_list" not in st.session_state:
    st.session_state.staff_list = saved_data.get("staff_list", default_staff_list)

if "primary_color" not in st.session_state:
    st.session_state.primary_color = saved_data.get("primary_color", "#ff4b4b")
if "bg_color" not in st.session_state:
    st.session_state.bg_color = saved_data.get("bg_color", "#ffffff")
if "sidebar_bg" not in st.session_state:
    st.session_state.sidebar_bg = saved_data.get("sidebar_bg", "#f0f2f6")
if "text_color" not in st.session_state:
    st.session_state.text_color = saved_data.get("text_color", "#31333F")
if "bg_image_base64" not in st.session_state:
    st.session_state.bg_image_base64 = saved_data.get("bg_image_base64", None)
if "avatar_base64" not in st.session_state:
    st.session_state.avatar_base64 = saved_data.get("avatar_base64", None)
if "current_menu" not in st.session_state:
    st.session_state.current_menu = saved_data.get("current_menu", "1. Nhập Sản Lượng")

# Ensure STT is always sequential
if not st.session_state.input_df.empty:
    st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
if not st.session_state.rules_df.empty:
    st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
if not st.session_state.deleted_input_df.empty:
    st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)

save_data()

bg_style = f"background-color: {st.session_state.bg_color};"
if st.session_state.bg_image_base64:
    bg_style = f"background-image: url(data:image/png;base64,{st.session_state.bg_image_base64}); background-size: cover; background-repeat: no-repeat; background-attachment: fixed;"

# CSS giao diện tinh gọn, chuyên nghiệp
st.markdown(f"""
<style>
    .stApp {{
        {bg_style}
        color: {st.session_state.text_color};
    }}
    [data-testid="stSidebar"] {{
        background-color: {st.session_state.sidebar_bg};
        resize: horizontal !important;
        overflow: auto !important;
    }}
    h1, h2, h3, h4, h5, h6, .stMarkdown, p, span, label {{
        color: {st.session_state.text_color} !important;
    }}
    h1 {{
        color: {st.session_state.primary_color} !important;
    }}
    /* Làm đậm chữ trong bảng rõ ràng */
    [data-testid="stDataEditor"] *, [data-testid="stDataFrame"] * {{
        font-weight: 600 !important;
        color: #111111 !important;
    }}
    
    /* Thiết kế khung Avatar Zalo/Facebook chuẩn */
    .avatar-container {{
        position: relative;
        width: 100px;
        height: 100px;
        margin: 0 auto 5px auto;
    }}
    .avatar-container img {{
        width: 100px;
        height: 100px;
        border-radius: 50% !important;
        object-fit: cover;
        border: 3px solid {st.session_state.primary_color};
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    .camera-badge-absolute {{
        position: absolute;
        bottom: 0px;
        right: 0px;
        background-color: #ffffff;
        border: 2px solid {st.session_state.primary_color};
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        font-size: 14px;
        cursor: pointer;
    }}

    /* Thẻ thông tin nhân sự chuyên nghiệp */
    .staff-badge-container {{
        background-color: rgba(0, 0, 0, 0.03);
        border-left: 4px solid {st.session_state.primary_color};
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 0.95rem;
    }}

    /* Responsive cho Điện thoại (Mobile) */
    @media (max-width: 768px) {{
        h1 {{
            font-size: 1.5rem !important;
        }}
        h2 {{
            font-size: 1.2rem !important;
        }}
        h3 {{
            font-size: 1.1rem !important;
        }}
        .stApp {{
            padding: 5px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# ----------------- THANH BÊN (SIDEBAR) & ẢNH ĐẠI DIỆN -----------------
with st.sidebar:
    st.markdown("### 👤 Ảnh Đại Diện")
    
    avatar_img_tag = ""
    if st.session_state.avatar_base64:
        try:
            pure_b64 = st.session_state.avatar_base64.split(",")[1] if "," in st.session_state.avatar_base64 else st.session_state.avatar_base64
            pure_b64 += "=" * (-len(pure_b64) % 4)
            avatar_bytes = base64.b64decode(pure_b64)
            encoded_img = base64.b64encode(avatar_bytes).decode("utf-8")
            avatar_img_tag = f'<img src="data:image/png;base64,{encoded_img}" alt="Avatar">'
        except Exception:
            pass
            
    if not avatar_img_tag:
        avatar_img_tag = f'<div style="width:100px;height:100px;border-radius:50%;background:#cbd5e1;display:flex;align-items:center;justify-content:center;font-size:36px;">👤</div>'

    # Sử dụng popover bọc quanh nút bấm icon máy ảnh giống y như mẫu yêu cầu
    col_av1, col_av2, col_av3 = st.columns([1, 2, 1])
    with col_av2:
        with st.popover("📷 Cập nhật ảnh đại diện", use_container_width=True):
            avatar_file = st.file_uploader("Tải ảnh mới (PNG, JPG)", type=["png", "jpg", "jpeg"], key="avatar_uploader_popover", label_visibility="collapsed")
            if avatar_file is not None:
                avatar_bytes = avatar_file.getvalue()
                st.session_state.avatar_base64 = base64.b64encode(avatar_bytes).decode("utf-8")
                save_data()
                st.success("Đã cập nhật ảnh thành công!")
                st.rerun()
                
            if st.session_state.avatar_base64:
                st.markdown("---")
                if st.button("🗑️ Xóa Ảnh Đại Diện", use_container_width=True):
                    st.session_state.avatar_base64 = None
                    save_data()
                    st.success("Đã xóa ảnh đại diện!")
                    st.rerun()

    # Hiển thị ảnh đại diện với icon máy ảnh góc phải dưới
    st.markdown(f"""
    <div class="avatar-container" style="margin-top: 10px;">
        {avatar_img_tag}
        <div class="camera-badge-absolute" title="Nhấp vào nút trên để cập nhật">📷</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📂 CHỨC NĂNG HỆ THỐNG")

    with st.expander("📌 Quản Lý Nghiệp Vụ", expanded=True):
        if st.button("1. Nhập Sản Lượng", use_container_width=True):
            st.session_state.current_menu = "1. Nhập Sản Lượng"
            save_data()
            st.rerun()
        if st.button("2. Báo Cáo & Biểu Đồ", use_container_width=True):
            st.session_state.current_menu = "2. Báo Cáo & Biểu Đồ Tổng Hợp"
            save_data()
            st.rerun()
        if st.button("3. Quản Lý Định Mức", use_container_width=True):
            st.session_state.current_menu = "3. Quản Lý Định Mức Điểm"
            save_data()
            st.rerun()
        if st.button("4. Thùng Rác Sản Lượng", use_container_width=True):
            st.session_state.current_menu = "4. Thùng Rác / Khôi Phục Sản Lượng"
            save_data()
            st.rerun()

    st.markdown("---")

    with st.expander("⚙️ Cấu Hình", expanded=True):
        if st.button("🎨 Cài Đặt Giao Diện", use_container_width=True):
            st.session_state.current_menu = "5. Cài Đặt Giao Diện"
            save_data()
            st.rerun()

menu = st.session_state.current_menu

# Tiêu đề hệ thống tối ưu chuyên nghiệp
st.title("QUẢN LÝ & CHẤM ĐIỂM SẢN LƯỢNG")

staff_joined = " | ".join([f"**{s}**" for s in st.session_state.staff_list])
st.markdown(f"""
<div class="staff-badge-container">
    👥 <b>Nhân sự hệ thống:</b> {staff_joined}
</div>
""", unsafe_allow_html=True)

if menu == "1. Nhập Sản Lượng":
    st.subheader("Nhập Sản Lượng Hàng Ngày")
    st.info("💡 Mẹo: Có thể chụp ảnh trực tiếp từ camera điện thoại hoặc tải file ảnh đính kèm.")
    
    with st.form("entry_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ngay = st.date_input("Ngày làm việc", datetime.date.today())
        with col2:
            nhan_su = st.selectbox("Nhân sự thực hiện", st.session_state.staff_list)
        with col3:
            danh_sach_hang_muc = st.session_state.rules_df["Hạng Mục Công Việc"].tolist()
            hang_muc = st.selectbox("Hạng mục công việc", danh_sach_hang_muc)
            
        col_img, col_qty, col_note = st.columns([2, 2, 2])
        with col_img:
            img_source = st.radio("Nguồn ảnh:", ["Tải lên / Kéo thả", "Chụp trực tiếp"], horizontal=True)
            if img_source == "Chụp trực tiếp":
                record_image = st.camera_input("Chụp ảnh công việc")
            else:
                record_image = st.file_uploader("Tải ảnh đính kèm", type=["png", "jpg", "jpeg"], key="record_img")
                
        with col_qty:
            so_luong = st.number_input("Số lượng thực tế", min_value=1, value=100, step=1)
        with col_note:
            ghi_chu = st.text_input("Ghi chú", "")
            
        submitted = st.form_submit_button("➕ Thêm Bản Ghi Sản Lượng", use_container_width=True)
        if submitted:
            row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
            he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
            don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
            tong_diem = so_luong * he_so
            
            img_base64 = ""
            if record_image is not None:
                bytes_data = record_image.getvalue()
                img_base64 = base64.b64encode(bytes_data).decode("utf-8")
            
            new_stt = len(st.session_state.input_df) + 1
            new_row = {
                "STT": new_stt,
                "Ngày": str(ngay),
                "Nhân Sự": nhan_su,
                "Hạng Mục Công Việc": hang_muc,
                "Hình Ảnh": img_base64,
                "Đơn Vị": don_vi,
                "Số Lượng": so_luong,
                "Hệ Số Điểm": he_so,
                "Tổng Điểm": round(tong_diem, 2),
                "Ghi Chú": ghi_chu
            }
            st.session_state.input_df = pd.concat([st.session_state.input_df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
            save_data()
            st.success(f"Đã thêm thành công sản lượng cho **{nhan_su}**! Tổng điểm: **{tong_diem} điểm**")
            st.rerun()

    st.markdown("---")
    st.subheader("Danh Sách Sản Lượng")
    
    if not st.session_state.input_df.empty:
        st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            all_dates = ["Tất cả"] + sorted(st.session_state.input_df["Ngày"].unique().tolist())
            filter_date = st.selectbox("Lọc theo Ngày", all_dates)
        with f_col2:
            all_staff = ["Tất cả"] + sorted(st.session_state.input_df["Nhân Sự"].unique().tolist())
            filter_staff = st.selectbox("Lọc theo Nhân Sự", all_staff)
        with f_col3:
            all_tasks = ["Tất cả"] + sorted(st.session_state.input_df["Hạng Mục Công Việc"].unique().tolist())
            filter_task = st.selectbox("Lọc theo Hạng Mục", all_tasks)
            
        filtered_df = st.session_state.input_df.copy()
        if filter_date != "Tất cả":
            filtered_df = filtered_df[filtered_df["Ngày"] == filter_date]
        if filter_staff != "Tất cả":
            filtered_df = filtered_df[filtered_df["Nhân Sự"] == filter_staff]
        if filter_task != "Tất cả":
            filtered_df = filtered_df[filtered_df["Hạng Mục Công Việc"] == filter_task]
            
        if not filtered_df.empty:
            filtered_df["STT"] = range(1, len(filtered_df) + 1)
            
            display_df = filtered_df.copy()
            display_df.insert(0, "Chọn", False)
            
            cols_order = ["Chọn", "STT", "Ngày", "Nhân Sự", "Hạng Mục Công Việc", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"]
            display_df = display_df[[c for c in cols_order if c in display_df.columns]]

            edited_table = st.data_editor(
                display_df,
                hide_index=True,
                use_container_width=True,
                key="input_editor_delete"
            )
            
            if st.button("🗑️ Xóa Các Dòng Đã Tích Chọn"):
                selected_rows = edited_table[edited_table["Chọn"] == True]
                if not selected_rows.empty:
                    stt_to_remove = selected_rows["STT"].tolist()
                    rows_to_delete = st.session_state.input_df[st.session_state.input_df["STT"].isin(stt_to_remove)]
                    st.session_state.deleted_input_df = pd.concat([st.session_state.deleted_input_df, rows_to_delete], ignore_index=True)
                    
                    st.session_state.input_df = st.session_state.input_df[~st.session_state.input_df["STT"].isin(stt_to_remove)].reset_index(drop=True)
                    st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                    
                    if not st.session_state.deleted_input_df.empty:
                        st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
                        
                    save_data()
                    st.success("Đã chuyển các dòng đã chọn vào thùng rác thành công!")
                    st.rerun()
                else:
                    st.warning("Vui lòng tích chọn ít nhất một dòng trong bảng để xóa!")
        else:
            st.info("Không tìm thấy bản ghi nào khớp với bộ lọc.")
    else:
        st.info("Chưa có dữ liệu sản lượng nào.")

elif menu == "2. Báo Cáo & Biểu Đồ Tổng Hợp":
    st.header("Báo Cáo Tổng Hợp & Đánh Giá Thi Đua")
    
    if not st.session_state.input_df.empty:
        df_in = st.session_state.input_df
        
        summary = df_in.groupby("Nhân Sự").agg(
            Tổng_Số_Lượng=("Số Lượng", "sum"),
            Tổng_Điểm=("Tổng Điểm", "sum")
        ).reindex(st.session_state.staff_list).fillna(0).reset_index()
        
        total_all_points = summary["Tổng_Điểm"].sum()
        summary["Tỷ_Lệ_Đóng_Góp"] = summary["Tổng_Điểm"].apply(lambda x: (x / total_all_points) if total_all_points > 0 else 0)
        
        def rank_func(pts):
            if pts >= 700:
                return "Xuất Sắc"
            elif pts >= 400:
                return "Đạt"
            else:
                return "Cần Cố Gắn"
                
        summary["Xếp_Loại"] = summary["Tổng_Điểm"].apply(rank_func)
        
        st.subheader("Bảng Tổng Kết Theo Nhân Sự")
        st.dataframe(
            summary.style.format({
                "Tổng_Số_Lượng": "{:,.0f}",
                "Tổng_Điểm": "{:,.1f}",
                "Tỷ_Lệ_Đóng_Góp": "{:.2%}"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        cols = st.columns(len(st.session_state.staff_list) if len(st.session_state.staff_list) > 0 else 1)
        for idx, row in summary.iterrows():
            with cols[idx % len(cols)]:
                st.metric(label=f"Nhân sự: {row['Nhân Sự']}", value=f"{row['Tổng_Điểm']:,.1f} điểm", delta=f"{row['Tỷ_Lệ_Đóng_Góp']:.1%} tổng điểm")
                
        st.subheader("Biểu Đồ Tỷ Lệ Đóng Góp Điểm Thi Đua")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(summary["Tổng_Điểm"], labels=summary["Nhân Sự"], autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
        ax.axis('equal')
        st.pyplot(fig)
        
    else:
        st.warning("Chưa có dữ liệu để tổng hợp báo cáo.")

elif menu == "3. Quản Lý Định Mức Điểm":
    st.header("Quản Lý Danh Mục & Hệ Số Điểm")
    st.markdown("Chỉnh sửa trực tiếp tên công việc, hệ số điểm hoặc khôi phục các mục định mức.")
    
    if not st.session_state.rules_df.empty:
        st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
        
    current_items = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else []
    deleted_items_list = [r for r in master_rules if r["Hạng Mục Công Việc"] not in current_items]
    
    if deleted_items_list:
        st.markdown("#### Khôi Phục Định Mức Đã Xóa")
        deleted_names = [item["Hạng Mục Công Việc"] for item in deleted_items_list]
        selected_to_restore = st.multiselect("Chọn các hạng mục muốn khôi phục lại:", deleted_names)
        
        col_r1, col_r2 = st.columns([2, 5])
        with col_r1:
            if st.button("📥 Khôi Phục Đã Chọn"):
                if selected_to_restore:
                    items_to_add = [item for item in deleted_items_list if item["Hạng Mục Công Việc"] in selected_to_restore]
                    restored_df = pd.DataFrame(items_to_add)
                    st.session_state.rules_df = pd.concat([st.session_state.rules_df, restored_df], ignore_index=True)
                    st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
                    save_data()
                    st.success(f"Đã khôi phục thành công các mục: {', '.join(selected_to_restore)}!")
                    st.rerun()
                else:
                    st.warning("Vui lòng chọn ít nhất một mục để khôi phục.")
        with col_r2:
            if st.button("🔄 Khôi Phục Toàn Bộ Mặc Định"):
                st.session_state.rules_df = pd.DataFrame(master_rules)
                st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
                save_data()
                st.success("Đã khôi phục toàn bộ danh mục mặc định ban đầu thành công!")
                st.rerun()
    else:
        if st.button("🔄 Khôi Phục Toàn Bộ Mặc Định"):
            st.session_state.rules_df = pd.DataFrame(master_rules)
            st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
            save_data()
            st.success("Đã khôi phục toàn bộ danh mục mặc định ban đầu thành công!")
            st.rerun()

    st.markdown("---")
    st.markdown("#### Danh Sách Định Mức Hiện Tại")
    
    edited_rules = st.data_editor(
        st.session_state.rules_df, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="rules_editor",
        hide_index=True
    )
    
    if not edited_rules.equals(st.session_state.rules_df):
        edited_rules["STT"] = range(1, len(edited_rules) + 1)
        st.session_state.rules_df = edited_rules
        save_data()
        st.success("Đã cập nhật lại danh mục định mức điểm thành công!")
        st.rerun()

elif menu == "4. Thùng Rác / Khôi Phục Sản Lượng":
    st.header("Thùng Rác & Khôi Phục Bản Ghi")
    st.markdown("Quản lý các bản ghi sản lượng đã xóa. Có thể khôi phục hoặc xóa vĩnh viễn.")
    
    if not st.session_state.deleted_input_df.empty:
        st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
        trash_display = st.session_state.deleted_input_df.copy()
        trash_display.insert(0, "Chọn", False)
        
        edited_trash = st.data_editor(
            trash_display.drop(columns=["Hình Ảnh"], errors="ignore"),
            hide_index=True,
            use_container_width=True,
            key="trash_editor"
        )
        
        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            if st.button("📥 Khôi Phục Dòng Đã Chọn"):
                selected_rows = edited_trash[edited_trash["Chọn"] == True]
                if not selected_rows.empty:
                    selected_rows = selected_rows.drop(columns=["Chọn"])
                    stt_to_remove = selected_rows["STT"].tolist()
                    
                    st.session_state.deleted_input_df = st.session_state.deleted_input_df[~st.session_state.deleted_input_df["STT"].isin(stt_to_remove)].reset_index(drop=True)
                    if not st.session_state.deleted_input_df.empty:
                        st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
                    
                    selected_rows = selected_rows.copy()
                    for idx, row in selected_rows.iterrows():
                        new_row = row.copy()
                        new_row["STT"] = len(st.session_state.input_df) + 1
                        st.session_state.input_df = pd.concat([st.session_state.input_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                    save_data()
                    st.success("Đã khôi phục các dòng đã chọn thành công về danh sách chính!")
                    st.rerun()
                else:
                    st.warning("Vui lòng tích chọn ít nhất một dòng trong bảng!")

        with col_act2:
            if st.button("🔥 Xóa Vĩnh Viễn Dòng Đã Chọn"):
                selected_rows = edited_trash[edited_trash["Chọn"] == True]
                if not selected_rows.empty:
                    selected_rows = selected_rows.drop(columns=["Chọn"])
                    stt_to_remove = selected_rows["STT"].tolist()
                    
                    st.session_state.deleted_input_df = st.session_state.deleted_input_df[~st.session_state.deleted_input_df["STT"].isin(stt_to_remove)].reset_index(drop=True)
                    if not st.session_state.deleted_input_df.empty:
                        st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
                    
                    save_data()
                    st.success("Đã xóa vĩnh viễn các dòng đã chọn khỏi thùng rác!")
                    st.rerun()
                else:
                    st.warning("Vui lòng tích chọn ít nhất một dòng trong bảng!")

        st.markdown("---")
        if st.button("🧹 Dọn Sạch Toàn Bộ Thùng Rác"):
            st.session_state.deleted_input_df = pd.DataFrame(columns=st.session_state.input_df.columns)
            save_data()
            st.success("Đã dọn sạch toàn bộ thùng rác!")
            st.rerun()
    else:
        st.info("Thùng rác hiện tại đang trống.")

elif menu == "5. Cài Đặt Giao Diện":
    st.header("Cài Đặt Giao Diện & Nhân Sự")
    st.markdown("Tùy chỉnh danh sách nhân sự, màu sắc và hình nền cho toàn bộ ứng dụng.")
    
    st.subheader("Quản Lý Danh Sách Nhân Sự")
    staff_df = pd.DataFrame({"Nhân Sự": st.session_state.staff_list})
    edited_staff_df = st.data_editor(
        staff_df,
        num_rows="dynamic",
        use_container_width=True,
        key="staff_editor",
        hide_index=True
    )
    if not edited_staff_df.equals(staff_df):
        new_staff_list = [str(x).strip() for x in edited_staff_df["Nhân Sự"].tolist() if str(x).strip() != ""]
        if new_staff_list:
            st.session_state.staff_list = new_staff_list
            save_data()
            st.success("Đã cập nhật danh sách nhân sự thành công!")
            st.rerun()
        else:
            st.warning("Danh sách nhân sự không được để trống.")

    st.markdown("---")
    st.subheader("Tùy Chỉnh Màu Sắc Giao Diện")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.session_state.primary_color = st.color_picker("Màu chủ đạo", st.session_state.primary_color)
        st.session_state.bg_color = st.color_picker("Màu nền trang", st.session_state.bg_color)
    with col_c2:
        st.session_state.sidebar_bg = st.color_picker("Màu nền thanh bên", st.session_state.sidebar_bg)
        st.session_state.text_color = st.color_picker("Màu chữ", st.session_state.text_color)
        
    st.markdown("---")
    st.subheader("Tùy Chọn Hình Nền (Wallpaper)")
    bg_file = st.file_uploader("Kéo thả hoặc tải ảnh hình nền (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="bg_uploader")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if bg_file is not None:
            bytes_data = bg_file.getvalue()
            st.session_state.bg_image_base64 = base64.b64encode(bytes_data).decode("utf-8")
            save_data()
            st.success("Đã tải ảnh hình nền thành công!")
    with col_b2:
        if st.session_state.bg_image_base64 is not None:
            if st.button("🗑️ Xóa Hình Nền Hiện Tại"):
                st.session_state.bg_image_base64 = None
                save_data()
                st.success("Đã xóa ảnh hình nền về mặc định!")
                st.rerun()

    st.markdown("---")
    if st.button("💾 Lưu & Áp Dụng Thay Đổi"):
        save_data()
        st.success("Đã lưu và cập nhật giao diện thực tế thành công!")
        st.rerun()
