PROVIDER_OPENAI = "openai"
PROVIDER_PERSONAPLEX = "personaplex"

SESSION_BY_USER_SQL = """SELECT id, user_id, persona_id, started_at, ended_at, duration_seconds
FROM conversation_sessions
WHERE id = $1 AND user_id = $2"""

INSERT_EVENT_SQL = """INSERT INTO events (user_id, event_type, ts, props)
VALUES ($1, $2, $3, $4)"""
