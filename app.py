# ==================== BÁO CÁO & BIỂU ĐỒ ====================
elif feature == "report":
    st.header(menu)
    
    all_staff_current = st.session_state.staff_list
    
    if not st.session_state.input_df.empty:
        df_in = st.session_state.input_df
        summary = df_in.groupby("Nhân Sự").agg(
            Tổng_Số_Lượng=("Số Lượng", "sum"),
            Tổng_Điểm=("Tổng Điểm", "sum")
        ).reindex(all_staff_current).fillna(0).reset_index()
    else:
        summary = pd.DataFrame({
            "Nhân Sự": all_staff_current,
            "Tổng_Số_Lượng": [0.0] * len(all_staff_current),
            "Tổng_Điểm": [0.0] * len(all_staff_current)
        })
        
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
    
    st.markdown("---")
    st.subheader("⚖️ Bảng Đối Chiếu Thời Gian Làm Việc & Sản Lượng")
    
    if not st.session_state.attendance_df.empty:
        att_summary = st.session_state.attendance_df.groupby("Nhân Sự")["Số Phút Làm Việc"].sum().reset_index()
        att_summary.columns = ["Nhân Sự", "Tổng Phút Làm Việc"]
    else:
        att_summary = pd.DataFrame({"Nhân Sự": all_staff_current, "Tổng Phút Làm Việc": 0})
        
    comparison_df = pd.merge(summary[["Nhân Sự", "Tổng_Điểm", "Tỷ_Lệ_Đóng_Góp"]], att_summary, on="Nhân Sự", how="outer").fillna(0)
    comparison_df = comparison_df.sort_values(by="Tỷ_Lệ_Đóng_Góp", ascending=False).reset_index(drop=True)
    
    rank_badges = []
    current_rank_num = 1
    for idx in range(len(comparison_df)):
        if idx > 0 and comparison_df.loc[idx, "Tổng_Điểm"] == comparison_df.loc[idx - 1, "Tổng_Điểm"]:
            rank_badges.append(rank_badges[-1])
        else:
            if idx > 0:
                current_rank_num += 1
            else:
                current_rank_num = 1
                
            if current_rank_num == 1:
                rank_badges.append("🥇 Hạng 1")
            elif current_rank_num == 2:
                rank_badges.append("🥈 Hạng 2")
            elif current_rank_num == 3:
                rank_badges.append("🥉 Hạng 3")
            else:
                rank_badges.append(f"Top {current_rank_num}")
            
    comparison_df.insert(0, "Xếp Hạng", rank_badges)
    
    total_minutes_all = comparison_df["Tổng Phút Làm Việc"].sum()
    comparison_df["Tỷ_Lệ_Thời_Gian"] = comparison_df["Tổng Phút Làm Việc"].apply(lambda x: (x / total_minutes_all) if total_minutes_all > 0 else 0)
    comparison_df["Chênh_Lệch_%"] = comparison_df["Tỷ_Lệ_Đóng_Góp"] - comparison_df["Tỷ_Lệ_Thời_Gian"]
    
    comparison_table = comparison_df[["Xếp Hạng", "Nhân Sự", "Tổng Phút Làm Việc", "Tỷ_Lệ_Thời_Gian", "Tổng_Điểm", "Tỷ_Lệ_Đóng_Góp", "Chênh_Lệch_%"]].copy()
    comparison_table.columns = ["Xếp Hạng", "Nhân Sự", "Tổng Thời Gian (Phút)", "Tỷ Lệ Thời Gian (%)", "Tổng Điểm", "Tỷ Lệ Sản Lượng (%)", "Chênh Lệch (Sản Lượng - Thời Gian)"]
    
    st.dataframe(
        comparison_table.style.format({
            "Tổng Thời Gian (Phút)": "{:,.0f}",
            "Tỷ Lệ Thời Gian (%)": "{:.2%}",
            "Tổng Điểm": "{:,.1f}",
            "Tỷ Lệ Sản Lượng (%)": "{:.2%}",
            "Chênh Lệch (Sản Lượng - Thời Gian)": "{:+.2%}"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.subheader("Biểu Đồ & Chi Tiết Tỷ Lệ Đóng Góp")
    
    with st.expander("🎨 Tùy Chỉnh Màu Sắc Biểu Đồ", expanded=False):
        while len(st.session_state.chart_colors) < len(all_staff_current):
            st.session_state.chart_colors.append("#3b82f6")
        
        color_cols = st.columns(min(len(all_staff_current), 4))
        for i, staff_name in enumerate(all_staff_current):
            col_idx = i % len(color_cols)
            with color_cols[col_idx]:
                st.session_state.chart_colors[i] = st.color_picker(f"Màu: {staff_name}", st.session_state.chart_colors[i], key=f"color_pick_{i}")
        if st.button("Lưu Màu Biểu Đồ", use_container_width=True):
            save_data()
            st.success("Đã cập nhật màu sắc biểu đồ!")
            st.rerun()

    chart_size = 3.0
    col_pie, col_details = st.columns([1, 1])
    
    with col_pie:
        fig, ax = plt.subplots(figsize=(chart_size, chart_size), dpi=300)
        current_colors = st.session_state.chart_colors[:len(summary)]
        
        max_pts = summary["Tổng_Điểm"].max()
        explode_values = [0.02 + 0.05 * (pts / max_pts) if max_pts > 0 else 0.0 for pts in summary["Tổng_Điểm"]]

        # Ẩn hoàn toàn nhãn đè trên biểu đồ tròn (autopct=None) để tránh chồng chéo số liệu
        wedges, texts = ax.pie(
            summary["Tổng_Điểm"], 
            labels=None, 
            autopct=None, 
            startangle=90, 
            colors=current_colors,
            explode=explode_values,
            shadow=False
        )
        
        ax.axis('equal')
        st.pyplot(fig)
        
    with col_details:
        st.markdown("#### 📌 Chi Tiết Điểm Số & Tỷ Lệ")
        current_colors = st.session_state.chart_colors[:len(summary)]
        for i, row in summary.iterrows():
            color_box = current_colors[i] if i < len(current_colors) else "#3b82f6"
            staff_name = row["Nhân Sự"]
            staff_pts = row["Tổng_Điểm"]
            staff_pct = row["Tỷ_Lệ_Đóng_Góp"] * 100
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 8px; background: rgba(255,255,255,0.7); padding: 8px 10px; border-radius: 6px;">
                <div style="width: 16px; height: 16px; background-color: {color_box}; border-radius: 4px; margin-right: 10px; flex-shrink: 0;"></div>
                <div style="font-size: 0.9rem;">
                    <b>{staff_name}</b>: {staff_pts:,.1f} điểm (<b>{staff_pct:.1f}%</b>)
                </div>
            </div>
            """, unsafe_allow_html=True)
