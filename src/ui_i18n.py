"""Small UTF-8 translation loader, independent of Streamlit."""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "i18n.json"


def translate(key: str, language="ar", *, catalog=None) -> str:
    if language not in ("ar", "en"):
        raise ValueError("Unsupported language")
    if catalog is None:
        try:
            catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            catalog = {}
    if not isinstance(catalog, dict):
        return key
    for locale in (language, "en"):
        section = catalog.get(locale)
        if isinstance(section, dict):
            value = section.get(key)
            if isinstance(value, str) and value:
                return value
    return key
