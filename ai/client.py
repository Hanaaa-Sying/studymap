import os

PROVIDERS = ("deepseek", "doubao", "claude")


class LLMClient:
    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv("STUDYMAP_LLM_PROVIDER", "deepseek")
        if self.provider not in PROVIDERS:
            raise ValueError(f"Unknown provider: {self.provider}. Choose from {PROVIDERS}")
        self._client = self._build_client()

    def _build_client(self):
        if self.provider == "deepseek":
            from openai import OpenAI
            return OpenAI(
                api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url="https://api.deepseek.com",
            )
        if self.provider == "doubao":
            from openai import OpenAI
            return OpenAI(
                api_key=os.environ["DOUBAO_API_KEY"],
                base_url="https://ark.cn-beijing.volces.com/api/v3",
            )
        if self.provider == "claude":
            import anthropic
            return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def chat(self, prompt: str, system: str = "") -> str:
        if self.provider in ("deepseek", "doubao"):
            model = "deepseek-chat" if self.provider == "deepseek" else "doubao-pro-32k"
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = self._client.chat.completions.create(model=model, messages=messages)
            return resp.choices[0].message.content
        if self.provider == "claude":
            kwargs = {"model": "claude-sonnet-4-6", "max_tokens": 4096,
                      "messages": [{"role": "user", "content": prompt}]}
            if system:
                kwargs["system"] = system
            resp = self._client.messages.create(**kwargs)
            return resp.content[0].text
