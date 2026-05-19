import json
from ai.client import LLMClient
from fill_mode.parser import extract_first_pages
from store.schema import KnowledgeNode

FRAMEWORK_PROMPT = """你是一个专业的学术课程知识结构分析师。
以下是课程《{course_name}》的目录和章节概览：

<material>
{material_text}
</material>

请提取该课程的知识框架，严格遵守以下规则：
1. 输出 JSON 格式的节点数组，schema 见下方
2. 层级最多 4 层（level 1-4）
3. 每个节点 title 不超过 10 个字，使用名词短语
4. 只保留考试相关内容：理论名称、学者姓名、核心命题、重要对比
5. 删除：章节编号、"引言"/"结论"/"举例"等非考点内容
6. 节点总数控制在 50-80 个

输出 JSON schema（只输出 JSON，不要解释）：
[{{"id": "n1", "title": "...", "parent_id": null, "level": 1}}]"""


def generate_framework(course_name: str, pdf_path: str = None, material_text: str = None,
                       client: LLMClient = None) -> list[KnowledgeNode]:
    if client is None:
        client = LLMClient()
    if material_text is None:
        if pdf_path is None:
            raise ValueError("pdf_path or material_text required")
        material_text = extract_first_pages(pdf_path, n=25)
    prompt = FRAMEWORK_PROMPT.format(course_name=course_name, material_text=material_text[:15000])
    raw = client.chat(prompt)
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    nodes_data = json.loads(raw)
    return [KnowledgeNode(**{k: v for k, v in n.items() if k in KnowledgeNode.__dataclass_fields__})
            for n in nodes_data]
