"""RAG 引擎测试"""

from unittest.mock import MagicMock

import pytest

from learn_system.llm.base import LLMResponse
from learn_system.models.chunk import Chunk
from learn_system.retriever.rag_engine import RAGEngine, RAGResponse, Source
from learn_system.retriever.vector_store import SearchResult


@pytest.fixture
def mock_retriever():
    retriever = MagicMock()
    chunks = [
        Chunk(
            chunk_id="chunk_001",
            document_id="doc_001",
            chunk_index=0,
            text="Python print function prints to stdout.",
            source_url="https://docs.python.org/3.12/library/functions.html#print",
        ),
        Chunk(
            chunk_id="chunk_002",
            document_id="doc_001",
            chunk_index=1,
            text="Use sys.stdout.write for more control.",
            source_url="https://docs.python.org/3.12/library/sys.html",
        ),
    ]
    results = [
        SearchResult(chunk=chunks[0], score=0.95),
        SearchResult(chunk=chunks[1], score=0.85),
    ]
    retriever.retrieve.return_value = results
    return retriever


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.model = "gpt-4"
    llm.generate.return_value = LLMResponse(
        content="The print() function prints to standard output.",
        model="gpt-4",
    )
    return llm


class TestRAGEngine:
    def test_ask_with_results(self, mock_retriever, mock_llm):
        engine = RAGEngine(mock_retriever, mock_llm)
        response = engine.ask("How to print in Python?")

        assert isinstance(response, RAGResponse)
        assert "print" in response.answer.lower()
        assert response.evidence_count == 2
        assert len(response.sources) == 2

    def test_ask_with_no_results(self, mock_retriever, mock_llm):
        mock_retriever.retrieve.return_value = []
        engine = RAGEngine(mock_retriever, mock_llm)
        response = engine.ask("Unrelated question")

        assert "无法" in response.answer or "没有" in response.answer
        assert response.evidence_count == 0

    def test_build_prompt(self, mock_retriever, mock_llm):
        engine = RAGEngine(mock_retriever, mock_llm)
        prompt = engine._build_prompt("Test question?", "Some context")

        assert "Test question?" in prompt
        assert "Some context" in prompt

    def test_build_prompt_with_history(self, mock_retriever, mock_llm):
        engine = RAGEngine(mock_retriever, mock_llm)
        prompt = engine._build_prompt(
            "Question?",
            "Some context",
            [
                {"role": "user", "content": "前一个问题"},
                {"role": "assistant", "content": "前一个回答"},
            ],
        )

        assert "对话历史" in prompt
        assert "前一个问题" in prompt
        assert "前一个回答" in prompt

    def test_ask_stream_yields_deltas_then_done(self):
        class StreamingLLM:
            model = "gpt-4"

            def generate_stream(self, prompt):
                yield "第一段"
                yield "第二段"

        retriever = MagicMock()
        retriever.retrieve.return_value = [
            SearchResult(
                chunk=Chunk(
                    chunk_id="c1",
                    document_id="d1",
                    chunk_index=0,
                    text="text",
                    section_path=["T"],
                    source_url="https://a",
                ),
                score=0.9,
            )
        ]
        engine = RAGEngine(retriever, StreamingLLM())

        events = list(engine.ask_stream("question"))

        kinds = [kind for kind, _ in events]
        assert kinds == ["delta", "delta", "done"]
        assert events[-1][1]["answer"] == "第一段第二段"
        assert events[-1][1]["sources"][0]["url"] == "https://a"


class TestRAGResponse:
    def test_format_with_sources(self):
        response = RAGResponse(
            question="What is Python?",
            answer="Python is a programming language.",
            sources=[Source(url="https://python.org", path="", title="Python", score=0.9)],
            evidence_count=1,
        )
        formatted = response.format()
        assert "What is Python?" in formatted
        assert "Python is a programming language" in formatted
        assert "python.org" in formatted


class TestSource:
    def test_source_creation(self):
        source = Source(url="https://example.com", path="", title="Example", score=0.95)
        assert source.url == "https://example.com"
        assert source.title == "Example"
        assert source.score == 0.95
