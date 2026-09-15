import datetime
import io
from PIL import Image
import base64

class VietnamTz(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=7)
    def tzname(self, dt):
        return "ICT"
    def dst(self, dt):
        return datetime.timedelta(0)

VN_TIMEZONE = VietnamTz()

def compress_image_to_base64(uploaded_file, max_size=(800, 800), quality=60):
    try:
        if uploaded_file is None:
            return None
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(max_size)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=quality)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception:
        return None

def calculate_exact_minutes(date_in_str, time_in_str, date_out_str, time_out_str):
    try:
        dt1 = datetime.datetime.strptime(f"{date_in_str} {time_in_str}", "%Y-%m-%d %H:%M:%S")
        dt2 = datetime.datetime.strptime(f"{date_out_str} {time_out_str}", "%Y-%m-%d %H:%M:%S")
        delta = dt2 - dt1
        minutes = int(delta.total_seconds() / 60)
        return max(0, minutes)
    except Exception:
        return 0

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
