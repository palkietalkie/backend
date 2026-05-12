# Palkie Talkie: Backend

Server-side. Shared product, features, and backend-stack decisions (Clerk, Neon, Pinecone, AuraDB, Stripe, IAP, entitlement) live in `../CLAUDE.md`.

## Stack

- Language: Python.
- Inference: PersonaPlex on Lambda Labs A100 (~$1.10/hr), region `us-west-1` (San Francisco — closest to Bay Area ICP). WebSocket protocol to the iOS app. Single US-region instance for MVP. Multi-region (e.g., a Japan-region A100) is a post-launch task once the user base spreads outside the US.
- API + workers: FastAPI on Fly.io, region `sjc` (San Jose — co-located with Lambda Labs us-west-1 to minimize backend → inference RTT). Always-on small instance ($5/mo entry tier) handles Stripe / ASN webhooks, entitlement endpoint, conversation-start endpoint, and FastAPI BackgroundTasks for NLP pipelines. Move heavy batch jobs to Modal later if load grows.
- NLP: spaCy for tokenization + lemmatization. LLM (Claude / GPT) for mistake detection, native-phrase extraction, phrase alternatives, KG entity extraction.
- Transcripts: PersonaPlex exposes Inner Monologue text tokens (decoded with SentencePiece) as a "Model response" transcript alongside the audio stream. No separate Whisper pass needed. Reassembly logic required: text tokens occasionally split across frames (e.g., "fl uff" → "fluff").
- Mistake detection scope: article errors, preposition errors, verb tense, word choice, naturalness. Pronunciation deferred (PersonaPlex doesn't grade pronunciation directly; needs separate pipeline).
- CEFR vocab reference: start with an open list (CEFR-J, Lextutor, EFLLEX). If quality matters at scale, license Cambridge English Vocabulary Profile.
- Native phrase corpus: start with LLM-generated phrase lists seeded by CEFR levels (1-2k phrases). If quality matters at scale, license a phrase corpus (Cambridge, SkELL).
- Audio over WebSocket: iOS encodes mic audio as Opus (~24 kbps); backend / PersonaPlex server decodes Opus → PCM before feeding Mimi. ~16× less bandwidth than raw PCM, transparent voice quality.
- Quizzes + news: daily backend job pulls 10 latest news stories from a news API and generates 10 fresh quizzes via the Google Gemma API. Cached for the day per user (or globally if not user-specific). Surfaced on Feature 4 "What to talk about today" screen.
- KG population: read-only viewer for users. Backend extracts entities + relations from conversation transcripts via LLM after each session; writes to AuraDB. User cannot edit directly — KG reflects what they've told the AI naturally.
- Voice library: 17 stock PersonaPlex voices ship with the model. Beyond that, we curate our own — collect voice samples (comedians, actors, character types), encode each via Mimi → `.pt` tensor, store the bundle in object storage and ship with the Lambda PersonaPlex instance. Users pick from the combined library; they never upload.
- Push notifications: APNs HTTP/2 API (Python `apns2` or `pyapns2` library). Backend sends scheduled-session reminders, follow-ups, calendar-driven prompts (Feature 6).
- Analytics: write session and user events directly to Neon as `events(user_id, event_type, ts, props jsonb)`. View with Metabase or custom dashboards. No external analytics vendor — keeps PII in our DB.
- Auth propagation: backend issues / passes through Clerk JWTs. PersonaPlex server on Lambda validates the same JWT against Clerk's JWKS endpoint on every WebSocket connection. Same auth the user signed in with, propagated to the GPU server so only paying users can open audio streams.

## Components

- `personaplex/` — Lambda Labs deployment scripts + config. SSH-managed.
- `api/` — FastAPI app:
  - Stripe webhook handler (subscription state → Neon)
  - App Store Server Notifications handler (IAP state → Neon)
  - Entitlement endpoint (`/users/{id}/entitlement` → `is_premium`)
  - Session-end trigger (called by iOS app, queues post-session jobs)
  - Conversation-start endpoint (builds the text prompt: persona + situational context + KG + profile → returns to iOS)
- `pipelines/` — post-session jobs:
  - Tokenize + lemmatize transcripts → `word_freq`
  - n-gram + LLM phrase extraction → `phrase_freq`
  - LLM mistake detection → `mistakes`
  - LLM alternative-phrase generation → cached in Postgres
  - KG entity + relation extraction → AuraDB
  - CEFR coverage recompute → cached aggregate per user
- `migrations/` — Neon Postgres schema migrations.

## Setup (TODO once Lambda instance is up)

- `./scripts/setup.sh` — environment provisioning
- `.env.example` — required environment variables (Lambda IP, HF token, Stripe keys, Clerk keys, AuraDB connection, Pinecone API key, OpenAI/Anthropic key)
