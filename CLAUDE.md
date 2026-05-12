# Palkie Talkie: Backend

Server-side. Shared product, features, and backend-stack decisions (Clerk, Neon, Pinecone, AuraDB, Stripe, IAP, entitlement) live in `../CLAUDE.md`.

## Stack

- Language: Python.
- Inference: PersonaPlex on Lambda Labs A100. WebSocket protocol to iOS app.
- API: FastAPI.
- Workers: same FastAPI deployment, async tasks for post-session NLP pipelines.
- NLP: spaCy for tokenization + lemmatization. LLM (Claude / GPT) for mistake detection, native-phrase extraction, phrase alternatives, KG entity extraction.

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
