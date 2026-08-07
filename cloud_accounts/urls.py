from django.urls import path
from .views import CloudAccountListCreateView, CostRecordListView

urlpatterns = [
    path("cloud-accounts/", CloudAccountListCreateView.as_view(), name="cloud-accounts"),
    path("cost-records/", CostRecordListView.as_view(), name="cost-records"),
]
