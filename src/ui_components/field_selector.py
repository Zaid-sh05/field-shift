"""GeoJSON options preserve source IDs; map rendering accepts existing Folium maps."""


def field_options(geojson, language="ar"):
    return {f["properties"]["field_id"]: f["properties"].get(f"name_{language}") or f["properties"]["field_id"]
            for f in geojson.get("features", [])}


def render_map(folium_map, *, key="role6_field_map"):
    try:
        from streamlit_folium import st_folium
    except ImportError:
        return {"available": False, "error": "streamlit-folium is unavailable"}
    return st_folium(folium_map, height=420, use_container_width=True, key=key)
