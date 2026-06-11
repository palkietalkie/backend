"""Print one index's stats (total vectors + per-namespace counts). Entry point for scripts/pinecone/describe.sh; argv[1] is the index name, PINECONE_API_KEY from env."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.pinecone.get_pinecone_client import get_pinecone_client  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: describe_index.py <index>", file=sys.stderr)
        sys.exit(1)
    name = sys.argv[1]

    stats = get_pinecone_client().Index(name).describe_index_stats()
    print(f"index: {name}")
    print(f"total vectors: {stats.total_vector_count}")
    namespaces = stats.namespaces
    if not namespaces:
        print("namespaces: (none — index is empty)")
        return
    print("namespaces:")
    for ns, info in namespaces.items():
        print(f"  {ns or '(default)'}: {info.vector_count} vectors")


if __name__ == "__main__":
    main()
