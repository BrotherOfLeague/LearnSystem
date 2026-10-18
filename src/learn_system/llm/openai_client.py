"""OpenAI LLM 客户端"""

import logging

from learn_system.llm.base import BaseLLMClient, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM 客户端"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = None

    @property
    def model(self) -> str:
        return self._model

    def _ensure_client(self):
        """确保客户端已初始化"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as err:
                raise ImportError("openai not installed. Install with: pip install openai") from err

            try:
                import httpx2 as _httpx
            except ImportError:
                import httpx as _httpx

            # 禁用代理自动检测：避免误读系统代理（如 Clash 未运行时）导致请求超时
            http_client = _httpx.Client(trust_env=False)
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                http_client=http_client,
                timeout=120.0,
            )

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成回复"""
        self._ensure_client()
        assert self._client is not None

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_tokens", self._max_tokens),
            )

            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }

            return LLMResponse(content=content, model=self._model, usage=usage)

        except Exception as err:
            logger.error(f"LLM generation failed: {err}")
            raise

    def generate_stream(self, prompt: str, **kwargs):
        """流式生成回复，逐段 yield 文本"""
        self._ensure_client()
        assert self._client is not None

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self._temperature),
            max_tokens=kwargs.get("max_tokens", self._max_tokens),
            stream=True,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
