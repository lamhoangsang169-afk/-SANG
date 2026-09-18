import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Khởi tạo kết nối Supabase an toàn từ st.secrets
def init_supabase():
    try:
        url = st.secrets["supabase"]["SUPABASE_URL"]
        key = st.secrets["supabase"]["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()
is_supabase_connected = supabase is not None

def init_db_data():
    pass

@st.cache_data(ttl=600, show_spinner=False)
def get_staff_df_db():
    if supabase is None:
        return pd.DataFrame(columns=["id", "name"])
    try:
        res = supabase.table("staff").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            if "name" not in df.columns and "ten" in df.columns:
                df = df.rename(columns={"ten": "name"})
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "name"])

def get_staff_list_db():
    df = get_staff_df_db()
   
