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
    return catalog.get(language, {}).get(key, catalog.get("en", {}).get(key, key))
