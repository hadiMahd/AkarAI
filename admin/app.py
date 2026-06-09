import os

import requests
import streamlit as st

st.set_page_config(page_title="AkarAI Admin", page_icon="🏢", layout="wide")

st.title("AkarAI Platform Admin")
st.caption("Phase 1 — Infrastructure Foundation")

col1, col2, col3 = st.columns(3)

backend_url = os.getenv("BACKEND_URL", "http://backend:8000")

with col1:
    st.subheader("Backend Status")
    try:
        resp = requests.get(f"{backend_url}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            st.success(f"Healthy — {data.get('service', 'backend')}")
        else:
            st.error(f"Unhealthy (HTTP {resp.status_code})")
    except Exception as e:
        st.error(f"Unreachable: {e}")

with col2:
    st.subheader("Dependencies")
    try:
        resp = requests.get(f"{backend_url}/ready", timeout=5)
        data = resp.json()
        st.json(data.get("checks", {}))
    except Exception as e:
        st.warning(f"Cannot check: {e}")

with col3:
    st.subheader("Quick Links")
    st.markdown("- [User App](http://localhost:3000)")
    st.markdown("- [Agency App](http://localhost:3001)")
    st.markdown("- [MinIO Console](http://localhost:9001)")
    st.markdown("- [API Docs](http://localhost:8000/docs)")

st.divider()
st.metric("Environment", os.getenv("APP_ENV", "development"))
