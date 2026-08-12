from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .services import generate_forecast
from .models import ForecastResult
from .serializers import ForecastResultSerializer


class ForecastView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days_ahead = int(request.query_params.get("days", 30))
        organization = request.user.organization

        try:
            forecast = generate_forecast(organization, days_ahead=days_ahead)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Save the forecast for historical record-keeping
        result = ForecastResult.objects.create(
            organization=organization,
            forecast_period=forecast["forecast_period"],
            predicted_total=forecast["predicted_total"],
            mae=forecast["model_confidence"]["mae"],
            based_on_days=forecast["model_confidence"]["based_on_days"],
            daily_predictions=forecast["daily_predictions"],
        )

        serializer = ForecastResultSerializer(result)
        return Response(serializer.data)


class ForecastHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        forecasts = ForecastResult.objects.filter(
            organization=request.user.organization
        )[:10]
        serializer = ForecastResultSerializer(forecasts, many=True)
        return Response(serializer.data)
