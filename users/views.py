from rest_framework import generics, permissions
from .serializers import RegisterSerializer, UserSerializer
from .models import User
from common.permissions import IsOrgAdmin


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class OrgUsersListView(generics.ListAPIView):
    """List all users in the caller's own organization. Admin-only."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]

    def get_queryset(self):
        return User.objects.filter(organization=self.request.user.organization)