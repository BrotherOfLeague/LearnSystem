"""BM25 关键词检索

面向英文技术文档（API 名、函数名、异常名等精确术语）的关键词检索。
"""

import json
import math
import re
from collections import Counter
from pathlib import Path

from learn_system.models.chunk import Chunk
from learn_system.retriever.vector_store import SearchResult

# 英文技术文档中的高频停用词，过滤以减少 BM25 噪声
STOPWORDS = {
    "python", "the", "a", "an", "and", "or", "of", "to", "in", "for", "on",
    "is", "are", "was", "were", "be", "been", "being", "it", "its", "this",
    "that", "these", "those", "with", "without", "as", "at", "by", "from",
    "how", "what", "why", "when", "where", "which", "who", "does", "do",
    "can", "could", "should", "would", "will", "not", "no", "if", "else",
    "then", "than", "so", "such", "also", "into", "about", "over", "under",
    "use", "using", "used", "via", "example", "examples", "see", "note",
    "new", "return", "returns", "returned",
}


def tokenize(text: str) -> list[str]:
    """简单分词：提取小写字母、数字、下划线，并过滤停用词"""
    tokens = re.findall(r"[a-z0-9_]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS]


def load_chunks(chunks_file: Path) -> list[Chunk]:
    """从 chunks.jsonl 读取分块"""
    chunks: list[Chunk] = []
    with open(chunks_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(Chunk(**json.loads(line)))
    return chunks


class BM25Index:
    """BM25 Okapi 关键词索引"""

    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.corpus = [tokenize(c.to_embedding_text()) for c in chunks]
        self.doc_len = [len(doc) for doc in self.corpus]
        self.N = len(self.corpus)
        self.avgdl = sum(self.doc_len) / self.N if self.N else 0.0

        self.doc_freqs = [Counter(doc) for doc in self.corpus]
        df: Counter[str] = Counter()
        for freq in self.doc_freqs:
            for term in freq:
                df[term] += 1
        self.idf = {
            term: math.log(1 + (self.N - n + 0.5) / (n + 0.5))
            for term, n in df.items()
        }

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """检索最相关的分块，返回按 BM25 分数排序的结果（分数归一化到 [0,1]）"""
        if self.N == 0:
            return []

        query_tokens = tokenize(query)
        scores = [0.0] * self.N
        for term in query_tokens:
            idf = self.idf.get(term)
            if idf is None or idf <= 0:
                continue
            for i in range(self.N):
                f = self.doc_freqs[i].get(term, 0)
                if f == 0:
                    continue
                dl = self.doc_len[i]
                denom = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i] += idf * f * (self.k1 + 1) / denom

        ranked = sorted(
            ((scores[i], i) for i in range(self.N) if scores[i] > 0),
            key=lambda x: x[0],
            reverse=True,
        )[:top_k]

        if not ranked:
            return []

        max_score = ranked[0][0]
        return [
            SearchResult(chunk=self.chunks[idx], score=score / max_score)
            for score, idx in ranked
        ]
