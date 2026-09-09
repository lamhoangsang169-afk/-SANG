# ==================== 6. CÀI ĐẶT GIAO DIỆN ====================
elif menu == "6. Cài Đặt Giao Diện":
    st.header("Cài Đặt Giao Diện & Nhân Sự")
    st.markdown("Tùy chỉnh danh sách nhân sự, màu sắc và kho lưu trữ hình nền cho ứng dụng.")
    
    st.subheader("Quản Lý Danh Sách Nhân Sự")
    with st.form("staff_form"):
        staff_df = pd.DataFrame({"Nhân Sự": st.session_state.staff_list})
        edited_staff_df = st.data_editor(
            staff_df,
            num_rows="dynamic",
            use_container_width=True,
            key="staff_editor",
            hide_index=True
        )
        save_staff_btn = st.form_submit_button("💾 Lưu Danh Sách Nhân Sự", use_container_width=True)
        if save_staff_btn:
            new_staff_list = [str(x).strip() for x in edited_staff_df["Nhân Sự"].tolist() if str(x).strip() != ""]
            if new_staff_list:
                st.session_state.staff_list = new_staff_list
                save_data()
                st.success("Đã cập nhật danh sách nhân sự thành công!")
                st.rerun()
            else:
                st.warning("Danh sách nhân sự không được để trống.")

    st.markdown("---")
    
    # Gom chung toàn bộ phần Cài đặt Giao diện vào một Form lớn để khi bấm "Lưu & Áp Dụng" mới ghi nhận tất cả
    with st.form("interface_settings_form"):
        st.subheader("Tùy Chỉnh Màu Sắc Giao Diện")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            new_primary = st.color_picker("Màu chủ đạo", st.session_state.primary_color)
            new_bg = st.color_picker("Màu nền trang", st.session_state.bg_color)
        with col_c2:
            new_sidebar_bg = st.color_picker("Màu nền thanh bên", st.session_state.sidebar_bg)
            new_text_color = st.color_picker("Màu chữ", st.session_state.text_color)
            
        new_opacity = st.slider(
            "Độ trong suốt của thanh Sidebar (0.0 = trong suốt hoàn toàn thấy ảnh nền, 1.0 = đặc màu)", 
            min_value=0.0, max_value=1.0, value=float(st.session_state.sidebar_opacity), step=0.05
        )

        st.markdown("---")
        st.subheader("🖼️ Kho Lưu Trữ Hình Nền (Tối đa 5 hình)")
        
        current_count = len(st.session_state.wallpaper_library)
        st.info(f"Đang lưu trữ trong kho: **{current_count} / 5** hình ảnh.")

        # Kiểm tra giới hạn tối đa 5 hình
        if current_count >= 5:
            st.warning("⚠️ Kho lưu trữ đã đạt giới hạn tối đa 5 hình nền! Vui lòng xóa bớt hình ảnh cũ bên dưới trước nếu muốn lưu thêm hình mới.")
            bg_file = None
        else:
            bg_file = st.file_uploader("Kéo thả hoặc tải ảnh hình nền mới (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="bg_uploader_form")

        submitted_interface = st.form_submit_button("💾 Lưu & Áp Dụng Thay Đổi", use_container_width=True)
        
        if submitted_interface:
            st.session_state.primary_color = new_primary
            st.session_state.bg_color = new_bg
            st.session_state.sidebar_bg = new_sidebar_bg
            st.session_state.text_color = new_text_color
            st.session_state.sidebar_opacity = new_opacity

            # Chỉ khi bấm nút Lưu này và có file tải lên thì mới tính là 1 bức hình được thêm vào kho
            if bg_file is not None:
                if len(st.session_state.wallpaper_library) < 5:
                    bytes_data = bg_file.getvalue()
                    new_b64 = base64.b64encode(bytes_data).decode("utf-8")
                    st.session_state.wallpaper_library.append(new_b64)
                    st.session_state.bg_image_base64 = new_b64
                    st.success("Đã thêm hình nền mới vào kho và áp dụng thành công!")
                else:
                    st.error("Kho đã đầy (5/5), không thể lưu thêm hình mới!")
            
            save_data()
            st.success("Đã lưu và cập nhật giao diện thực tế thành công!")
            st.rerun()

    # Phần quản lý danh sách ảnh đã lưu bên dưới (Chọn nhanh hoặc Xóa) nằm ngoài form chính để thao tác trực quan từng ảnh
    if st.session_state.wallpaper_library:
        st.markdown("---")
        st.markdown("#### 📂 Quản Lý & Chọn Hình Nền Đã Lưu")
        cols = st.columns(min(len(st.session_state.wallpaper_library), 5))
        
        for idx, img_b64 in enumerate(st.session_state.wallpaper_library):
            col_idx = idx % len(cols)
            with cols[col_idx]:
                try:
                    pure_b64 = img_b64.split(",")[1] if "," in img_b64 else img_b64
                    img_bytes = base64.b64decode(pure_b64)
                    st.image(img_bytes, width=120, caption=f"Ảnh #{idx+1}")
                    
                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if st.button("Chọn", key=f"use_wall_{idx}", use_container_width=True):
                            st.session_state.bg_image_base64 = img_b64
                            save_data()
                            st.success(f"Đã chọn Ảnh #{idx+1} làm hình nền!")
                            st.rerun()
                    with b_col2:
                        if st.button("Xóa", key=f"del_wall_{idx}", use_container_width=True):
                            if st.session_state.bg_image_base64 == img_b64:
                                st.session_state.bg_image_base64 = None
                            st.session_state.wallpaper_library.pop(idx)
                            save_data()
                            st.warning(f"Đã xóa Ảnh #{idx+1} khỏi kho lưu trữ!")
                            st.rerun()
                except Exception:
                    pass
    else:
        st.text("Chưa có hình nền nào trong kho lưu trữ.")

    if st.session_state.bg_image_base64 is not None and not st.session_state.wallpaper_library:
        if st.button("🗑️ Xóa Hình Nền Đang Dùng Hiện Tại"):
            st.session_state.bg_image_base64 = None
            save_data()
            st.success("Đã xóa ảnh hình nền về mặc định!")
            st.rerun()
