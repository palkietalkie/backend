"""List all Pinecone indexes on the account. Entry point for scripts/pinecone/indexes.sh (reads PINECONE_API_KEY from env)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.pinecone.get_pinecone_client import get_pinecone_client  # noqa: E402


def main() -> None:
    for idx in get_pinecone_client().list_indexes():
        print(f"{idx.name:<22} dim={idx.dimension} metric={idx.metric}")


if __name__ == "__main__":
    main()
