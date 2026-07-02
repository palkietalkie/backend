from typing import Literal

# Source of truth for the inference-provider wire value. The constants are typed against it, so a typo in either is a type error, and StartResponse.provider reuses Provider to surface it as an enum in /openapi.json + the generated iOS type.
Provider = Literal["openai", "personaplex", "openai_webrtc"]
PROVIDER_OPENAI: Provider = "openai"
PROVIDER_PERSONAPLEX: Provider = "personaplex"
# Same OpenAI Realtime model + ephemeral token as "openai", but iOS connects over WebRTC (Opus/SRTP/UDP) instead of the base64-PCM16 WebSocket. ws_url carries the /v1/realtime/calls URL for the SDP handshake rather than the wss:// URL.
PROVIDER_OPENAI_WEBRTC: Provider = "openai_webrtc"

# How many real current headlines a Talk-view conversation gets: three — enough that one might be relevant as a timely opener, few enough not to bloat the prompt or tempt the tutor into reciting a news list.
NEWS_HEADLINES_IN_PROMPT = 3

SESSION_BY_USER_SQL = """SELECT id, user_id, persona_id, started_at, ended_at, duration_seconds
FROM conversation_sessions
WHERE id = $1 AND user_id = $2"""

INSERT_EVENT_SQL = """INSERT INTO events (user_id, event_type, ts, props)
VALUES ($1, $2, $3, $4)"""
