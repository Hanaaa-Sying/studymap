_LANG_NAMES = {
    "zh": "中文（简体）",
    "zh-tw": "中文（繁體）",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch",
}


def build_lang_instruction(lang_mode: str, lang_from: str = "auto", lang_to: str = "zh") -> str:
    if lang_mode == "translate":
        target = _LANG_NAMES.get(lang_to, lang_to)
        src_part = "" if lang_from == "auto" else f"从{_LANG_NAMES.get(lang_from, lang_from)}"
        return f"将输出内容{src_part}翻译为{target}，专有名词、学者名、理论名保留原文并括注。"
    if lang_mode == "bilingual":
        return '将输出内容改为"中文 · English"双语并列，专有名词保持原文。'
    return "输出语言与原材料保持一致。"
