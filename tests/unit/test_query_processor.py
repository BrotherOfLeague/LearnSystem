"""查询改写测试"""

from unittest.mock import MagicMock

from learn_system.llm.base import LLMResponse
from learn_system.retriever.query_processor import QueryProcessor


def _processor(content: str) -> QueryProcessor:
    llm = MagicMock()
    llm.generate.return_value = LLMResponse(content=content, model="gpt")
    return QueryProcessor(llm)


def test_extract_keywords_parses_comma_separated():
    processor = _processor("decorator, function")
    assert processor.extract_keywords("什么是装饰器？") == ["decorator", "function"]


def test_extract_keywords_handles_chinese_punctuation():
    processor = _processor("generator，yield")
    assert processor.extract_keywords("生成器是什么？") == ["generator", "yield"]


def test_rewrite_appends_keywords():
    processor = _processor("generator")
    assert processor.rewrite("生成器是什么？") == "生成器是什么？ generator"


def test_rewrite_returns_original_when_empty():
    processor = _processor("")
    assert processor.rewrite("你好") == "你好"
