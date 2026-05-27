from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KGEntity:
    # person | place | project | interest | event
    type: str
    name: str
    props: dict[str, Any]


@dataclass(frozen=True)
class KGRelation:
    src_name: str
    # FRIENDS_WITH | WORKS_AT | LIVES_IN | INTERESTED_IN | RELATED_TO ...
    relation: str
    dst_name: str
