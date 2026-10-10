"""LLM 提供者接口"""

from abc import ABC, abstractmethod
from typing import Protocol


class LLMResponse:
    """LLM 响应"""

    def __init__(self, content: str, model: str, usage: dict | None = None):
        self.content = content
        self.model = model
        self.usage = usage or {}

    def __repr__(self) -> str:
        return f"LLMResponse(content={self.content[:50]}..., model={self.model})"


class LLMClient(Protocol):
    """LLM 客户端协议"""

    @property
    def model(self) -> str:
        """模型名称"""
        ...

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成回复"""
        ...


class BaseLLMClient(ABC):
    """LLM 客户端基类"""

    @property
    @abstractmethod
    def model(self) -> str:
        """模型名称"""
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成回复"""
        pass
