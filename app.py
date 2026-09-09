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

class VietnamTz(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=7)
    def tzname(self, dt):
        return "ICT"
    def dst(self, dt):
        return datetime.timedelta(0)

VN_TIMEZONE = VietnamTz()

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

default_staff_list = ["Nguyễn Hữu Khang Tôn Đức", "Nguyễn Đức Anh Tiến", "Trần Gia Bảo"]
default_chart_colors = ["#ff4b4b", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]

def load_data():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass
    return {}

def save_data():
    data = {
        "rules_df": st.session_state.rules_df.to_dict(orient="records") if "rules_df" in st.session_state else master_rules,
        "input_df": st.session_state.input_df.to_dict(orient="records") if "input_df" in st.session_state else [],
        "attendance_df": st.session_state.attendance_df.to_dict(orient="records") if "attendance_df" in st.session_state else [],
        "deleted_input_df": st.session_state.deleted_input_df.to_dict(orient="records") if "deleted_input_df" in st.session_state else [],
        "staff_list": st.session_state.staff_list if "staff_list" in st.session_state else default_staff_list,
        "chart_colors": st.session_state.chart_colors if "chart_colors" in st.session_state else default_chart_colors,
        "primary_color": st.session_state.primary_color if "primary_color" in st.session_state else "#ff4b4b",
        "bg_color": st.session_state.bg_color if "bg_color" in st.session_state else "#ffffff",
        "sidebar_bg": st.session_state.sidebar_bg if "sidebar_bg" in st.session_state else "#f0f2f6",
        "sidebar_opacity": st.session_state.sidebar_opacity if "sidebar_opacity" in st.session_state else 0.9,
        "text_color": st.session_state.text_color if "text_color" in st.session_state else "#31333F",
        "bg_image_base64": st.session_state.get("bg_image_base64", None),
        "avatar_base64": st.session_state.get("avatar_base64", None),
        "current_menu": st.session_state.get("current_menu", "1. Nhập Sản Lượng")
    }
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception:
        pass

# Cơ chế tự động lắng nghe và nạp lại tệp dữ liệu ngầm mỗi khi có tương tác
saved_data = load_data()

if "rules_df" in saved_data and saved_data["rules_df"]:
    st.session_state.rules_df = pd.DataFrame(saved_data["rules_df"])
else:
    if "rules_df" not in st.session_state:
        st.session_state.rules_df = pd.DataFrame(master_rules)

if "input_df" in saved_data:
    st.session_state.input_df = pd.DataFrame(saved_data["input_df"])
else:
    if "input_df" not in st.session_state:
        st.session_state.input_df = pd.DataFrame(columns=["STT", "Ngày", "Nhân Sự", "Hạng Mục Công Việc", "Hình Ảnh", "Đơn Vị", "Số Lượng", "Hệ Số Điểm", "Tổng Điểm", "Ghi Chú"])

if "attendance_df" in saved_data:
    st.session_state.attendance_df = pd.DataFrame(saved_data["attendance_df"])
else:
    if "attendance_df" not in st.session_state:
        st.session_state.attendance_df = pd.DataFrame(columns=["STT", "Ngày", "Nhân Sự", "Giờ Vào Ca", "Giờ Ra Ca", "Ghi Chú"])

if "deleted_input_df" in saved_data:
    st.session_state.deleted_input_df = pd.DataFrame(saved_data["deleted_input_df"])
else:
    if "deleted_input_df" not in st.session_state:
        st.session_state.deleted_input_df = pd.DataFrame(columns=st.session_state.input_df.columns)

st.session_state.staff_list = saved_data.get("staff_list", default_staff_list)
st.session_state.chart_colors = saved_data.get("chart_colors", default_chart_colors)
st.session_state.primary_color = saved_data.get("primary_color", "#ff4b4b")
st.session_state.bg_color = saved_data.get("bg_color", "#ffffff")
st.session_state.sidebar_bg = saved_data.get("sidebar_bg", "#f0f2f6")
st.session_state.sidebar_opacity = saved_data.get("sidebar_opacity", 0.9)
st.session_state.text_color = saved_data.get("text_color", "#31333F")
st.session_state.bg_image_base64 = saved_data.get("bg_image_base64", None)
st.session_state.avatar_base64 = saved_data.get("avatar_base64", None)
st.session_state.current_menu = saved_data.get("current_menu", "1. Nhập Sản Lượng")

