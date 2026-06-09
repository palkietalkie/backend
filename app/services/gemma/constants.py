DEFAULT_MODEL = "gemma-4-31b-it"
ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
# Long enough for unconstrained generation (no maxOutputTokens). Gemma 4 thinks before answering and can take 60-180s for multi-item JSON. Callers are async background pipelines (daily content scheduler, post-session NLP) where latency is fine.
GEMMA_TIMEOUT_SECONDS = 300.0
