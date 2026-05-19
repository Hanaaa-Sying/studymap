import json
from ai.client import LLMClient
from store.schema import KnowledgeNode, RhetoricEntry
from typing import List


REVIEW_PROMPT = """你是一个考试答题助手。
学生面对的论述题是："{question}"

以下是课程知识框架节点（JSON）：
{framework_json}

以下是话术库（JSON）：
{rhetoric_json}

请：
1. 从框架中识别与该题目最相关的节点（3-6 个）
2. 从话术库中推荐最适合答题的条目（2-4 条）
3. 给出一个 3 步答题思路（每步一句话）

输出 JSON（只输出 JSON）：
{{"relevant_nodes": [{{"id": "...", "title": "..."}}],
  "recommended_rhetoric": [{{"text": "...", "context": "..."}}],
  "answer_outline": ["第一步...", "第二步...", "第三步..."]}}"""


def review_question(question: str, nodes: List[KnowledgeNode],
                    rhetoric: List[RhetoricEntry], client: LLMClient = None) -> dict:
    if client is None:
        client = LLMClient()
    fw_json = json.dumps([{"id": n.id, "title": n.title} for n in nodes], ensure_ascii=False)
    rh_json = json.dumps([{"text": r.text, "context": r.context} for r in rhetoric], ensure_ascii=False)
    prompt = REVIEW_PROMPT.format(question=question, framework_json=fw_json, rhetoric_json=rh_json)
    raw = client.chat(prompt)
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)
