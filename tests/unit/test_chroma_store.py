"""Chroma 向量存储集成测试（内存模式）"""

import uuid

from learn_system.models.chunk import Chunk
from learn_system.retriever.chroma_store import ChromaVectorStore


def _store(persist_dir=None):
    return ChromaVectorStore(
        persist_dir=persist_dir, collection_name=f"test_{uuid.uuid4().hex}"
    )


def _chunk(chunk_id: str, text: str, url: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id="d1",
        chunk_index=0,
        text=text,
        section_path=["T"],
        source_url=url,
        version="3.15",
    )


def test_add_and_search_returns_text():
    store = _store()
    store.add_chunks(
        [
            _chunk(
                "c1", "Python print function", "https://docs.python.org/3.15/library/functions.html"
            )
        ],
        [[0.1] * 8],
    )

    results = store.search([0.1] * 8, 1)

    assert len(results) == 1
    assert results[0].chunk.text == "Python print function"
    assert results[0].chunk.source_url == "https://docs.python.org/3.15/library/functions.html"


def test_upsert_updates_existing_chunk():
    store = _store()
    store.add_chunks([_chunk("c1", "old text", "https://a")], [[0.1] * 8])
    store.add_chunks([_chunk("c1", "new text", "https://a")], [[0.2] * 8])

    assert store.count() == 1
    results = store.search([0.2] * 8, 1)
    assert results[0].chunk.text == "new text"


def test_clear_then_reuse():
    store = _store()
    store.add_chunks([_chunk("c1", "text", "https://a")], [[0.1] * 8])

    store.clear()
    assert store.count() == 0

    store.add_chunks([_chunk("c2", "text2", "https://b")], [[0.1] * 8])
    assert store.count() == 1


def test_clear_on_fresh_store():
    """测试未初始化时 clear（应初始化并删除已有集合）"""
    store = _store()
    store.clear()
    assert store.count() == 0


def test_delete_by_document_ids():
    store = _store()
    c1 = Chunk(
        chunk_id="c1",
        document_id="doc_a",
        chunk_index=0,
        text="t1",
        section_path=["T"],
        source_url="https://a",
    )
    c2 = Chunk(
        chunk_id="c2",
        document_id="doc_b",
        chunk_index=0,
        text="t2",
        section_path=["T"],
        source_url="https://b",
    )
    store.add_chunks([c1, c2], [[0.1] * 8, [0.2] * 8])

    assert store.count() == 2
    assert store.list_document_ids() == {"doc_a", "doc_b"}

    store.delete_by_document_ids(["doc_a"])
    assert store.count() == 1
    assert store.list_document_ids() == {"doc_b"}
