"""向量存储测试"""

from learn_system.models.chunk import Chunk
from learn_system.retriever.vector_store import BaseVectorStore, SearchResult


class TestSearchResult:
    """SearchResult 测试"""

    def test_search_result_creation(self):
        """测试创建搜索结果"""
        chunk = Chunk(
            chunk_id="doc_test_001_chunk_0000",
            document_id="doc_test_001",
            chunk_index=0,
            text="Test text",
            section_path=["Home"],
        )
        result = SearchResult(chunk=chunk, score=0.95, distance=0.05)

        assert result.chunk == chunk
        assert result.score == 0.95
        assert result.distance == 0.05

    def test_search_result_repr(self):
        """测试字符串表示"""
        chunk = Chunk(
            chunk_id="doc_test_001_chunk_0000",
            document_id="doc_test_001",
            chunk_index=0,
            text="Test text",
        )
        result = SearchResult(chunk=chunk, score=0.95)

        assert "0.9500" in repr(result)
        assert "doc_test_001_chunk_0000" in repr(result)


class TestVectorStoreProtocol:
    """VectorStore 协议测试"""

    def test_store_protocol(self):
        """测试协议定义"""
        from unittest.mock import MagicMock

        mock_store = MagicMock(spec=BaseVectorStore)
        mock_store.count.return_value = 10

        assert mock_store.count() == 10
