"""Application settings loaded from environment via Pydantic."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration, loaded from environment.

    Defaults are safe placeholders for local dev / tests. Production deploys override via Fly secrets.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # --- Neon (Postgres) ---
    neon_database_url: str = Field(
        default="postgresql+asyncpg://palkie:palkie@localhost:5432/palkietalkie"
    )

    # --- Neo4j AuraDB ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j"  # noqa: S105 — default Neo4j local dev password

    # --- Pinecone ---
    pinecone_api_key: str = ""
    pinecone_index: str = "palkietalkie"

    # --- Clerk ---
    clerk_jwks_url: str = "https://example.clerk.accounts.dev/.well-known/jwks.json"
    clerk_issuer: str = "https://example.clerk.accounts.dev"

    # --- Stripe ---
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # --- Apple ---
    # Bundle id + key ids are non-secret constants (app/apple_identifiers.py), imported directly by consumers — not Settings fields. Only env-loaded secrets belong here.
    apple_verify_receipt_shared_secret: str = ""

    # --- LLMs ---
    # Google AI Studio API key. Same key works for both Gemini and Gemma endpoints — we use it for the `gemma-2-9b-it:generateContent` endpoint everywhere (daily quizzes, mistake detection, phrase extraction, KG extraction).  # noqa: E501
    gemini_api_key: str = ""
    openai_api_key: str = ""

    # --- Inference provider switch ---
    # Selects which speech-to-speech backend `/conversation/start` mints a session for. Dev-only switch, no UI. "openai" calls OpenAI's Realtime API (`gpt-realtime-mini`, $10/M audio input + $20/M audio output, JSON event protocol). Picked over `gpt-realtime-2` ($32/$64) which is unshippable at $17.99/mo Individual. `gpt-realtime` base and `gpt-realtime-2` are also valid model strings if a pricing/quality tradeoff later shifts. "personaplex" routes to NVIDIA PersonaPlex on Modal (binary Ogg-Opus protocol). Defaulting to openai because PersonaPlex on Modal still has cold-start + cost variance we're A/B-testing against.
    inference_provider: str = "openai"

    # --- News ---
    news_api_key: str = ""

    # --- APNs ---
    apns_key_id: str = ""
    apns_team_id: str = ""
    apns_auth_key_path: str = ""
    apns_use_sandbox: bool = True

    # --- PersonaPlex (Lambda Labs) ---
    personaplex_host: str = "127.0.0.1"
    personaplex_port: int = 8080
    # Set to "ws" for local dev (no TLS), "wss" in production. Lambda Labs runs PersonaPlex behind a TLS-terminating proxy in production.  # noqa: E501
    personaplex_scheme: str = "wss"

    # --- Google OAuth (Calendar) ---
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/integrations/google-calendar/callback"

    # --- Slack ---
    # Bot User OAuth token (xoxb-…) for the PT Slack workspace. Same auth used by scripts/slack.sh so we don't run two separate Slack integrations. Optional — if unset, outbound chat.postMessage skips silently.
    slack_bot_token: str = ""
    # Channel ID for the #gtm channel. Every iOS event, Apple ASN webhook event, and Stripe webhook event pings here so we can watch user activity in real time. Channel IDs are public identifiers and could live in fly.toml [env] too — keeping here so settings can read them with the same env lookup pattern.
    slack_channel_gtm: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def personaplex_ws_base(self) -> str:
        """Base WebSocket URL (scheme + host + port) for PersonaPlex. The full URL is built in ``app.services.personaplex.build_handshake`` because it includes per-conversation query params (text prompt, voice id, JWT, decoding hyperparameters)."""
        # Default ports (80 / 443) are conventionally omitted from URLs
        if (self.personaplex_scheme == "wss" and self.personaplex_port == 443) or (
            self.personaplex_scheme == "ws" and self.personaplex_port == 80
        ):
            return f"{self.personaplex_scheme}://{self.personaplex_host}"
        return f"{self.personaplex_scheme}://{self.personaplex_host}:{self.personaplex_port}"

    @property
    def personaplex_ws_url(self) -> str:
        """Backwards-compat alias used by smoke tests. Returns the base URL, not the full per-conversation URL (see ``personaplex_ws_base``)."""
        return self.personaplex_ws_base


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
