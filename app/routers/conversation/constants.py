from typing import Literal

# Source of truth for the inference-provider wire value. The constants are typed against it, so a typo in either is a type error, and StartResponse.provider reuses Provider to surface it as an enum in /openapi.json + the generated iOS type.
Provider = Literal["openai", "personaplex"]
PROVIDER_OPENAI: Provider = "openai"
PROVIDER_PERSONAPLEX: Provider = "personaplex"

SESSION_BY_USER_SQL = """SELECT id, user_id, persona_id, started_at, ended_at, duration_seconds
FROM conversation_sessions
WHERE id = $1 AND user_id = $2"""

INSERT_EVENT_SQL = """INSERT INTO events (user_id, event_type, ts, props)
VALUES ($1, $2, $3, $4)"""
