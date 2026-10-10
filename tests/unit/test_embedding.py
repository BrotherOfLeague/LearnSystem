"""Embedding 提供者测试"""

from unittest.mock import MagicMock

from learn_system.embedding.base import BaseEmbeddingProvider


class TestBaseEmbeddingProvider:
    """测试基础接口"""

    def test_provider_protocol(self):
        """测试协议定义"""
        # 创建一个模拟的提供者
        mock_provider = MagicMock(spec=BaseEmbeddingProvider)
        mock_provider.model_name = "test-model"
        mock_provider.dimension = 768
        mock_provider.embed.return_value = [0.1] * 768
        mock_provider.embed_batch.return_value = [[0.1] * 768, [0.2] * 768]

        # 测试接口方法
        assert mock_provider.model_name == "test-model"
        assert mock_provider.dimension == 768
        result = mock_provider.embed("test text")
        assert len(result) == 768
        batch_results = mock_provider.embed_batch(["text1", "text2"])
        assert len(batch_results) == 2
