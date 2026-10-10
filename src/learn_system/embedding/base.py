"""Embedding 提供者接口"""

from abc import ABC, abstractmethod
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Embedding 提供者协议"""

    @property
    def model_name(self) -> str:
        """模型名称"""
        ...

    @property
    def dimension(self) -> int:
        """向量维度"""
        ...

    def embed(self, text: str) -> list[float]:
        """生成单个文本的 embedding 向量"""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成 embedding 向量"""
        ...


class BaseEmbeddingProvider(ABC):
    """Embedding 提供者基类"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """生成单个文本的 embedding 向量"""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成 embedding 向量"""
        pass
