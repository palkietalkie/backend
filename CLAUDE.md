# Palkie Talkie — Backend

Terminology: see /JARGON.md at the repo root.

Server-side. Shared product, business model, cost simulation, GTM, team/fundraising live in `../CLAUDE.md`. iOS client concerns (Swift, AVAudioEngine, audio session) live in `../ios/CLAUDE.md`. This file covers backend Python, FastAPI surface, NLP pipelines, inference plane, and deploy.

## Stack

- Language: Python 3.14. Dependency manager: `uv`. `uv pip install -e ".[dev]"` for dev.
- DB driver: `asyncpg`. Raw SQL only — no ORM, no SQLAlchemy expression DSL. SQL is inline at the call site as Python triple-quoted strings (positional `$N` parameters required by asyncpg).
- Migrations: flat `.sql` files in `migrations/`, applied in lexical order by `migrations/run.py` (tracked in a `schema_version` table). No Alembic. Container CMD runs `python -m migrations.run` then `uvicorn app.main:app --workers 1`.
- API: FastAPI on Fly.io. Two apps: `palkietalkie-api` (prd) + `palkietalkie-api-dev` (dev). Region `sjc`. `shared-cpu-1x:1024MB` (512MB OOM'd with spaCy + SDKs; 1024MB with 1 uvicorn worker fits).
- Inference plane: pluggable via `INFERENCE_PROVIDER` env var on the Fly backend.
  - `openai` (current default) — calls OpenAI Realtime via `app/services/openai_realtime.py:mint_openai_session`. Returns an ephemeral `client_secret.value` (string like `ek_…`) + `wss://api.openai.com/v1/realtime?model=gpt-realtime-mini`. JSON event protocol. Requires `OPENAI_API_KEY`. Server-side VAD with `interrupt_response: true` configured at session-mint time.
  - `personaplex` (alternative) — returns the canonical NVIDIA PersonaPlex WS URL with an HMAC ticket. Binary Ogg-Opus protocol. Two Modal environments (`main` prd + `dev`): `palkietalkie--api.modal.run` and `palkietalkie-dev--api.modal.run`. Migration target for "scale" is Lambda Labs A100 always-on (see root `../CLAUDE.md` § Cost simulation for economics).
  - Voice catalogs are per-provider and do NOT translate — `app/personas/voices.py:voices_for_provider(provider)` returns the active catalog. Each preset carries `voice_id_personaplex` + `voice_id_openai` separately. `mint_openai_session` rejects voice IDs not in `SUPPORTED_OPENAI_VOICES` to fail fast on misconfig.
- Modal cold-start optimizations for the PersonaPlex path (target: 5-8s, hidden by iOS `LoadingTipsView`):
  - NVMe Modal Volume mount for weights: ~3-5s load (vs ~30-60s from cloud object storage).
  - Container image baked with PyTorch + Mimi + Helium code + dependencies: 2-3s container boot.
  - Weights stay BF16 (14GB, full quality). Quantization considered but rejected: INT4 drops MMLU 9.9 points on full Moshi (paper Table 11). Saves only ~1.5s load. Not worth the quality cost.
  - Idle TTL: Modal default 5 min.
  - Real cold-start times recorded to `events` table via iOS `SessionController.scheduleColdStartReport` → `POST /events`. Percentile analysis via raw SQL.
- Auth: Clerk JWT verified via cached JWKS (`app/auth/verify_clerk_jwt.py`). `resolve_current_user` FastAPI dependency lazily creates the `users` row on first request. For PersonaPlex's Modal WS, we mint an HMAC ticket (`app/services/ws_ticket.py`) signed with `WS_TICKET_SECRET` — no Clerk hop on Modal. For OpenAI's WS, the ephemeral `ek_…` token from `/v1/realtime/client_secrets` is the auth.
- NLP: spaCy (`en_core_web_sm`) for tokenization + lemmatization (pinned to a version with cp314 wheels; spaCy stable doesn't ship cp314 yet so we float on `>=3.7.6`). Gemma 4 31b on Google AI Studio (free, `gemma-4-31b-it`) for mistake detection, native-phrase extraction, phrase alternatives, KG entity extraction.
- CEFR reference: in-memory CSV loaded once at module import (`app/services/cefr_vocab.py` reads `app/scripts/data/cefr_vocab.csv`, ~98k entries derived from the `wordfreq` library's Zipf-frequency English wordlist). Regenerated rarely via `app/scripts/regenerate_cefr_vocab.py` (PEP 723 inline metadata — `uv run` installs wordfreq into a one-shot venv).
- Native phrase corpus: LLM-generated phrase lists seeded by CEFR level (1-2k phrases). License Cambridge / SkELL if quality matters at scale.
- Vector embeddings: Pinecone Inference (`llama-text-embed-v2`, 1024 dim, cosine, AWS us-east-1). Indexes `palkietalkie` (prd) and `palkietalkie-dev` (dev). No separate embedding API call — Pinecone embeds + stores in one call.
- Push: APNs HTTP/2 via `aioapns`. Scheduled-session reminders, follow-ups, calendar-driven prompts. Migrated from `apns2` (pyjwt conflict with `app-store-server-library`).
- Analytics: `events(user_id, event_type, ts, props jsonb)` in Neon. iOS posts client-side events to `POST /events`. View via Metabase / raw SQL. No external vendor.
- Apple App Store Server Notifications: signature verified with `app-store-server-library` (proper x5c cert-chain validation against Apple's root CAs).

## Module conventions

Conventions, not a file tree (filesystem is the source of truth). What lives where and the invariants:

- `app/routers/` — HTTP endpoints, one file per feature; file name matches the URL prefix. Resource-bundle grouping (list / create / update / delete for one resource) stays together; otherwise prefer splitting.
- `app/services/` — non-HTTP work. One purpose per file; verb-prefixed file name matches the function (`verb_noun.py` → `def verb_noun(...)`). Each external integration lives in its own subdirectory: `openai/`, `gemma/`, `personaplex/`, `weather/`, `google_calendar/`, `calendar/` (cross-provider abstraction), `stripe_webhooks/`, `apple_asn/`, `apple_push/`, `cefr_vocab/`, `neon/` (Postgres — pool + types + queries), `neo4j/` (AuraDB — driver + KG models + queries).
- `app/pipelines/` — post-session NLP. Each split into a pure `extract(...)` + async `persist(...)` pair so the LLM-touching half stays unit-testable.
- `app/auth/` — JWKS-cached Clerk JWT verify + FastAPI `resolve_current_user` dependency that JIT-creates the `users` row on first request.
- Neon-specific: `app/services/neon/` holds the asyncpg pool, `DBConn` type alias (`Connection | PoolConnectionProxy`), TypedDicts mirroring schema (`rows.py`), pool lifecycle (`get_pool`, `get_db`, `reset_pool`, `init_connection`, `normalize_url`), and query helpers (`find_user_by_clerk_id`, `apply_subscription_state`). NO ORM, NO Alembic. SQL is inline at the call site as triple-quoted Python strings.
- `app/personas/` — code-defined preset personas + voice library + character-to-prompt assembler. Presets NEVER live in the DB; user-customs go in the `personas` table.
- `app/scripts/` — one-shot scripts (currently just `regenerate_cefr_vocab.py`, PEP 723 inline-deps). No seed scripts; reference data is in-memory CSV or code constants.
- `inference/` — speech-to-speech inference plane. Today targets Modal (`voice_server.py` is `modal.App("voice")` on A100 with NVMe-backed Volume). `moshi/` is the vendored NVIDIA PersonaPlex Moshi fork (only the inner Python package; our diffs are normal git, see `inference/moshi/SOURCE.md`). Auth uses HMAC tickets — no Clerk in the WS path.
- `migrations/` — flat numbered `.sql` files, applied in lexical order by `run.py` (tracked in `schema_version` table). No Alembic.
- `tests/` (alongside source: `app/**/test_*.py`) — pytest + pytest-asyncio + httpx + testcontainers (real Postgres via Docker for integration tests). Unit tests don't need Docker.

## Deploys

- Backend prd → Fly `palkietalkie-api`. Auto-deploys on push to `main` via `.github/workflows/deploy-api.yml` (`FLY_API_TOKEN` GH secret).
- Backend dev → Fly `palkietalkie-api-dev`. Manual deploy (`flyctl deploy -a palkietalkie-api-dev` or via `boot.sh`).
- Inference `voice` (both Modal envs) → manual `modal deploy inference/voice_server.py` or via `.github/workflows/deploy-inference.yml` (`MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` GH secrets, triggers on changes under `inference/`).
- CI: `.github/workflows/pytest.yml` runs ruff + mypy + pytest with coverage on every PR + push to main.

## Setup (once per clone)

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
modal token new   # if not already authenticated
# Run locally:
uvicorn app.main:app --reload --port 8000
# Run tests (unit tests work without Docker; testcontainers tests need a running Docker daemon):
pytest --cov=app
```

`.env.example` documents required env vars: Clerk dev keys, Neon dev DB URL, Neo4j AuraDB URI / user / password, Pinecone API key + index host, Modal token id / secret, HF_TOKEN (PersonaPlex gated repo), Gemma + NewsAPI keys, Google OAuth client id / secret (dev redirect URI `http://localhost:5000/api/integrations/google-calendar/callback`), Stripe sandbox keys + price IDs (`STRIPE_PRICE_INDIVIDUAL_MONTHLY` / `_ANNUAL`, `STRIPE_PRICE_FAMILY_MONTHLY` / `_ANNUAL`), `OPENAI_API_KEY`, `INFERENCE_PROVIDER` (defaults to `openai`).

## LGTM Workflow

CRITICAL: NEVER start without explicit user request. PR must be clean, don't ignore failures.

1. `git fetch origin main && git merge origin/main`
2. `git commit -m "<one-liner subject>"`, user has already run `git add` before saying "lgtm"
   - Pre-commit hook runs `ruff format --check`, `ruff check`, `mypy app/`. Pytest runs in CI, not pre-commit (too slow + needs Docker).
   - One-liner subject only. No body paragraphs. PR body carries long-form context.
   - NO co-author lines, NO `[skip ci]`
   - If hook fails: fix, re-stage, commit again. Don't stage other sessions' files.
3. Check for existing PR: `gh pr list --head $(git branch --show-current) --state open`, if exists, STOP and ask
4. `git push`
5. `gh pr create --title "<technical, descriptive title>" --body "" --assignee @me`, title is enough; no body until product launches.
