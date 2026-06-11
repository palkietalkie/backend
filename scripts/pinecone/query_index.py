"""Semantic top-k search of one index within a namespace. Entry point for scripts/pinecone/query.sh; argv is <index> <namespace> <text>, PINECONE_API_KEY from env."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.pinecone.get_pinecone_client import get_pinecone_client  # noqa: E402


def main() -> None:
    if len(sys.argv) < 4:
        print("usage: query_index.py <index> <namespace> <text>", file=sys.stderr)
        sys.exit(1)
    index_name, namespace, text = sys.argv[1], sys.argv[2], sys.argv[3]

    res = (
        get_pinecone_client()
        .Index(index_name)
        .search(
            namespace=namespace,
            query={"inputs": {"text": text}, "top_k": 5},
        )
    )
    hits = res.result.hits
    if not hits:
        print("(no matches)")
        return
    for hit in hits:
        snippet = str(hit.fields.get("text", "")) if hit.fields else ""
        print(f"{hit.score:.4f}  {hit.id}  {snippet[:80]}")


if __name__ == "__main__":
    main()
