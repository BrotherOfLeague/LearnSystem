"""查询改写：用 LLM 从中文问题中提取英文技术关键词，增强检索查询"""

import logging

from learn_system.llm.base import LLMClient
from learn_system.retriever.retriever import Retriever
from learn_system.retriever.vector_store import SearchResult

logger = logging.getLogger(__name__)


class QueryProcessor:
    """查询改写器：从中文问题中提取英文检索关键词"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def extract_keywords(self, question: str) -> list[str]:
        """提取英文技术关键词（函数名、模块名、概念名等）"""
        prompt = (
            "从下面的中文问题中提取用于检索 Python 官方文档的英文技术关键词"
            "（函数名、模块名、概念名等），用逗号分隔，只输出关键词，不要解释。\n\n"
            f"问题：{question}\n\n关键词："
        )
        try:
            resp = self.llm_client.generate(prompt)
            raw = resp.content.replace("，", ",").replace("、", ",").replace("；", ",")
            return [k.strip().lower() for k in raw.split(",") if k.strip()]
        except Exception as e:
            logger.warning(f"关键词提取失败: {e}")
            return []

    def rewrite(self, question: str) -> str:
        """返回追加英文关键词后的查询（无关键词则原样返回）"""
        keywords = self.extract_keywords(question)
        if keywords:
            return f"{question} {' '.join(keywords)}"
        return question


class RewriteRetriever:
    """带查询改写的检索器（包装底层检索器）"""

    def __init__(self, base_retriever: Retriever, query_processor: QueryProcessor):
        self.base_retriever = base_retriever
        self.query_processor = query_processor

    def retrieve(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        rewritten = self.query_processor.rewrite(query)
        if rewritten != query:
            logger.info(f"查询改写: {query[:30]}... -> {rewritten[:60]}...")
        return self.base_retriever.retrieve(rewritten, top_k)

    def count(self) -> int:
        return self.base_retriever.count()
