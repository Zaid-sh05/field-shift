"""Standalone Role 6 preview; reads the repository's real data through its adapter."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.ui import FileDataAdapter, render_frontend

st.set_page_config(page_title="Field Shift — Role 6 Preview", page_icon="🌾", layout="wide")
render_frontend(adapter=FileDataAdapter(ROOT / "data"), preview=True)
