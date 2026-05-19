import json
from ai.client import LLMClient

RHETORIC_PROMPT = """你是一个社会科学论述题答题专家。
以下是课程《{course_name}》的材料：

<material>
{material_text}
</material>

请提取可在论述题中直接使用的高频话术和学术表达。

要求：
1. 每条话术是完整表达（1-3 句话），可直接嵌入答题
2. 附上适用场景（如"批判某理论时"）
3. 标注来源（页码/章节）
4. 优先提取：理论批判套路、概念界定句式、学者观点引用格式

只输出 JSON 数组：
[{{"text": "...", "context": "...", "source": "..."}}]"""


def extract_rhetoric(course_name: str, material_text: str, client: LLMClient = None) -> list[dict]:
    if client is None:
        client = LLMClient()
    prompt = RHETORIC_PROMPT.format(course_name=course_name, material_text=material_text[:12000])
    raw = client.chat(prompt)
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)
