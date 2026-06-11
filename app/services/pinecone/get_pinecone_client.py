"""Construct and cache the shared Pinecone client — used by the app's memory index AND the scripts/pinecone/* tools (anything needing a Pinecone handle, not just scripts).

A lazy function, not a module-level constant, on merit: a const evaluates at import time, so importing this module (or anything that transitively imports it — including a test that only wants to import a sibling) would read settings and open the client as a side effect, and would fail at import if the API key isn't present yet (a confusing error far from the use site). A function defers construction to first actual use, fails at the call site where the error is actionable, and stays mockable in tests. The cached holder still gives a single reused client — the singleton benefit without the import-time cost.
"""

from dataclasses import dataclass

from pinecone import Pinecone

from app.config import get_settings


@dataclass
class _ClientState:
    client: Pinecone | None = None


_state = _ClientState()


def get_pinecone_client() -> Pinecone:
    if _state.client is None:
        _state.client = Pinecone(api_key=get_settings().pinecone_api_key)
    return _state.client
