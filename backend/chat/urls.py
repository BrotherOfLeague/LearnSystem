from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chat.views import ChatStreamView, ChatView, ConversationViewSet, health

router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("chat/stream/", ChatStreamView.as_view(), name="chat-stream"),
    path("health/", health, name="health"),
    path("", include(router.urls)),
]
