"""集成测试：导入 → 解析 → 分块 → 索引 → 检索 → 回答 的完整链路

用轻量关键词 embedding 替代 bge-m3，避免测试加载大模型；
用 Echo LLM 替代真实 API，测试 RAG 引擎的编排逻辑。
"""

import uuid
from pathlib import Path

from learn_system.chunker.rule_based_chunker import RuleBasedChunker
from learn_system.embedding.base import BaseEmbeddingProvider
from learn_system.llm.base import BaseLLMClient, LLMResponse
from learn_system.loaders.document_loader import DocumentLoader
from learn_system.parsers.html_parser import HtmlParser
from learn_system.retriever.chroma_store import ChromaVectorStore
from learn_system.retriever.rag_engine import RAGEngine
from learn_system.retriever.retriever import Retriever


class KeywordEmbeddingProvider(BaseEmbeddingProvider):
    """基于关键词的确定性 embedding（固定词表 + bag-of-words）"""

    VOCAB = ["json", "load", "dumps", "cooking", "recipe", "file", "serialize"]

    @property
    def model_name(self) -> str:
        return "keyword-embedding"

    @property
    def dimension(self) -> int:
        return len(self.VOCAB)

    def embed(self, text: str) -> list[float]:
        lower = text.lower()
        return [1.0 if word in lower else 0.0 for word in self.VOCAB]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class EchoLLM(BaseLLMClient):
    """返回固定回答的 LLM，用于测试 RAG 编排"""

    def __init__(self, answer: str = "回答内容"):
        self._answer = answer

    @property
    def model(self) -> str:
        return "echo-llm"

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(content=self._answer, model=self.model)


def _write_docs(docs_dir: Path) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "json.html").write_text(
        '<html><body><div class="body"><h1>json — JSON encoder and decoder</h1>'
        "<p>json.load reads a file.</p><p>json.dumps serialize objects.</p></div></body></html>",
        encoding="utf-8",
    )
    (docs_dir / "cooking.html").write_text(
        '<html><body><div class="body"><h1>Cooking</h1>'
        "<p>This is a cooking recipe about pasta.</p></div></body></html>",
        encoding="utf-8",
    )


def _build_chunks(docs_dir: Path):
    """真实链路：加载 → 解析 → 分块"""
    loader = DocumentLoader(docs_dir)
    parser = HtmlParser()
    chunker = RuleBasedChunker()
    chunks = []
    for doc in loader.load_documents():
        result = parser.parse(doc)
        assert result.success and result.document is not None
        chunks.extend(chunker.chunk_document(result.document).chunks)
    return chunks


def test_import_parse_chunk_produces_metadata(tmp_path):
    docs_dir = tmp_path / "docs"
    _write_docs(docs_dir)
    chunks = _build_chunks(docs_dir)

    assert len(chunks) >= 2

    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.source_url
        assert chunk.section_path  # 至少含标题
        assert chunk.text

    urls = {chunk.source_url for chunk in chunks}
    assert any("json.html" in (u or "") for u in urls)
    assert any("cooking.html" in (u or "") for u in urls)


def test_index_and_retrieve(tmp_path):
    docs_dir = tmp_path / "docs"
    _write_docs(docs_dir)
    chunks = _build_chunks(docs_dir)

    provider = KeywordEmbeddingProvider()
    store = ChromaVectorStore(collection_name=f"test_{uuid.uuid4().hex}")  # 内存模式
    retriever = Retriever(vector_store=store, embedding_provider=provider, top_k=3)
    retriever.add_chunks(chunks)

    assert store.count() == len(chunks)

    results = retriever.retrieve("json load")
    urls = [r.chunk.source_url or "" for r in results]
    assert any("json.html" in u for u in urls)


def test_rag_engine_end_to_end(tmp_path):
    docs_dir = tmp_path / "docs"
    _write_docs(docs_dir)
    chunks = _build_chunks(docs_dir)

    provider = KeywordEmbeddingProvider()
    store = ChromaVectorStore(collection_name=f"test_{uuid.uuid4().hex}")
    retriever = Retriever(vector_store=store, embedding_provider=provider, top_k=3)
    retriever.add_chunks(chunks)

    engine = RAGEngine(retriever=retriever, llm_client=EchoLLM("答案是 json.load"))
    response = engine.ask("json 怎么 load")

    assert response.answer == "答案是 json.load"
    assert response.evidence_count >= 1
    assert response.sources


def test_chroma_persistence(tmp_path):
    """持久化：写入后重新打开，数据仍在且可检索"""
    docs_dir = tmp_path / "docs"
    _write_docs(docs_dir)
    chunks = _build_chunks(docs_dir)

    persist_dir = tmp_path / "chroma"
    provider = KeywordEmbeddingProvider()
    coll = f"test_{uuid.uuid4().hex}"

    store1 = ChromaVectorStore(persist_dir=persist_dir, collection_name=coll)
    store1.add_chunks(chunks, [provider.embed(c.text) for c in chunks])
    assert store1.count() == len(chunks)

    # 重新打开同一目录
    store2 = ChromaVectorStore(persist_dir=persist_dir, collection_name=coll)
    assert store2.count() == len(chunks)
    results = store2.search(provider.embed("json load"), 3)
    assert any("json.html" in (r.chunk.source_url or "") for r in results)
