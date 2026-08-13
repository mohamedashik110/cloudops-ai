from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .services import ask_copilot


class CopilotChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        question = request.data.get("question")
        if not question:
            return Response(
                {"error": "'question' field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        days = int(request.data.get("days", 90))
        organization = request.user.organization

        result = ask_copilot(organization, question, days=days)
        return Response(result)
