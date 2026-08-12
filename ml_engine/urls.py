from django.urls import path
from .views import ForecastView, ForecastHistoryView

urlpatterns = [
    path("predictions/forecast/", ForecastView.as_view(), name="forecast"),
    path("predictions/history/", ForecastHistoryView.as_view(), name="forecast-history"),
]
