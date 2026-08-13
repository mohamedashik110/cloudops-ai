from django.urls import path
from .views import CopilotChatView

urlpatterns = [
    path("copilot/chat/", CopilotChatView.as_view(), name="copilot-chat"),
]
