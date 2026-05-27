from typing import Any


def coerce_to_dict(obj: Any) -> dict[str, Any]:
    """Coerce one of the SDK's attrs-based payload objects to a plain dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    try:
        import cattrs

        result = cattrs.unstructure(obj)
        return result if isinstance(result, dict) else dict(getattr(obj, "__dict__", {}) or {})
    except ImportError:
        return dict(getattr(obj, "__dict__", {}) or {})
