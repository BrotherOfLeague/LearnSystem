"""本地 Embedding 实现

使用 sentence-transformers 生成 embedding。检测到 CUDA 时自动使用 GPU 并启用半精度，
以适配小显存显卡；否则回退到 CPU。
"""

import logging

from learn_system.embedding.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """本地 Embedding 提供者"""

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str | None = None,
        normalize: bool = True,
    ):
        self._model_name = model_name
        self._device = device  # None 表示自动检测
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

    def _resolve_device(self) -> str:
        """自动选择设备：优先 CUDA，否则 CPU"""
        if self._device:
            return self._device
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    def _ensure_model(self) -> None:
        """确保模型已加载"""
        if self._model is None:
            try:
                import torch
                from sentence_transformers import SentenceTransformer
            except ImportError as err:
                raise ImportError(
                    "sentence-transformers not installed. Install with: pip install sentence-transformers"
                ) from err

            device = self._resolve_device()
            model_kwargs: dict = {}
            if device == "cuda":
                # 半精度以适配小显存显卡（如 3GB 的 GTX 1060）
                model_kwargs["torch_dtype"] = torch.float16

            logger.info(f"Loading embedding model: {self._model_name} on {device}")
            self._model = SentenceTransformer(
                self._model_name, device=device, model_kwargs=model_kwargs
            )
            self._dimension = self._get_dimension(self._model)
            logger.info(f"Model loaded, dimension: {self._dimension}")

    @staticmethod
    def _get_dimension(model) -> int:
        if hasattr(model, "get_embedding_dimension"):
            return model.get_embedding_dimension()
        return model.get_sentence_embedding_dimension()

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
