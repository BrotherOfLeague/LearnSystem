"""RAG 引擎"""

import logging

from learn_system.llm.base import LLMClient
from learn_system.retriever.retriever import Retriever
from learn_system.retriever.vector_store import SearchResult

logger = logging.getLogger(__name__)


class Source:
    """信息来源"""

    def __init__(self, url: str | None, path: str, title: str, score: float):
        self.url = url
        self.path = path
        self.title = title
        self.score = score


class RAGResponse:
    """RAG 响应"""

    def __init__(
        self,
        question: str,
        answer: str,
        sources: list[Source],
        evidence_count: int,
    ):
        self.question = question
        self.answer = answer
        self.sources = sources
        self.evidence_count = evidence_count

    def format(self) -> str:
        """格式化输出"""
        output = [f"**问题：** {self.question}", "", f"**回答：**\n{self.answer}"]

        if self.sources:
            output.append("")
            output.append("**参考来源：**")
            for i, source in enumerate(self.sources, 1):
                title = source.title
                url = source.url or source.path
                output.append(f"  {i}. [{title}]({url})")

        return "\n".join(output)


class RAGEngine:
    """RAG 引擎"""

    def __init__(
        self,
        retriever: Retriever,
        llm_client: LLMClient,
        min_relevance_score: float = 0.3,
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.min_relevance_score = min_relevance_score

    def ask(
        self,
        question: str,
        top_k: int | None = None,
        history: list[dict] | None = None,
    ) -> RAGResponse:
        """问答

        Args:
            question: 用户问题
            top_k: 检索结果数量
            history: 多轮对话历史，格式 [{"role": "user"/"assistant", "content": str}, ...]
        """
        results = self.retriever.retrieve(question, top_k)

        relevant = [r for r in results if r.score >= self.min_relevance_score]

        if not relevant:
            return RAGResponse(
                question=question,
                answer="抱歉，我没有找到与您问题相关的文档来回答这个问题。",
                sources=[],
                evidence_count=0,
            )

        context = self._build_context(relevant)
        prompt = self._build_prompt(question, context, history)
        response = self.llm_client.generate(prompt)
        sources = self._extract_sources(relevant)

        return RAGResponse(
            question=question,
            answer=response.content,
            sources=sources,
            evidence_count=len(relevant),
        )

    def ask_stream(
        self, question: str, top_k: int | None = None, history: list[dict] | None = None
    ):
        """流式问答

        逐段 yield ("delta", 文本)，最后 yield ("done", dict)，
        dict 含 answer / sources / evidence_count。
        """
        results = self.retriever.retrieve(question, top_k)
        relevant = [r for r in results if r.score >= self.min_relevance_score]

        if not relevant:
            no_answer = "抱歉，我没有找到与您问题相关的文档来回答这个问题。"
            yield ("delta", no_answer)
            yield ("done", {"answer": no_answer, "sources": [], "evidence_count": 0})
            return

        context = self._build_context(relevant)
        prompt = self._build_prompt(question, context, history)

        answer_parts: list[str] = []
        if hasattr(self.llm_client, "generate_stream"):
            for chunk in self.llm_client.generate_stream(prompt):
                answer_parts.append(chunk)
                yield ("delta", chunk)
        else:
            response = self.llm_client.generate(prompt)
            answer_parts.append(response.content)
            yield ("delta", response.content)

        answer = "".join(answer_parts)
        sources = [
            {"title": s.title, "url": s.url or s.path, "score": round(s.score, 4)}
            for s in self._extract_sources(relevant)
        ]
        yield ("done", {"answer": answer, "sources": sources, "evidence_count": len(relevant)})

    def _build_context(self, results: list[SearchResult]) -> str:
        """构建上下文"""
        context_parts = []

        for i, result in enumerate(results, 1):
            chunk = result.chunk
            context_parts.append(
                f"[{i}] (来源: {chunk.source_url or chunk.source_path}, "
                f"相似度: {result.score:.2f})\n{chunk.text}\n"
            )

        return "\n---\n".join(context_parts)

    def _build_prompt(self, question: str, context: str, history: list[dict] | None = None) -> str:
        """构建提示词"""
        history_section = ""
        if history:
            lines = []
            for msg in history:
                role = "用户" if msg.get("role") == "user" else "助手"
                content = (msg.get("content") or "").strip()
                if content:
                    lines.append(f"{role}：{content}")
            if lines:
                history_section = "**对话历史：**\n" + "\n".join(lines) + "\n\n"

        return f"""你是一名 Python 官方文档助手。请只用中文回答，保留准确的英文标识符、函数名和代码。

**回答规则：**
1. 只能依据下面的"参考资料"回答，不要使用资料之外的知识或编造信息。
2. 如果资料中没有足够信息，请直接说明无法根据资料回答，并建议查阅官方文档。
3. 需要引用资料时，请用 [1]、[2] 这样的编号标明出处。
4. 回答要简洁、准确。

{history_section}**参考资料：**
{context}

**问题：**
{question}

**回答：**
"""

    def _extract_sources(self, results: list[SearchResult]) -> list[Source]:
        """提取来源"""
        sources = []
        seen = set()

        for result in results:
            chunk = result.chunk
            source_key = chunk.source_url or chunk.source_path

            if source_key and source_key not in seen:
                seen.add(source_key)
                sources.append(
                    Source(
                        url=chunk.source_url,
                        path=chunk.source_path,
                        title=chunk.section_path[-1] if chunk.section_path else "Unknown",
                        score=result.score,
                    )
                )

        return sources
