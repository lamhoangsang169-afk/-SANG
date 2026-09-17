import streamlit as st
from database import get_rules_df_db

st.set_page_config(page_title="Tham Chiếu Định Mức", page_icon="⚖️", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Vui lòng đăng nhập ở trang chủ trước!")
    st.stop()

st.subheader("⚖️ Tham Chiếu Định Mức Công Việc")
rules_df = get_rules_df_db()
st.dataframe(rules_df, use_container_width=True, hide_index=True)
