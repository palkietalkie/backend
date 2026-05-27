import json
from dataclasses import asdict, is_dataclass
from typing import Any

from pydantic import TypeAdapter, ValidationError

_DICT_ADAPTER: TypeAdapter[dict[str, Any]] = TypeAdapter(dict[str, Any])


def coerce_to_dict(obj: object) -> dict[str, Any]:
    """Coerce one of the SDK's attrs-based payload objects to a plain dict.

    The SDK doesn't ship py.typed, so the input is `object`. We try strongly-typed conversions first (dataclass → asdict; cattrs.unstructure → dict). Anything that doesn't validate to dict[str, Any] via Pydantic collapses to {} so callers see a stable shape.
    """
    if obj is None:
        return {}
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    candidate: object = obj
    try:
        import cattrs

        candidate = cattrs.unstructure(obj)
    except ImportError:
        pass
    # Round-trip through JSON to escape pyright's Any-narrowing trap: json.dumps takes any json-serializable value; json.loads returns a typed value that, when fed to Pydantic, validates cleanly as dict[str, Any].
    try:
        serialized = json.dumps(candidate, default=lambda o: getattr(o, "__dict__", str(o)))
        return _DICT_ADAPTER.validate_python(json.loads(serialized))
    except TypeError, ValueError, ValidationError:
        return {}
