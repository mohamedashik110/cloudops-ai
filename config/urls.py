from django.contrib import admin
from django.urls import path, include
from common.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health"),
    path("api/v1/auth/", include("users.urls")),
    path("api/v1/", include("cloud_accounts.urls")),
    path("api/v1/", include("analytics.urls")),
    path("api/v1/", include("ml_engine.urls")),
    path("api/v1/", include("ai_copilot.urls")),
]
