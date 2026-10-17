from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status


class ChatApiTests(TestCase):
    def test_chat_requires_question(self):
        resp = self.client.post(reverse("chat"), {}, content_type="application/json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    @patch("chat.views.get_engine")
    def test_chat_returns_answer_and_sources(self, mock_get_engine):
        engine = MagicMock()
        engine.ask.return_value = MagicMock(
            answer="答案内容",
            sources=[],
            evidence_count=0,
        )
        mock_get_engine.return_value = engine

        resp = self.client.post(
            reverse("chat"),
            {"question": "有哪些内置函数"},
            content_type="application/json",
        )

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["answer"] == "答案内容"
        assert "conversation_id" in data
        # 后续同一会话追问应携带历史
        engine.ask.assert_called_with("有哪些内置函数", history=[])

    def test_conversation_list_and_detail(self):
        resp = self.client.get(reverse("conversation-list"))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []
