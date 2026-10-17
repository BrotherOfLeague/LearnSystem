from django.conf import settings as django_settings
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Conversation, Message
from chat.serializers import ConversationSerializer
from chat.services import get_engine


@api_view(["GET"])
def health(request):
    """健康检查"""
    return Response({"status": "ok", "service": "learn-system-backend"})


class ConversationViewSet(viewsets.ModelViewSet):
    """会话的增删查（列表 / 详情含消息）"""

    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer


class ChatView(APIView):
    """发送问题，返回回答与来源，并持久化对话历史"""

    def post(self, request) -> Response:
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response(
                {"error": "question 不能为空"}, status=status.HTTP_400_BAD_REQUEST
            )

        conversation_id = request.data.get("conversation_id")
        conversation = None
        if conversation_id:
            conversation = Conversation.objects.filter(id=conversation_id).first()
            if conversation is None:
                return Response(
                    {"error": "会话不存在"}, status=status.HTTP_404_NOT_FOUND
                )

        if conversation is None:
            conversation = Conversation.objects.create(title=question[:50] or "新对话")

        # 取最近若干条历史（按时间倒序取再反转，得到正序的最近记录）
        history_limit = getattr(django_settings, "CHAT_HISTORY_LIMIT", 6)
        recent = list(conversation.messages.order_by("-created_at")[:history_limit])
        recent.reverse()
        history = [{"role": m.role, "content": m.content} for m in recent]

        try:
            response = get_engine().ask(question, history=history)
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"error": f"问答失败: {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        sources = [
            {
                "title": s.title,
                "url": s.url or s.path,
                "score": round(s.score, 4),
            }
            for s in response.sources
        ]

        Message.objects.create(conversation=conversation, role="user", content=question)
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=response.answer,
            sources=sources,
        )

        return Response(
            {
                "conversation_id": str(conversation.id),
                "answer": response.answer,
                "sources": sources,
                "evidence_count": response.evidence_count,
            }
        )
