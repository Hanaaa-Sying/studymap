from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class KnowledgeNode:
    id: str
    title: str
    summary: str = ""
    content: str = ""
    checked: bool = False
    parent_id: Optional[str] = None
    level: int = 1
    rhetoric_ids: List[str] = field(default_factory=list)


@dataclass
class RhetoricEntry:
    id: str
    text: str
    context: str = ""
    source: str = ""
    courses: List[str] = field(default_factory=list)
