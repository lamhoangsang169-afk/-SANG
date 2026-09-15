@st.cache_data(ttl=150, show_spinner=False)
def get_production_logs_by_date_range(start_date, end_date):
    if supabase is None:
        return pd.DataFrame()
    try:
        # Truy vấn trực tiếp theo khoảng thời gian từ Supabase, giới hạn tối đa 2000 dòng an toàn cho RAM
        res = supabase.table("production_logs")\
            .select("*")\
            .eq("is_deleted", False)\
            .gte("ngay", str(start_date))\
            .lte("ngay", str(end_date))\
            .order("id", desc=True)\
            .limit(2000)\
            .execute()
            
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "id": "db_id", "ngay": "Ngày", "thoi_gian": "Thời Gian", "nhan_su": "Nhân Sự",
                "hang_muc_cong_viec": "Hạng Mục Công Việc", "hinh_anh_url": "Hình Ảnh", "don_vi": "Đơn Vị",
                "so_luong": "Số Lượng", "he_so_diem": "Hệ Số Điểm", "tong_diem": "Tổng Điểm", "ghi_chu": "Ghi Chú"
            })
            df.insert(0, "STT", range(len(df), 0, -1))
            return df
    except Exception:
        pass
    return pd.DataFrame()
