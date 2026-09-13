import json
import os
from supabase import create_client

# Cấu hình kết nối Supabase của bạn
SUPABASE_URL = "https://xbozutjkiwnaoiluahq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhib3p1dGpraXl3bmFvaWx1YWhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwMjUwODIsImV4cCI6MjEwNDYwMTA4Mn0.ByzJ_xC9Cl3uUACmiIYD1xrHtDEs-fQBKZ4wSX-nlWc"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
DATA_FILE = "app_storage.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 1. Đẩy danh sách nhân sự
    if "staff_list" in data and data["staff_list"]:
        # Xóa dữ liệu cũ nếu có
        supabase.table("staff").delete().neq("id", 0).execute()
        for s in data["staff_list"]:
            supabase.table("staff").insert({"name": s}).execute()
        print("Đã đồng bộ xong Nhân sự!")

    # 2. Đẩy danh sách định mức công việc (rules)
    if "rules_df" in data and data["rules_df"]:
        supabase.table("rules").delete().neq("id", 0).execute()
        for r in data["rules_df"]:
            payload = {
                "stt": int(r.get("STT", r.get("stt", 1))),
                "hang_muc": r.get("Hạng Mục Công Việc", r.get("hang_muc", "")),
                "don_vi": r.get("Đơn Vị", r.get("don_vi", "Cái")),
                "he_so_diem": float(r.get("Hệ Số Điểm", r.get("he_so_diem", 1.0))),
                "ghi_chu": r.get("Ghi Chú", r.get("ghi_chu", ""))
            }
            supabase.table("rules").insert(payload).execute()
        print("Đã đồng bộ xong Quy tắc/Định mức!")

    # 3. Đẩy lịch sử sản lượng (input_df)
    if "input_df" in data and data["input_df"]:
        for row in data["input_df"]:
            payload = {
                "ngay": str(row.get("Ngày", "")),
                "thoi_gian": str(row.get("Thời Gian", "00:00:00")),
                "nhan_su": str(row.get("Nhân Sự", "")),
                "hang_muc_cong_viec": str(row.get("Hạng Mục Công Việc", "")),
                "hinh_anh_url": str(row.get("Hình Ảnh", "")), # Lưu ý: Nếu trước đó lưu base64, chuỗi sẽ rất dài
                "don_vi": str(row.get("Đơn Vị", "")),
                "so_luong": int(row.get("Số Lượng", 0) or 0),
                "he_so_diem": float(row.get("Hệ Số Điểm", 1.0) or 1.0),
                "tong_diem": float(row.get("Tổng Điểm", 0.0) or 0.0),
                "ghi_chu": str(row.get("Ghi Chú", "")),
                "is_deleted": False
            }
            supabase.table("production_logs").insert(payload).execute()
        print("Đã đồng bộ xong Lịch sử sản lượng!")

    # 4. Đẩy lịch sử chấm công (attendance_df)
    if "attendance_df" in data and data["attendance_df"]:
        for row in data["attendance_df"]:
            payload = {
                "ngay": str(row.get("Ngày", "")),
                "nhan_su": str(row.get("Nhân Sự", "")),
                "gio_vao_ca": str(row.get("Giờ Vào Ca", "")),
                "gio_ra_ca": str(row.get("Giờ Ra Ca", "")),
                "so_phut_lam_viec": int(row.get("Số Phút Làm Việc", 0) or 0),
                "ghi_chu": str(row.get("Ghi Chú", ""))
            }
            supabase.table("attendance").insert(payload).execute()
        print("Đã đồng bộ xong Lịch sử chấm công!")
        
    print("Hoàn tất quá trình chuyển dữ liệu cũ lên Supabase!")
else:
    print("Không tìm thấy file app_storage.json trong thư mục.")
