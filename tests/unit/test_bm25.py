"""BM25 关键词检索测试"""

from learn_system.models.chunk import Chunk
from learn_system.retriever.bm25 import BM25Index, tokenize


def _chunk(cid: str, text: str) -> Chunk:
    return Chunk(chunk_id=cid, document_id="d", chunk_index=0, text=text)


def test_tokenize():
    assert tokenize("JSON load and dump") == ["json", "load", "dump"]
    assert tokenize("sorted() 函数") == ["sorted"]
    assert tokenize("os.path.join") == ["os", "path", "join"]
    # 停用词被过滤
    assert tokenize("the Python for loop") == ["loop"]


def test_bm25_search_ranks_relevant_docs():
    chunks = [
        _chunk("c1", "The json module provides json.load and json.dump functions"),
        _chunk("c2", "The sorted function returns a sorted list"),
        _chunk("c3", "unrelated text about networking and sockets"),
    ]
    index = BM25Index(chunks)

    results = index.search("json load", top_k=3)
    assert results[0].chunk.chunk_id == "c1"

    results2 = index.search("sorted", top_k=3)
    assert results2[0].chunk.chunk_id == "c2"


def test_bm25_empty_query_returns_empty():
    index = BM25Index([_chunk("c1", "some text")])
    assert index.search("只有中文没有英文") == []
