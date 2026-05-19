from store.schema import KnowledgeNode
from typing import List


def to_mubu_markdown(nodes: List[KnowledgeNode]) -> str:
    lines = []

    def render(node: KnowledgeNode, prefix: str):
        indent = "  " * (node.level - 1)
        lines.append(f"{indent}- {prefix} {node.title}")
        children = [n for n in nodes if n.parent_id == node.id]
        for i, child in enumerate(children, 1):
            if child.level <= 3:
                child_prefix = f"{prefix}.{i}"
            else:
                child_prefix = f"{i}）"
            render(child, child_prefix)

    roots = [n for n in nodes if n.parent_id is None]
    for i, root in enumerate(roots, 1):
        render(root, str(i))

    return "\n".join(lines)
