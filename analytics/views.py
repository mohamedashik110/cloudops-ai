from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .services import get_cost_summary


class CostSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        summary = get_cost_summary(request.user.organization, days=days)
        return Response(summary)


import csv
from django.http import HttpResponse
from cloud_accounts.models import CostRecord


class MonthlyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        summary = get_cost_summary(request.user.organization, days=days)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="cost_report.csv"'

        writer = csv.writer(response)
        writer.writerow(["CloudOps AI - Cost Report"])
        writer.writerow(["Period", summary["period"]])
        writer.writerow(["Total Cost (USD)", summary["total_cost"]])
        writer.writerow([])
        writer.writerow(["Top Services", "Amount (USD)"])
        for s in summary["top_services"]:
            writer.writerow([s["service"], s["amount"]])
        writer.writerow([])
        writer.writerow(["Date", "Amount (USD)"])
        for t in summary["trend"]:
            writer.writerow([t["date"], t["amount"]])

        return response
