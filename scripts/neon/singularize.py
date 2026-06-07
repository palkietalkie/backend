def singularize(name: str) -> str:
    """Crude best-effort English plural → singular ("users" → "user", "ies" → "y", "ses/xes/zes" → "se/xe/ze").

    Used by `table_to_class_name` to derive a singular `<Table>Row` TypedDict name from a plural table name. Schema is small; if the heuristic hits an irregular we hard-code a mapping rather than reaching for `inflect` or similar.
    """
    if name.endswith("ies"):
        return name[:-3] + "y"
    if name.endswith("ses") or name.endswith("xes") or name.endswith("zes"):
        return name[:-2]
    if name.endswith("s"):
        return name[:-1]
    return name
