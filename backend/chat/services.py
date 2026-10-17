"""RAG 引擎单例服务"""

import threading
from pathlib import Path

from learn_system.config.settings import settings
from learn_system.embedding.local import LocalEmbeddingProvider
from learn_system.llm.openai_client import OpenAIClient
from learn_system.retriever.chroma_store import ChromaVectorStore
from learn_system.retriever.rag_engine import RAGEngine
from learn_system.retriever.retriever import Retriever

_lock = threading.Lock()
_engine: RAGEngine | None = None

# 仓库根目录（backend/chat/services.py -> 上溯三级）
REPO_ROOT = Path(__file__).resolve().parents[2]


def _resolve(path: Path) -> Path:
    """相对路径统一解析到仓库根目录，避免受 CWD 影响"""
    return path if path.is_absolute() else REPO_ROOT / path


def get_engine() -> RAGEngine:
    """返回全局唯一的 RAGEngine 实例（模型懒加载，首次提问时才加载）"""
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                provider = LocalEmbeddingProvider(model_name=settings.embedding_model)
                store = ChromaVectorStore(persist_dir=_resolve(settings.chroma_dir))
                retriever = Retriever(
                    vector_store=store,
                    embedding_provider=provider,
                    top_k=settings.retrieval_top_k,
                )
                llm = OpenAIClient(
                    api_key=settings.llm_api_key,
                    base_url=settings.llm_base_url,
                    model=settings.llm_model,
                    temperature=settings.llm_temperature,
                )
                _engine = RAGEngine(retriever=retriever, llm_client=llm)
    return _engine
