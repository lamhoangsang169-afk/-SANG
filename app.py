
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Phần Mềm Chấm Điểm Sản Lượng", page_icon="📊", layout="wide")

# Initialize Session State data if not present
if "rules_df" not in st.session_state:
    st.session_state.rules_df = pd.DataFrame([
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
    ])

if "input_df" not in st.session_state:
    st.session_state.input_df = pd.DataFrame([
        {"STT": 1, "Ngày": str(datetime.date.today()), "Nhân Sự": "Đức", "Hạng Mục Công Việc": "Lấy hộp có sẵn", "Đơn Vị": "Cái", "Số Lượng": 200, "Hệ Số Điểm": 0.5, "Tổng Điểm": 100.0, "Ghi Chú": "Ca sáng"},
        {"STT": 2, "Ngày": str(datetime.date.today()), "Nhân Sự": "Bảo", "Hạng Mục Công Việc": "Lấy đế có sẵn", "Đơn Vị": "Cái", "Số Lượng": 300, "Hệ Số Điểm": 0.5, "Tổng Điểm": 150.0, "Ghi Chú": "Cấp đế"},
        {"STT": 3, "Ngày": str(datetime.date.today()), "Nhân Sự": "Tiến", "Hạng Mục Công Việc": "Giao hàng shiper", "Đơn Vị": "Cái", "Số Lượng": 398, "Hệ Số Điểm": 1.0, "Tổng Điểm": 398.0, "Ghi Chú": "Giao đơn"}
    ])

st.title("🏭 HỆ THỐNG QUẢN LÝ & CHẤM ĐIỂM SẢN LƯỢNG")
st.markdown("### Dành cho nhân sự: **Đức, Bảo, Tiến**")

# Sidebar navigation
menu = st.sidebar.selectbox("📂 Chọn Chức Năng", ["1. Nhập Sản Lượng", "2. Báo Cáo & Biểu Đồ Tổng Hợp", "3. Quản Lý Định Mức Điểm"])

# 1. Nhập Sản Lượng
if menu == "1. Nhập Sản Lượng":
    st.header("📝 Nhập Sản Lượng Hàng Ngày")
    
    with st.form("entry_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ngay = st.date_input("Ngày làm việc", datetime.date.today())
        with col2:
            nhan_su = st.selectbox("Chọn Nhân Sự", ["Đức", "Bảo", "Tiến"])
        with col3:
            danh_sach_hang_muc = st.session_state.rules_df["Hạng Mục Công Việc"].tolist()
            hang_muc = st.selectbox("Hạng Mục Công Việc", danh_sach_hang_muc)
            
        col4, col5 = st.columns(2)
        with col4:
            so_luong = st.number_input("Số lượng thực tế", min_value=1, value=100, step=1)
        with col5:
            ghi_chu = st.text_input("Ghi chú công việc", "")
            
        submitted = st.form_submit_button("➕ Thêm Bản Ghi Sản Lượng")
        if submitted:
            # Get coefficient
            row_rule = st.session_state.rules_df[st.session_state.rules_df["Hạng Mục Công Việc"] == hang_muc]
            he_so = float(row_rule["Hệ Số Điểm"].values[0]) if not row_rule.empty else 1.0
            don_vi = row_rule["Đơn Vị"].values[0] if not row_rule.empty else "Cái"
            tong_diem = so_luong * he_so
            
            new_stt = len(st.session_state.input_df) + 1
            new_row = {
                "STT": new_stt,
                "Ngày": str(ngay),
                "Nhân Sự": nhan_su,
                "Hạng Mục Công Việc": hang_muc,
                "Đơn Vị": don_vi,
                "Số Lượng": so_luong,
                "Hệ Số Điểm": he_so,
                "Tổng Điểm": round(tong_diem, 2),
                "Ghi Chú": ghi_chu
            }
            st.session_state.input_df = pd.concat([st.session_state.input_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Đã thêm thành công sản lượng cho **{nhan_su}**! Tổng điểm nhận được: **{tong_diem} điểm**")

    st.subheader("📋 Danh Sách Sản Lượng Đã Nhập")
    if not st.session_state.input_df.empty:
        st.dataframe(st.session_state.input_df, use_container_width=True)
        
        # Delete row option
        del_idx = st.number_input("Nhập STT dòng muốn xóa (nếu cần)", min_value=0, max_value=len(st.session_state.input_df), value=0, step=1)
        if st.button("🗑️ Xóa dòng đã chọn"):
            if del_idx > 0:
                st.session_state.input_df = st.session_state.input_df[st.session_state.input_df["STT"] != del_idx].reset_index(drop=True)
                # Re-index STT
                st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
                st.success(f"Đã xóa dòng số {del_idx}!")
                st.rerun()
    else:
        st.info("Chưa có dữ liệu sản lượng nào.")

# 2. Báo Cáo & Biểu Đồ Tổng Hợp
elif menu == "2. Báo Cáo & Biểu Đồ Tổng Hợp":
    st.header("📊 Báo Cáo Tổng Hợp & Đánh Giá Thi Đua")
    
    if not st.session_state.input_df.empty:
        df_in = st.session_state.input_df
        
        # Aggregate by personnel (Đức, Bảo, Tiến)
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
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        for idx, row in summary.iterrows():
            with [col1, col2, col3][idx]:
                st.metric(label=f"Nhân sự: {row['Nhân Sự']}", value=f"{row['Tổng_Điểm']:,.1f} điểm", delta=f"{row['Tỷ_Lệ_Đóng_Góp']:.1%} tổng điểm")
                
        # Pie Chart
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
    st.markdown("Bạn có thể thêm hạng mục mới hoặc thay đổi hệ số điểm tại đây. Hệ thống sẽ tự động cập nhật cho các phần nhập liệu.")
    
    st.dataframe(st.session_state.rules_df, use_container_width=True)
    
    st.subheader("➕ Thêm Hạng Mục Mới")
    with st.form("add_rule_form"):
        new_hang_muc = st.text_input("Tên Hạng Mục Công Việc Mới")
        new_don_vi = st.text_input("Đơn Vị", "Cái")
        new_he_so = st.number_input("Hệ Số Điểm (Điểm/Cái)", min_value=0.0, value=1.0, step=0.1)
        new_ghichu = st.text_input("Ghi Chú", "Sản xuất / Vận hành")
        
        add_rule_btn = st.form_submit_button("Thêm Hạng Mục")
        if add_rule_btn and new_hang_muc:
            if new_hang_muc in st.session_state.rules_df["Hạng Mục Công Việc"].values:
                st.error("Hạng mục này đã tồn tại!")
            else:
                next_stt = len(st.session_state.rules_df) + 1
                new_rule = {
                    "STT": next_stt,
                    "Hạng Mục Công Việc": new_hang_muc,
                    "Đơn Vị": new_don_vi,
                    "Hệ Số Điểm": float(new_he_so),
                    "Ghi Chú": new_ghichu
                }
                st.session_state.rules_df = pd.concat([st.session_state.rules_df, pd.DataFrame([new_rule])], ignore_index=True)
                st.success(f"Đã thêm hạng mục **{new_hang_muc}** thành công!")
                st.rerun()
