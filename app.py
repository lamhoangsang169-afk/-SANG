
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from PIL import Image
import io

st.set_page_config(page_title="Phần Mềm Chấm Điểm Sản Lượng", page_icon="📊", layout="wide")

# Master list of all default rules
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

# Initialize Session State data if not present
if "rules_df" not in st.session_state:
    st.session_state.rules_df = pd.DataFrame(master_rules)

if "input_df" not in st.session_state:
    st.session_state.input_df = pd.DataFrame([
        {
            "STT": 1, "Ngày": str(datetime.date.today()), "Nhân Sự": "Đức", 
            "Hạng Mục Công Việc": "Lấy hộp có sẵn", "Hình Ảnh": "Không có", 
            "Đơn Vị": "Cái", "Số Lượng": 200, "Hệ Số Điểm": 0.5, "Tổng Điểm": 100.0, "Ghi Chú": "Ca sáng"
        },
        {
            "STT": 2, "Ngày": str(datetime.date.today()), "Nhân Sự": "Bảo", 
            "Hạng Mục Công Việc": "Lấy đế có sẵn", "Hình Ảnh": "Không có", 
            "Đơn Vị": "Cái", "Số Lượng": 300, "Hệ Số Điểm": 0.5, "Tổng Điểm": 150.0, "Ghi Chú": "Cấp đế"
        },
        {
            "STT": 3, "Ngày": str(datetime.date.today()), "Nhân Sự": "Tiến", 
            "Hạng Mục Công Việc": "Giao hàng shiper", "Hình Ảnh": "Không có", 
            "Đơn Vị": "Cái", "Số Lượng": 398, "Hệ Số Điểm": 1.0, "Tổng Điểm": 398.0, "Ghi Chú": "Giao đơn"
        }
    ])

