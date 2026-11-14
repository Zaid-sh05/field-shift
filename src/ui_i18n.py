"""Small UTF-8 translation loader, independent of Streamlit."""
import json
from functools import lru_cache
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "i18n.json"


@lru_cache(maxsize=1)
def _catalog():
    """Parse i18n.json once per process instead of once per label."""
    try:
        return json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def translate(key: str, language="ar", *, catalog=None) -> str:
    if language not in ("ar", "en"):
        raise ValueError("Unsupported language")
    if catalog is None:
        catalog = _catalog()
    if not isinstance(catalog, dict):
        return key
    for locale in (language, "en"):
        section = catalog.get(locale)
        if isinstance(section, dict):
            value = section.get(key)
            if isinstance(value, str) and value:
                return value
    return key
