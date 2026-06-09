import re

from scripts.neon.singularize import singularize


def table_to_class_name(table: str) -> str:
    """`users` → `UserRow`, `persona_likes` → `PersonaLikeRow`.

    Pure name mangling — never hits the DB. Result is the TypedDict class name emitted into the generated `rows.py`.
    """
    base = singularize(table)
    parts = re.split(r"_+", base)
    return "".join(p.capitalize() for p in parts if p) + "Row"
