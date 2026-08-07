from django.contrib import admin
from .models import CloudAccount, CostRecord


@admin.register(CloudAccount)
class CloudAccountAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "provider", "status", "last_synced_at"]
    list_filter = ["provider", "status", "organization"]
    search_fields = ["name"]


@admin.register(CostRecord)
class CostRecordAdmin(admin.ModelAdmin):
    list_display = ["service", "amount", "currency", "date", "cloud_account", "is_synthetic"]
    list_filter = ["service", "is_synthetic", "date"]
    search_fields = ["service"]
