import json
from ai.client import LLMClient
from ai.lang_utils import build_lang_instruction
from fill_mode.parser import (
    extract_first_pages,
    extract_text_from_pdf,
    detect_toc,
    detect_toc_docx,
    extract_first_paras_docx,
    extract_text_from_docx,
)
from store.schema import KnowledgeNode

# 有目录：精细提取，50-80 节点
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
7. {lang_instruction}

输出 JSON schema（只输出 JSON，不要解释）：
[{{"id": "n1", "title": "...", "parent_id": null, "level": 1}}]"""

# 无目录：略读全文，20-30 节点，抓主线
FRAMEWORK_LIGHT_PROMPT = """你是一个专业的学术文献阅读助手。
以下是《{course_name}》的全文内容（可能是论文、笔记或文献）：

<material>
{material_text}
</material>

这份材料没有目录，请对全文进行略读，提取主要论点和知识结构，严格遵守以下规则：
1. 输出 JSON 格式的节点数组，schema 见下方
2. 层级最多 3 层（level 1-3），不要过度细分
3. 每个节点 title 不超过 12 个字，使用名词短语或短动宾结构
4. 聚焦主要论点、核心概念、关键论据，忽略举例和细节
5. 节点总数控制在 20-35 个
6. {lang_instruction}

输出 JSON schema（只输出 JSON，不要解释）：
[{{"id": "n1", "title": "...", "parent_id": null, "level": 1}}]"""


def _parse_nodes(raw: str) -> list[KnowledgeNode]:
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    nodes_data = json.loads(raw)
    return [
        KnowledgeNode(**{k: v for k, v in n.items() if k in KnowledgeNode.__dataclass_fields__})
        for n in nodes_data
    ]


def generate_framework(
    course_name: str,
    pdf_path: str = None,
    docx_path: str = None,
    material_text: str = None,
    client: LLMClient = None,
    lang_mode: str = "original",
    lang_from: str = "auto",
    lang_to: str = "zh",
) -> list[KnowledgeNode]:
    if client is None:
        client = LLMClient()

    lang_instruction = build_lang_instruction(lang_mode, lang_from, lang_to)

    if material_text is not None:
        prompt = FRAMEWORK_PROMPT.format(
            course_name=course_name,
            material_text=material_text[:15000],
            lang_instruction=lang_instruction,
        )
        return _parse_nodes(client.chat(prompt))

    if pdf_path:
        has_toc = detect_toc(pdf_path)
        if has_toc:
            text = extract_first_pages(pdf_path, n=25)
            prompt = FRAMEWORK_PROMPT.format(course_name=course_name, material_text=text[:15000], lang_instruction=lang_instruction)
        else:
            text = extract_text_from_pdf(pdf_path)
            prompt = FRAMEWORK_LIGHT_PROMPT.format(course_name=course_name, material_text=text[:20000], lang_instruction=lang_instruction)

    elif docx_path:
        has_toc = detect_toc_docx(docx_path)
        if has_toc:
            text = extract_first_paras_docx(docx_path, n=200)
            prompt = FRAMEWORK_PROMPT.format(course_name=course_name, material_text=text[:15000], lang_instruction=lang_instruction)
        else:
            text = extract_text_from_docx(docx_path)
            prompt = FRAMEWORK_LIGHT_PROMPT.format(course_name=course_name, material_text=text[:20000], lang_instruction=lang_instruction)

    else:
        raise ValueError("pdf_path, docx_path, or material_text required")

    return _parse_nodes(client.chat(prompt))
