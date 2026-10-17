"""向量存储接口"""

from abc import ABC, abstractmethod
from typing import Protocol

from learn_system.models.chunk import Chunk


class SearchResult:
    """搜索结果"""

    def __init__(
        self,
        chunk: Chunk,
        score: float,
        distance: float | None = None,
    ):
        self.chunk = chunk
        self.score = score
        self.distance = distance

    def __repr__(self) -> str:
        return f"SearchResult(score={self.score:.4f}, id={self.chunk.chunk_id})"


class VectorStore(Protocol):
    """向量存储协议"""

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        """添加分块到向量存储"""
        ...

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        """搜索最相似的分块"""
        ...

    def count(self) -> int:
        """返回分块数量"""
        ...

    def delete_by_document_ids(self, document_ids: list[str]) -> None:
        """按文档 ID 删除分块"""
        ...

    def clear(self) -> None:
        """清空向量存储"""
        ...


class BaseVectorStore(ABC):
    """向量存储基类"""

    @abstractmethod
    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        """添加分块到向量存储"""
        pass

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        """搜索最相似的分块"""
        pass

    @abstractmethod
    def count(self) -> int:
        """返回分块数量"""
        pass

    @abstractmethod
    def delete_by_document_ids(self, document_ids: list[str]) -> None:
        """按文档 ID 删除分块"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空向量存储"""
        pass
