"""Field Shift: Streamlit entry point. Role 1 wires data in; Role 6 builds the real UI."""
import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

DATA = Path(__file__).parent / "data"
CONTRACT = ["fields.geojson", "climate_monthly.csv", "sat_monthly.csv", "field_history.csv",
            "field_static.csv", "crops.csv", "soil.json", "rotations.json", "explanations.json"]

st.set_page_config(page_title="Field Shift", page_icon="🌾", layout="wide")
st.markdown("<style>.block-container{direction:rtl;text-align:right}</style>", unsafe_allow_html=True)

st.title("Field Shift: مستكشف الدورات الزراعية")
st.caption("هاي الأداة بتساعدك تشوف الخيارات، والقرار إلك وللمرشد الزراعي.")


@st.cache_data
def load_fields():
    return json.loads((DATA / "fields.geojson").read_text(encoding="utf-8"))


fields = load_fields()
m = folium.Map(tiles=None)
folium.TileLayer(  # keyless satellite basemap (CARTO now needs an API key)
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery").add_to(m)
layer = folium.GeoJson(fields, tooltip=folium.GeoJsonTooltip(["name_ar"]),
                       style_function=lambda _: {"color": "#ffd60a", "weight": 3, "fillOpacity": 0.1}).add_to(m)
m.fit_bounds(layer.get_bounds())
st_folium(m, height=420, use_container_width=True)

st.subheader("حالة ملفات البيانات")
st.dataframe(pd.DataFrame({"file": CONTRACT, "ready": [(DATA / f).exists() for f in CONTRACT]}),
             hide_index=True)
