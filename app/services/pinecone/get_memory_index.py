from dataclasses import dataclass

from pinecone import Index

from app.config import get_settings
from app.services.pinecone.get_pinecone_client import get_pinecone_client

# Pinecone integrated-inference embedding model. The index is created bound to this model, so we upsert/search raw TEXT and Pinecone embeds server-side — no separate embed call. 1024-dim, cosine (model defaults).
EMBED_MODEL = "llama-text-embed-v2"


@dataclass
class _State:
    ensured: bool = False


_state = _State()


def get_memory_index() -> Index:
    """Return the conversation-memory index handle, creating it (bound to the embedding model) on first use. Index name is per-env via `pinecone_index` (palkietalkie / palkietalkie-dev)."""
    pc = get_pinecone_client()
    name = get_settings().pinecone_index
    if not _state.ensured:
        if not pc.has_index(name):
            pc.create_index_for_model(
                name=name,
                cloud="aws",
                region="us-east-1",
                embed={"model": EMBED_MODEL, "field_map": {"text": "text"}},
            )
        _state.ensured = True
    index = pc.Index(name)
    # The non-gRPC Pinecone client always returns a REST Index; this narrows the SDK's over-broad Index | GrpcIndex signature and fails fast if that ever stops holding.
    assert isinstance(index, Index)
    return index
