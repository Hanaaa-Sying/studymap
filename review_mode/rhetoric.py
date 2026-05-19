import json
from ai.client import LLMClient
from fill_mode.parser import chunk_text

RHETORIC_PROMPT = """你是一个社会科学论述题答题专家。
以下是课程《{course_name}》的材料片段：

<material>
{material_text}
</material>

请提取可在论述题中直接使用的高频话术和学术表达。

要求：
1. 每条话术是完整表达（1-3 句话），可直接嵌入答题
2. 附上适用场景（如"批判某理论时"）
3. 标注来源（页码/章节，如无则填"教材"）
4. 优先提取：理论批判套路、概念界定句式、学者观点引用格式

只输出 JSON 数组，没有话术则输出 []：
[{{"text": "...", "context": "...", "source": "..."}}]"""


def extract_rhetoric(course_name: str, material_text: str, client: LLMClient = None) -> list[dict]:
    if client is None:
        client = LLMClient()
    prompt = RHETORIC_PROMPT.format(course_name=course_name, material_text=material_text[:6000])
    raw = client.chat(prompt)
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)


def extract_rhetoric_chunked(course_name: str, text: str, client: LLMClient = None) -> list[dict]:
    if client is None:
        client = LLMClient()
    chunks = chunk_text(text, chunk_size=6000, overlap=500)
    all_rhetoric = []
    seen = set()
    for chunk in chunks:
        try:
            items = extract_rhetoric(course_name, chunk, client)
            for item in items:
                key = item.get("text", "")[:30]
                if key and key not in seen:
                    seen.add(key)
                    all_rhetoric.append(item)
        except Exception:
            continue
    return all_rhetoric
