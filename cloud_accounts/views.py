from rest_framework import generics, permissions
from .models import CloudAccount, CostRecord
from .serializers import CloudAccountSerializer, CostRecordSerializer
from common.permissions import IsOrgManagerOrAdmin


class CloudAccountListCreateView(generics.ListCreateAPIView):
    serializer_class = CloudAccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrAdmin]

    def get_queryset(self):
        return CloudAccount.objects.filter(organization=self.request.user.organization)


class CostRecordListView(generics.ListAPIView):
    serializer_class = CostRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = CostRecord.objects.filter(
            cloud_account__organization=self.request.user.organization
        )
        service = self.request.query_params.get("service")
        if service:
            queryset = queryset.filter(service=service)
        return queryset
