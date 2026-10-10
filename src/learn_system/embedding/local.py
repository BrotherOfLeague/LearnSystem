"""本地 Embedding 实现

使用 sentence-transformers 生成 embedding。
"""

import logging

from learn_system.embedding.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """本地 Embedding 提供者

    使用 sentence-transformers 模型生成 embedding。
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str | None = None,
        normalize: bool = True,
    ):
        self._model_name = model_name
        self._device = device or "cpu"
        self._normalize = normalize
        self._model = None
        self._dimension: int | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._ensure_model()
        assert self._dimension is not None
        return self._dimension

    def _ensure_model(self) -> None:
        """确保模型已加载"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading embedding model: {self._model_name}")
                self._model = SentenceTransformer(self._model_name, device=self._device)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded, dimension: {self._dimension}")
            except ImportError as err:
                raise ImportError(
                    "sentence-transformers not installed. Install with: pip install sentence-transformers"
                ) from err

    def embed(self, text: str) -> list[float]:
        """生成单个文本的 embedding 向量"""
        self._ensure_model()
        assert self._model is not None
        embedding = self._model.encode(text, normalize_embeddings=self._normalize)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成 embedding 向量"""
        self._ensure_model()
        assert self._model is not None
        embeddings = self._model.encode(texts, normalize_embeddings=self._normalize, batch_size=32)
        return embeddings.tolist()
