import uuid

_PRESET_NAMESPACE = uuid.UUID("e7f0c4a3-9b2e-5d18-8a3c-1f9c4e2b7a3d")


def compute_preset_id(name: str) -> uuid.UUID:
    return uuid.uuid5(_PRESET_NAMESPACE, name)
