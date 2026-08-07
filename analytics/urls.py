from django.urls import path
from .views import CostSummaryView, MonthlyReportView

urlpatterns = [
    path("analytics/summary/", CostSummaryView.as_view(), name="analytics-summary"),
    path("reports/monthly/", MonthlyReportView.as_view(), name="monthly-report"),
]
