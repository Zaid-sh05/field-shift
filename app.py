"""Field Shift: Streamlit entry point. Role 1 wires data in; Role 6 owns the UI (src/ui.py)."""
import streamlit as st

from src.ui import render_frontend

st.set_page_config(page_title="Field Shift", page_icon="🌾", layout="wide")
render_frontend()  # production mode: real data only, never the demo fixtures
