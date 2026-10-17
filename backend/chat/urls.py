from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chat.views import ChatView, ConversationViewSet

router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("", include(router.urls)),
]
