from aioapns import APNs

from app.config import get_settings

# Each ``APNs(...)`` opens a persistent HTTP/2 connection; reuse it across pushes for the process lifetime.
_client: APNs | None = None


def get_client() -> APNs:
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    _client = APNs(
        key=settings.apns_auth_key_path,
        key_id=settings.apns_key_id,
        team_id=settings.apns_team_id,
        topic=settings.apple_bundle_id,
        use_sandbox=settings.apns_use_sandbox,
    )
    return _client
