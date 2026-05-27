VERSION = "v1"
# 24h TTL. Each /conversation/start mints a fresh ticket, so in normal use this is invisible. The expiry exists only to limit damage if a URL leaks (debug logs, screenshot, MITM); 24h is short enough that secret rotation handles longer-term risk, long enough that no real user ever hits the cliff.
DEFAULT_TTL_SECONDS = 60 * 60 * 24
