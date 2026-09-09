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
        st.markdown(f"""
        <div style="cursor: pointer; text-align: center;">
            <img src="data:image/png;base64,{encoded_img}" style="width:160px; height:160px; border-radius:50%; object-fit:cover; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3);">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="width:160px; height:160px; border-radius:50%; background:#cbd5e1; display:flex; align-items:center; justify-content:center; font-size:60px; border:3px solid {st.session_state.primary_color}; box-shadow:0 4px 10px rgba(0,0,0,0.3); margin: 0 auto;">
            👤
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="avatar-popover-wrapper">', unsafe_allow_html=True)
    with st.popover(" "):
        st.markdown("##### ⚙️ Cài Đặt Ảnh Đại Diện")
        avatar_file = st.file_uploader("Tải ảnh", type=["png", "jpg", "jpeg"], key="avatar_uploader_popover", label_visibility="collapsed")
        if avatar_file is not None:
            avatar_bytes = avatar_file.getvalue()
            st.session_state.avatar_base64 = base64.b64encode(avatar_bytes).decode("utf-8")
            save_data()
            st.success("Đã cập nhật ảnh đại diện!")
            st.rerun()
            
        if st.session_state.avatar_base64:
            st.markdown("---")
            if st.button("🗑️ Xóa Ảnh Đại Diện", use_container_width=True):
                st.session_state.avatar_base64 = None
                save_data()
                st.success("Đã xóa ảnh đại diện!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Đưa nút Chấm Công lên trên cùng, tách khỏi nhóm Chức năng hệ thống
    if st.button("⏱️ Chấm Công Ca Làm Việc", use_container_width=True):
        st.session_state.current_menu = "2. Chấm Công Ca Làm Việc"
        save_data()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📂 CHỨC NĂNG HỆ THỐNG")

    with st.expander("📌 Quản Lý Nghiệp Vụ", expanded=True):
        if st.button("1. Nhập Sản Lượng", use_container_width=True):
            st.session_state.current_menu = "1. Nhập Sản Lượng"
            save_data()
            st.rerun()
        if st.button("3. Báo Cáo & Biểu Đồ", use_container_width=True):
            st.session_state.current_menu = "3. Báo Cáo & Biểu Đồ Tổng Hợp"
            save_data()
            st.rerun()
        if st.button("4. Quản Lý Định Mức", use_container_width=True):
            st.session_state.current_menu = "4. Quản Lý Định Mức Điểm"
            save_data()
            st.rerun()
        if st.button("5. Thùng Rác Sản Lượng", use_container_width=True):
            st.session_state.current_menu = "5. Thùng Rác / Khôi Phục Sản Lượng"
            save_data()
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Cấu Hình Hệ Thống")
    if st.button("🎨 Cài Đặt Giao Diện", use_container_width=True):
        st.session_state.current_menu = "6. Cài Đặt Giao Diện"
        save_data()
        st.rerun()
    if st.button("🧹 Làm Sạch & Tối Ưu Dữ Liệu", use_container_width=True):
        st.session_state.current_menu = "7. Làm Sạch Dữ Liệu"
        save_data()
        st.rerun()