if not st.session_state.input_df.empty:
    st.session_state.input_df["STT"] = range(1, len(st.session_state.input_df) + 1)
if not st.session_state.attendance_df.empty:
    st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)

bg_style = f"background-color: {st.session_state.bg_color};"
if st.session_state.bg_image_base64:
    bg_style = f"background-image: url(data:image/png;base64,{st.session_state.bg_image_base64}); background-size: cover; background-repeat: no-repeat; background-position: center; background-attachment: fixed;"

def hex_to_rgba(hex_str, opacity):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"
    except:
        return f"rgba(240, 242, 246, {opacity})"

sidebar_rgba = hex_to_rgba(st.session_state.sidebar_bg, st.session_state.sidebar_opacity)

st.markdown(f"""
<style>
    .stApp {{
        {bg_style}
        color: {st.session_state.text_color} !important;
    }}
    
    p, span, label, div, h1, h2, h3, h4, h5, h6, 
    .stMarkdown, [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"], [data-testid="stMetricValue"], [data-testid="stMetricLabel"],
    [data-testid="stWidgetLabel"] *, .streamlit-expanderHeader *,
    [data-testid="stDataEditor"] *, [data-testid="stDataFrame"] *, [data-testid="stTable"] *,
    .stSelectbox *, .stDateInput *, .stNumberInput *, .stTextInput *, .stTimeInput *,
    table, th, td, tr, [class*="css-"], 
    div[data-baseweb="select"] *, span[title], 
    div[data-testid="stDataFrame"] div, div[data-testid="stDataEditor"] div,
    canvas {{
        color: {st.session_state.text_color} !important;
    }}
    
    h1 {{
        color: {st.session_state.primary_color} !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: {sidebar_rgba} !important;
        backdrop-filter: blur(8px);
    }}
    
    [data-testid="stSidebar"] > div:first-child {{
        display: flex;
        flex-direction: column;
        height: 100vh;
        overflow-y: auto;
        padding-bottom: 50px;
    }}
    
    [data-testid="stSidebar"] * {{
        color: {st.session_state.text_color} !important;
    }}
    
    .fixed-avatar-container {{
        position: sticky;
        top: 0px;
        z-index: 999999;
        background-color: {sidebar_rgba};
        padding-top: 15px;
        padding-bottom: 15px;
        border-bottom: 2px solid {st.session_state.primary_color};
        margin-bottom: 15px;
        text-align: center;
    }}

    .avatar-wrapper {{
        position: relative;
        width: 160px;
        height: 160px;
        margin: 0 auto;
    }}
    
    .avatar-popover-wrapper {{
        position: absolute;
        bottom: 4px;
        right: 12px;
        z-index: 9999999;
    }}
    .avatar-popover-wrapper [data-testid="stPopover"] button {{
        background-color: #ffffff !important;
        border: 2px solid {st.session_state.primary_color} !important;
        border-radius: 50% !important;
        width: 34px !important;
        height: 34px !important;
        padding: 0px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }}
    .avatar-popover-wrapper [data-testid="stPopover"] button p {{
        display: none !important;
    }}
    .avatar-popover-wrapper [data-testid="stPopover"] button::after {{
        content: "⋮";
        font-size: 18px;
        font-weight: bold;
        color: #333333;
        line-height: 1;
    }}

    .staff-badge-container {{
        background-color: rgba(255, 255, 255, 0.7);
        border-left: 4px solid {st.session_state.primary_color};
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 0.95rem;
        backdrop-filter: blur(4px);
    }}

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

# Tích hợp bộ lắng nghe sự kiện click chuột toàn trang (Global Click Listener) bằng JavaScript:
# Bất cứ khi nào bạn nhấn chuột/chạm vào màn hình, trang sẽ tự động gọi trigger làm mới lại ứng dụng ngầm.
st.markdown("""
<script>
    document.addEventListener('click', function(event) {
        // Gửi tín hiệu tương tác ngầm để Streamlit nhận diện và đồng bộ trạng thái mới
        const target = window.parent.document;
        if (target) {
            const mainContainer = target.querySelector('.main');
            if (mainContainer) {
                // Tạo một sự kiện click giả lập nhẹ hoặc tương tác DOM giúp đánh thức kết nối WebSocket
                window.parent.dispatchEvent(new Event('focus'));
            }
        }
    }, true);
</script>
""", unsafe_allow_html=True)

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
    st.markdown("### ⚙️ Cấu Hình Hệ Thống")
    if st.button("🎨 Cài Đặt Giao Diện", use_container_width=True):
        st.session_state.current_menu = "5. Cài Đặt Giao Diện"
        save_data()
        st.rerun()

menu = st.session_state.current_menu

st.title("QUẢN LÝ & CHẤM ĐIỂM SẢN LƯỢNG")

staff_joined = " | ".join([f"**{s}**" for s in st.session_state.staff_list])
st.markdown(f"""
<div class="staff-badge-container">
    👥 <b>Nhân sự hệ thống:</b> {staff_joined}
</div>
""", unsafe_allow_html=True)

if menu == "1. Nhập Sản Lượng":
    st.subheader("Chấm Công Ca Làm Việc (Múi giờ VN: GMT+7)")
    now_vn = datetime.datetime.now(VN_TIMEZONE)
    today_str = str(now_vn.date())
    
    with st.form("attendance_form"):
        att_col1, att_col2, att_col3 = st.columns(3)
        with att_col1:
            att_date = st.date_input("Ngày chấm công", now_vn.date(), key="att_date")
        with att_col2:
            att_staff = st.selectbox("Nhân sự", st.session_state.staff_list, key="att_staff")
        with att_col3:
            att_note = st.text_input("Ghi chú ca", "", key="att_note")
            
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            check_in_clicked = st.form_submit_button("🟢 Check-in (Vào ca tự động)", use_container_width=True)
        with col_btn2:
            check_out_clicked = st.form_submit_button("🔴 Check-out (Kết thúc ca tự động)", use_container_width=True)
            
        current_time_str = now_vn.strftime("%H:%M:%S")
        
        if check_in_clicked:
            new_att_stt = len(st.session_state.attendance_df) + 1
            new_att_row = {
                "STT": new_att_stt,
                "Ngày": str(att_date),
                "Nhân Sự": att_staff,
                "Giờ Vào Ca": current_time_str,
                "Giờ Ra Ca": "Chưa kết thúc",
                "Ghi Chú": att_note
            }
            st.session_state.attendance_df = pd.concat([st.session_state.attendance_df, pd.DataFrame([new_att_row])], ignore_index=True)
            st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)
            save_data()
            st.success(f"Đã ghi nhận **Vào ca** cho **{att_staff}** lúc {current_time_str}!")
            st.rerun()
            
        if check_out_clicked:
            if not st.session_state.attendance_df.empty:
                mask = (st.session_state.attendance_df["Nhân Sự"] == att_staff) & \
                       (st.session_state.attendance_df["Ngày"] == str(att_date)) & \
                       (st.session_state.attendance_df["Giờ Ra Ca"] == "Chưa kết thúc")
                if mask.any():
                    st.session_state.attendance_df.loc[mask, "Giờ Ra Ca"] = current_time_str
                    save_data()
                    st.success(f"Đã ghi nhận **Kết thúc ca** cho **{att_staff}** lúc {current_time_str}!")
                    st.rerun()
                else:
                    new_att_stt = len(st.session_state.attendance_df) + 1
                    new_att_row = {
                        "STT": new_att_stt,
                        "Ngày": str(att_date),
                        "Nhân Sự": att_staff,
                        "Giờ Vào Ca": "--",
                        "Giờ Ra Ca": current_time_str,
                        "Ghi Chú": att_note
                    }
                    st.session_state.attendance_df = pd.concat([st.session_state.attendance_df, pd.DataFrame([new_att_row])], ignore_index=True)
                    st.session_state.attendance_df["STT"] = range(1, len(st.session_state.attendance_df) + 1)
                    save_data()
                    st.success(f"Đã ghi nhận **Kết thúc ca** cho **{att_staff}** lúc {current_time_str}!")
                    st.rerun()
            else:
                st.warning("Chưa có lịch sử chấm công vào ca nào để kết thúc!")

    if not st.session_state.attendance_df.empty:
        with st.expander("📋 Xem Lịch Sử Chấm Công", expanded=False):
            st.dataframe(st.session_state.attendance_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader(f"Nhập Sản Lượng Hàng Ngày (Ngày: {today_str})")
    
    active_staff = []
    inactive_staff = []
    
    if not st.session_state.attendance_df.empty:
        today_att = st.session_state.attendance_df[st.session_state.attendance_df["Ngày"] == today_str]
        checked_in_set = set(today_att[today_att["Giờ Vào Ca"] != "--"]["Nhân Sự"].tolist())
    else:
        checked_in_set = set()

    for s in st.session_state.staff_list:
        if s in checked_in_set:
            active_staff.append(s)
        else:
            inactive_staff.append(s)

    status_html = ""
    for s in active_staff:
        status_html += f"🟢 **{s}** - Đang Làm Việc<br>"
    for s in inactive_staff:
        status_html += f"🔴 **{s}** - không hoạt động<br>"
        
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.7); padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(4px);">
        {status_html}
    </div>
    """, unsafe_allow_html=True)

    if not active_staff:
        st.warning(f"⚠️ Hôm nay ({today_str}) chưa có nhân sự nào **Check-in (Vào ca)**. Vui lòng thực hiện Check-in ở phần trên để có thể nhập sản lượng!")
    else:
        st.info("💡 Mẹo: Có thể chụp ảnh trực tiếp từ camera điện thoại hoặc tải file ảnh đính kèm. *Lưu ý: Bắt buộc phải chọn Nhân sự, Hạng mục và tải ảnh đính kèm/chụp ảnh.*")
        
        with st.form("entry_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                ngay = st.date_input("Ngày làm việc", now_vn.date(), disabled=True)
            with col2:
                nhan_su = st.selectbox("Nhân sự thực hiện (Chỉ hiển thị người đang làm việc)", active_staff)
            with col3:
                danh_sach_hang_muc = st.session_state.rules_df["Hạng Mục Công Việc"].tolist()
                hang_muc = st.selectbox("Hạng mục công việc", danh_sach_hang_muc)
                
            col_img, col_qty, col_note = st.columns([2, 2, 2])
            with col_img:
                img_source = st.radio("Nguồn ảnh:", ["Tải lên / Kéo thả", "Chụp trực tiếp"], horizontal=True)
                if img_source == "Chụp trực tiếp":
                    record_image = st.camera_input("Chụp ảnh công việc (Bắt buộc)")
                else:
                    record_image = st.file_uploader("Tải ảnh đính kèm (Bắt buộc)", type=["png", "jpg", "jpeg"], key="record_img")
                    
            with col_qty:
                so_luong = st.number_input("Số lượng thực tế", min_value=1, value=100, step=1)
            with col_note:
                ghi_chu = st.text_input("Ghi chú", "")
                
            submitted = st.form_submit_button("📊 Báo Cáo Sản Lượng", use_container_width=True)

            if submitted:
                is_valid = True
                missing_fields = []
                if not nhan_su:
                    is_valid = False
                    missing_fields.append("Nhân sự thực hiện")
                if not hang_muc:
                    is_valid = False
                    missing_fields.append("Hạng mục công việc")
                if record_image is None:
                    is_valid = False
                    missing_fields.append("Ảnh đính kèm / Chụp ảnh công việc")

                if not is_valid:
                    st.error(f"⚠️ Vui lòng hoàn thành các mục bắt buộc sau trước khi báo cáo: {', '.join(missing_fields)}")
                else:
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
                        "Ngày": today_str,
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
                    st.success(f"Đã báo cáo sản lượng thành công cho **{nhan_su}**! Tổng điểm: **{tong_diem} điểm**")
                    st.rerun()

    st.markdown("---")
    st.subheader("Danh Sách Sản Lượng & Đối Chiếu Ảnh Trực Tiếp")
    
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
            
            # THANH TRƯỢT TÙY CHỈNH PHÓNG TO / THU NHỎ ẢNH THỜI GIAN THỰC
            zoom_level = st.slider("🔍 Thanh trượt phóng to / thu nhỏ ảnh toàn bộ danh sách:", min_value=60, max_value=400, value=90, step=10)
            
            with st.form("input_delete_form"):
                for idx, row in filtered_df.iterrows():
                    c_check, c_info, c_img = st.columns([0.6, 7.4, 2])
                    
                    with c_check:
                        is_selected = st.checkbox("Chọn", key=f"chk_{row['STT']}", label_visibility="collapsed")
                        filtered_df.loc[idx, "Chọn_Xóa"] = is_selected
                        
                    with c_info:
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.85); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); font-size: 0.88rem;">
                            <b>STT: {row['STT']}</b> | 📅 {row['Ngày']} | 👤 <b>{row['Nhân Sự']}</b><br>
                            📌 {row['Hạng Mục Công Việc']} | 📦 <b>{row['Số Lượng']} {row['Đơn Vị']}</b> (⭐ {row['Tổng Điểm']} điểm)<br>
                            💬 <i>{row['Ghi Chú'] if row['Ghi Chú'] else 'Không có ghi chú'}</i>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c_img:
                        img_b64_val = row["Hình Ảnh"]
                        if img_b64_val and isinstance(img_b64_val, str) and len(img_b64_val) > 10:
                            try:
                                pure_b64 = img_b64_val.split(",")[1] if "," in img_b64_val else img_b64_val
                                pure_b64 += "=" * (-len(pure_b64) % 4)
                                img_bytes = base64.b64decode(pure_b64)
                                
                                # Chèn ảnh với kích thước tùy chỉnh từ thanh trượt real-time
                                st.image(img_bytes, width=zoom_level)
                                
                                # Hỗ trợ xem chi tiết lớn hơn nhanh chóng bằng popup tích hợp ngay cạnh
                                with st.popover("🔎 Xem chi tiết", use_container_width=True):
                                    st.image(img_bytes, caption=f"Ảnh chi tiết bản ghi STT {row['STT']}", use_container_width=True)
                            except Exception:
                                st.text("Lỗi ảnh")
                        else:
                            st.text("Không có ảnh")
                            
                    st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)
                    
                delete_submitted = st.form_submit_button("🗑️ Xóa Các Dòng Đã Tích Chọn", use_container_width=True)
                if delete_submitted:
                    selected_rows = filtered_df[filtered_df["Chọn_Xóa"] == True]
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
                        st.warning("Vui lòng tích chọn ít nhất một dòng để xóa!")
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
        
        st.markdown("---")
        st.subheader("Biểu Đồ Tỷ Lệ Đóng Góp Điểm Thi Đua")
        
        with st.expander("🎨 Tùy Chỉnh Màu Sắc Biểu Đồ Cho Từng Nhân Sự", expanded=False):
            while len(st.session_state.chart_colors) < len(st.session_state.staff_list):
                st.session_state.chart_colors.append("#3b82f6")
            
            color_cols = st.columns(len(st.session_state.staff_list))
            for i, staff_name in enumerate(st.session_state.staff_list):
                with color_cols[i]:
                    st.session_state.chart_colors[i] = st.color_picker(f"Màu: {staff_name}", st.session_state.chart_colors[i], key=f"color_pick_{i}")
            if st.button("Lưu Màu Biểu Đồ"):
                save_data()
                st.success("Đã cập nhật màu sắc biểu đồ!")
                st.rerun()

        fig, ax = plt.subplots(figsize=(5, 5))
        
        current_colors = st.session_state.chart_colors[:len(summary)]
        
        max_pts = summary["Tổng_Điểm"].max()
        explode_values = []
        for pts in summary["Tổng_Điểm"]:
            if max_pts > 0:
                explode_values.append(0.01 + 0.12 * (pts / max_pts))
            else:
                explode_values.append(0.0)

        wedges, texts, autotexts = ax.pie(
            summary["Tổng_Điểm"], 
            labels=None, 
            autopct='%1.1f%%', 
            startangle=90, 
            colors=current_colors,
            explode=explode_values,
            shadow=True
        )
        
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.axis('equal')
        
        col_chart, col_legend = st.columns([1, 1])
        with col_chart:
            st.pyplot(fig)
            
        with col_legend:
            st.markdown("#### 📌 Chú Thích Nhân Sự")
            for i, row in summary.iterrows():
                color_box = current_colors[i] if i < len(current_colors) else "#3b82f6"
                staff_name = row["Nhân Sự"]
                staff_pts = row["Tổng_Điểm"]
                staff_pct = row["Tỷ_Lệ_Đóng_Góp"] * 100
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 12px; background: rgba(255,255,255,0.7); padding: 8px 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="width: 20px; height: 20px; background-color: {color_box}; border-radius: 4px; margin-right: 12px; flex-shrink: 0; border: 1px solid rgba(0,0,0,0.2);"></div>
                    <div style="font-size: 0.95rem;">
                        <b>{staff_name}</b><br>
                        <span style="font-size: 0.85rem; opacity: 0.8;">{staff_pts:,.1f} điểm ({staff_pct:.1f}%)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
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
    
    with st.form("rules_form"):
        edited_rules = st.data_editor(
            st.session_state.rules_df, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="rules_editor",
            hide_index=True
        )
        save_rules_btn = st.form_submit_button("💾 Lưu Thay Đổi Định Mức", use_container_width=True)
        if save_rules_btn:
            edited_rules["STT"] = range(1, len(edited_rules) + 1)
            st.session_state.rules_df = edited_rules
            save_data()
            st.success("Đã lưu và cập nhật danh mục định mức điểm thành công!")
            st.rerun()