# Trash bin for deleted production records
if "deleted_input_df" not in st.session_state:
    st.session_state.deleted_input_df = pd.DataFrame(columns=st.session_state.input_df.columns)

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# Sidebar image uploader for app header/logo
st.sidebar.markdown("### 🖼️ Tải Logo / Ảnh Tùy Ý")
uploaded_file = st.sidebar.file_uploader("Chọn ảnh (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="sidebar_img")
if uploaded_file is not None:
    st.session_state.uploaded_image = uploaded_file

if st.session_state.uploaded_image is not None:
    st.sidebar.image(st.session_state.uploaded_image, caption="Logo trên App", use_container_width=True)

st.title("🏭 HỆ THỐNG QUẢN LÝ & CHẤM ĐIỂM SẢN LƯỢNG")
st.markdown("### Dành cho nhân sự: **Đức, Bảo, Tiến**")

# Sidebar navigation with 4 menu items
menu = st.sidebar.selectbox("📂 Chọn Chức Năng", [
    "1. Nhập Sản Lượng", 
    "2. Báo Cáo & Biểu Đồ Tổng Hợp", 
    "3. Quản Lý Định Mức Điểm", 
    "4. Thùng Rác / Khôi Phục Sản Lượng"
])

# 1. Nhập Sản Lượng
if menu == "1. Nhập Sản Lượng":
    st.header("📝 Nhập Sản Lượng Hàng Ngày & Đính Kèm Ảnh")
    
    with st.form("entry_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ngay = st.date_input("Ngày làm việc", datetime.date.today())
        with col2:
            nhan_su = st.selectbox("Chọn Nhân Sự", ["Đức", "Bảo", "Tiến"])
        with col3:
            danh_sach_hang_muc = st.session_state.rules_df["Hạng Mục Công Việc"].tolist()
            hang_muc = st.selectbox("Hạng Mục Công Việc", danh_sach_hang_muc)
            
        col_img, col_qty, col_note = st.columns([2, 2, 2])
        with col_img:
            record_image = st.file_uploader("📷 Tải ảnh đính kèm (Cho hạng mục này)", type=["png", "jpg", "jpeg"], key="record_img")
        with col_qty:
            so_luong = st.number_input("Số lượng thực tế", min_value=1, value=100, step=1)
        with col_note:
            ghi_chu = st.text_input("Ghi chú công việc", "")
            
        submitted = st.form_submit_button("➕ Thêm Bản Ghi Sản Lượng")
        if submitted:
            row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
            he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
            don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
            tong_diem = so_luong * he_so
            
            img_name = "Có đính kèm ảnh" if record_image is not None else "Không có"
            
            new_stt = len(st.session_state.input_df) + 1
            new_row = {
                "STT": new_stt,
                "Ngày": str(ngay),
                "Nhân Sự": nhan_su,
                "Hạng Mục Công Việc": hang_muc,
                "Hình Ảnh": img_name,
                "Đơn Vị": don_vi,
                "Số Lượng": so_luong,
                "Hệ Số Điểm": he_so,
                "Tổng Điểm": round(tong_diem, 2),
                "Ghi Chú": ghi_chu
            }
            st.session_state.input_df = pd.concat([st.session_state.input_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Đã thêm thành công sản lượng cho **{nhan_su}**! Tổng điểm: **{tong_diem} điểm**")

    st.markdown("---")
    st.subheader("🔍 Bộ Lọc Dữ Liệu & Tùy Chọn Cột Hiển Thị")
    
    # Filter controls
    if not st.session_state.input_df.empty:
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            all_dates = ["Tất cả"] + sorted(st.session_state.input_df["Ngày"].unique().tolist())
            filter_date = st.selectbox("📅 Lọc theo Ngày", all_dates)
        with f_col2:
            all_staff = ["Tất cả"] + sorted(st.session_state.input_df["Nhân Sự"].unique().tolist())
            filter_staff = st.selectbox("👤 Lọc theo Nhân Sự", all_staff)
        with f_col3:
            all_tasks = ["Tất cả"] + sorted(st.session_state.input_df["Hạng Mục Công Việc"].unique().tolist())
            filter_task = st.selectbox("🛠️ Lọc theo Hạng Mục Công Việc", all_tasks)
            
        # Column selector (drop/select columns)
        all_cols = st.session_state.input_df.columns.tolist()
        selected_cols = st.multiselect("👁️ Chọn các cột muốn hiển thị trên bảng:", all_cols, default=all_cols)
            
        # Apply filters
        filtered_df = st.session_state.input_df.copy()
        if filter_date != "Tất cả":
            filtered_df = filtered_df[filtered_df["Ngày"] == filter_date]
        if filter_staff != "Tất cả":
            filtered_df = filtered_df[filtered_df["Nhân Sự"] == filter_staff]
        if filter_task != "Tất cả":
            filtered_df = filtered_df[filtered_df["Hạng Mục Công Việc"] == filter_task]
            
        # Display with selected columns
        if selected_cols:
            st.dataframe(filtered_df[selected_cols], use_container_width=True)
        else:
            st.dataframe(filtered_df, use_container_width=True)
        
        # Delete row functionality with trash bin logging
        del_idx = st.number_input("Nhập STT dòng muốn xóa (nếu cần)", min_value=0, max_value=len(st.session_state.input_df), value=0, step=1)
        if st.button("🗑️ Xóa dòng đã chọn"):
            if del_idx > 0:
                row_to_delete = st.session_state.input_df[st.session_state.input_df["STT"] == del_idx]
                if not row_to_delete.empty:
                    st.session_state.deleted_input_df = pd.concat([st.session_state.deleted_input_df, row_to_delete], ignore_index=True)
                    st.session_state.input_df = st.session_state.input_df[st.session_state.input_df["STT"] != del_idx].reset_index(drop=True)
                    st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                    st.success(f"Đã chuyển dòng số {del_idx} vào thùng rác!")
                    st.rerun()
                else:
                    st.error("Không tìm thấy số STT này!")
    else:
        st.info("Chưa có dữ liệu sản lượng nào.")

# 2. Báo Cáo & Biểu Đồ Tổng Hợp
elif menu == "2. Báo Cáo & Biểu Đồ Tổng Hợp":
    st.header("📊 Báo Cáo Tổng Hợp & Đánh Giá Thi Đua")
    
    if not st.session_state.input_df.empty:
        df_in = st.session_state.input_df
        
        summary = df_in.groupby("Nhân Sự").agg(
            Tổng_Số_Lượng=("Số Lượng", "sum"),
            Tổng_Điểm=("Tổng Điểm", "sum")
        ).reindex(["Đức", "Bảo", "Tiến"]).fillna(0).reset_index()
        
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
        
        st.subheader("🏆 Bảng Tổng Kết Theo Nhân Sự")
        st.dataframe(
            summary.style.format({
                "Tổng_Số_Lượng": "{:,.0f}",
                "Tổng_Điểm": "{:,.1f}",
                "Tỷ_Lệ_Đóng_Góp": "{:.2%}"
            }),
            use_container_width=True
        )
        
        col1, col2, col3 = st.columns(3)
        for idx, row in summary.iterrows():
            with [col1, col2, col3][idx]:
                st.metric(label=f"Nhân sự: {row['Nhân Sự']}", value=f"{row['Tổng_Điểm']:,.1f} điểm", delta=f"{row['Tỷ_Lệ_Đóng_Góp']:.1%} tổng điểm")
                
        st.subheader("🥧 Biểu Đồ Tỷ Lệ Đóng Góp Điểm Thi Đua")
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ['#ff9999','#66b3ff','#99ff99']
        ax.pie(summary["Tổng_Điểm"], labels=summary["Nhân Sự"], autopct='%1.1f%%', startangle=90, colors=colors, textprops={'fontsize': 12})
        ax.axis('equal')
        st.pyplot(fig)
        
    else:
        st.warning("Chưa có dữ liệu để tổng hợp báo cáo.")

# 3. Quản Lý Định Mức Điểm
elif menu == "3. Quản Lý Định Mức Điểm":
    st.header("⚙️ Quản Lý Danh Mục & Hệ Số Điểm")
    st.markdown("Bạn có thể **chỉnh sửa trực tiếp** tên công việc/hệ số điểm, xóa hạng mục, hoặc khôi phục các mục định mức đã xóa.")
    
    current_items = st.session_state.rules_df["Hạng Mục Công Việc"].tolist() if not st.session_state.rules_df.empty else []
    deleted_items_list = [r for r in master_rules if r["Hạng Mục Công Việc"] not in current_items]
    
    if deleted_items_list:
        st.markdown("#### ♻️ Khôi Phục Từng Mục Định Mức Đã Xóa")
        deleted_names = [item["Hạng Mục Công Việc"] for item in deleted_items_list]
        selected_to_restore = st.multiselect("Chọn các hạng mục muốn khôi phục lại:", deleted_names)
        
        col_r1, col_r2 = st.columns([2, 5])
        with col_r1:
            if st.button("📥 Khôi Phục Các Mục Đã Chọn"):
                if selected_to_restore:
                    items_to_add = [item for item in deleted_items_list if item["Hạng Mục Công Việc"] in selected_to_restore]
                    restored_df = pd.DataFrame(items_to_add)
                    st.session_state.rules_df = pd.concat([st.session_state.rules_df, restored_df], ignore_index=True)
                    st.session_state.rules_df["STT"] = range(1, len(st.session_state.rules_df) + 1)
                    st.success(f"Đã khôi phục thành công các mục: {', '.join(selected_to_restore)}!")
                    st.rerun()
                else:
                    st.warning("Vui lòng chọn ít nhất một mục để khôi phục.")
        with col_r2:
            if st.button("🔄 Khôi Phục Toàn Bộ Danh Mục Mặc Định"):
                st.session_state.rules_df = pd.DataFrame(master_rules)
                st.success("Đã khôi phục toàn bộ danh mục mặc định ban đầu thành công!")
                st.rerun()
    else:
        if st.button("🔄 Khôi Phục Toàn Bộ Danh Mục Mặc Định"):
            st.session_state.rules_df = pd.DataFrame(master_rules)
            st.success("Đã khôi phục toàn bộ danh mục mặc định ban đầu thành công!")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Danh Sách Định Mức Hiện Tại (Có thể chỉnh sửa hoặc xóa trực tiếp)")
    edited_rules = st.data_editor(
        st.session_state.rules_df, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="rules_editor"
    )
    
    if not edited_rules.equals(st.session_state.rules_df):
        st.session_state.rules_df = edited_rules
        st.success("Đã cập nhật lại danh mục định mức điểm thành công!")
        st.rerun()

# 4. Thùng Rác / Khôi Phục Sản Lượng
elif menu == "4. Thùng Rác / Khôi Phục Sản Lượng":
    st.header("🗑️ Thùng Rác & Khôi Phục Bản Ghi Sản Lượng Đã Xóa")
    st.markdown("Tại đây lưu trữ các dòng sản lượng đã bị xóa từ trang Nhập Sản Lượng. Bạn có thể xem lại và khôi phục khi cần.")
    
    if not st.session_state.deleted_input_df.empty:
        st.dataframe(st.session_state.deleted_input_df, use_container_width=True)
        
        restore_stt = st.number_input("Nhập STT dòng đã xóa muốn khôi phục lại:", min_value=0, max_value=len(st.session_state.deleted_input_df), value=0, step=1, key="restore_trash_stt")
        if st.button("📥 Khôi Phục Bản Ghi Này"):
            if restore_stt > 0:
                row_to_restore = st.session_state.deleted_input_df[st.session_state.deleted_input_df["STT"] == restore_stt]
                if not row_to_restore.empty:
                    st.session_state.deleted_input_df = st.session_state.deleted_input_df[st.session_state.deleted_input_df["STT"] != restore_stt].reset_index(drop=True)
                    if not st.session_state.deleted_input_df.empty:
                        st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
                    
                    row_to_restore = row_to_restore.copy()
                    row_to_restore["STT"] = len(st.session_state.input_df) + 1
                    st.session_state.input_df = pd.concat([st.session_state.input_df, row_to_restore], ignore_index=True)
                    st.success("Đã khôi phục dòng sản lượng thành công về danh sách chính!")
                    st.rerun()
                else:
                    st.error("Không tìm thấy số STT này trong thùng rác!")
    else:
        st.info("Thùng rác hiện tại đang trống (chưa có bản ghi sản lượng nào bị xóa).")
