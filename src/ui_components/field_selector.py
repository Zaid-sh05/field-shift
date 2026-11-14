"""GeoJSON options preserve source IDs; map rendering accepts existing Folium maps."""
from math import isfinite
from html import escape


def valid_polygon(geometry):
    if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
        return False
    rings = geometry.get("coordinates")
    if not isinstance(rings, list) or not rings:
        return False
    for ring in rings:
        if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
            return False
        for point in ring:
            if not isinstance(point, list) or len(point) < 2:
                return False
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) for v in point[:2]):
                return False
            if not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90):
                return False
    return True


def reliable_name(value, language):
    if not isinstance(value, str) or not value.strip():
        return False
    if any(char in value for char in ("\ufffd", "Ø", "Ù", "Ã", "Â")):
        return False
    return language != "ar" or any("\u0600" <= c <= "\u06ff" for c in value)


def field_options(geojson, language="ar"):
    return {f["properties"]["field_id"]: (f["properties"][f"name_{language}"] if reliable_name(f["properties"].get(f"name_{language}"), language) else f["properties"]["field_id"])
            for f in geojson.get("features", [])}


def render_map(folium_map, *, key="role6_field_map"):
    try:
        from streamlit_folium import st_folium
    except ImportError:
        return {"available": False, "error": "streamlit-folium is unavailable"}
    return st_folium(folium_map, height=420, use_container_width=True, key=key, returned_objects=[])


def build_map(geojson, selected=None, language="ar"):
    import folium
    m = folium.Map(tiles=None)
    folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri World Imagery").add_to(m)
    options = field_options(geojson, language)
    for feature in geojson["features"]:
        fid = feature["properties"]["field_id"]
        active = fid == selected
        folium.GeoJson(feature, tooltip=escape(options[fid]), style_function=lambda _, active=active: {
            "color": "#ffffff" if active else "#ffd60a", "weight": 5 if active else 2,
            "fillColor": "#2e8540", "fillOpacity": 0.5 if active else 0.1,
            "dashArray": None if active else "6 3"}).add_to(m)
    m.fit_bounds(folium.GeoJson(geojson).get_bounds())
    return m