elif menu == "4. Thùng Rác / Khôi Phục Sản Lượng":
    st.header("Thùng Rác & Khôi Phục Bản Ghi")
    st.markdown("Quản lý các bản ghi sản lượng đã xóa. Có thể khôi phục hoặc xóa vĩnh viễn.")
    
    if not st.session_state.deleted_input_df.empty:
        st.session_state.deleted_input_df["STT"] = range(1, len(st.session_state.deleted_input_df) + 1)
        trash_display = st.session_state.deleted_input_df.copy()
        trash_display.insert(0, "Chọn", False)
        
        with st.form("trash_form"):
            edited_trash = st.data_editor(
                trash_display.drop(columns=["Hình Ảnh"], errors="ignore"),
                hide_index=True,
                use_container_width=True,
                key="trash_editor"
            )
            
            col_act1, col_act2 = st.columns(2)
            
            with col_act1:
                restore_btn = st.form_submit_button("📥 Khôi Phục Dòng Đã Chọn", use_container_width=True)
            with col_act2:
                delete_perm_btn = st.form_submit_button("🔥 Xóa Vĩnh Viễn Dòng Đã Chọn", use_container_width=True)
                
            if restore_btn:
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

            if delete_perm_btn:
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
    st.subheader("Tùy Chỉnh Màu Sắc Giao Diện")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.session_state.primary_color = st.color_picker("Màu chủ đạo", st.session_state.primary_color)
        st.session_state.bg_color = st.color_picker("Màu nền trang", st.session_state.bg_color)
    with col_c2:
        st.session_state.sidebar_bg = st.color_picker("Màu nền thanh bên", st.session_state.sidebar_bg)
        st.session_state.text_color = st.color_picker("Màu chữ", st.session_state.text_color)
        
    st.session_state.sidebar_opacity = st.slider(
        "Độ trong suốt của thanh Sidebar (0.0 = trong suốt hoàn toàn thấy ảnh nền, 1.0 = đặc màu)", 
        min_value=0.0, max_value=1.0, value=float(st.session_state.sidebar_opacity), step=0.05
    )

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

    st.markdown("---")
    if st.button("💾 Lưu & Áp Dụng Thay Đổi"):
        save_data()
        st.success("Đã lưu và cập nhật giao diện thực tế thành công!")
        st.rerun()
