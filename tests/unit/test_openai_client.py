"""OpenAI LLM 客户端测试"""

from unittest.mock import Mock

from learn_system.llm.base import LLMResponse
from learn_system.llm.openai_client import OpenAIClient


def _chunk(content: str) -> Mock:
    """构造一个流式 chunk（delta.content 为给定文本）"""
    chunk = Mock()
    chunk.choices = [Mock()]
    chunk.choices[0].delta = Mock()
    chunk.choices[0].delta.content = content
    return chunk


def _client_with_stream(items) -> OpenAIClient:
    """构造一个流式响应为 items 的客户端（绕过真实网络）"""
    client = OpenAIClient(api_key="k", base_url="http://x", model="m")
    fake_openai = Mock()
    fake_openai.chat.completions.create.return_value = iter(items)
    client._client = fake_openai
    return client


def test_generate_stream_yields_content():
    """流式有内容时，逐段 yield"""
    client = _client_with_stream([_chunk("你好"), _chunk("世界")])
    assert list(client.generate_stream("hi")) == ["你好", "世界"]


def test_generate_stream_falls_back_when_empty():
    """流式无内容时，回退到非流式 generate"""
    client = _client_with_stream([])
    client.generate = Mock(return_value=LLMResponse(content="回退答案", model="m"))
    assert list(client.generate_stream("hi")) == ["回退答案"]
