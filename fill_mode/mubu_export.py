from store.schema import KnowledgeNode
from typing import List


def to_mubu_markdown(nodes: List[KnowledgeNode]) -> str:
    id_map = {n.id: n for n in nodes}
    lines = []

    def render(node: KnowledgeNode):
        indent = "  " * (node.level - 1)
        lines.append(f"{indent}- {node.title}")
        for child in [n for n in nodes if n.parent_id == node.id]:
            render(child)

    for root in [n for n in nodes if n.parent_id is None]:
        render(root)

    return "\n".join(lines)
