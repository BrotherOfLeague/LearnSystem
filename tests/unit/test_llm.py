"""LLM 客户端测试"""

from unittest.mock import MagicMock

from learn_system.llm.base import BaseLLMClient, LLMResponse


class TestLLMResponse:
    def test_response_creation(self):
        resp = LLMResponse(content="Test response", model="gpt-4")
        assert resp.content == "Test response"
        assert resp.model == "gpt-4"

    def test_response_repr(self):
        resp = LLMResponse(content="Short answer", model="gpt-4")
        assert "gpt-4" in repr(resp)


class TestLLMClient:
    def test_client_protocol(self):
        mock_client = MagicMock(spec=BaseLLMClient)
        mock_client.model = "gpt-4"
        mock_client.generate.return_value = LLMResponse(content="Test", model="gpt-4")

        assert mock_client.model == "gpt-4"
        resp = mock_client.generate("test prompt")
        assert resp.content == "Test"
