from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Organization


class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "organization", "is_staff"]
    list_filter = ["role", "organization", "is_staff"]
    search_fields = ["username", "email"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Organization Info", {"fields": ("organization", "role")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Organization Info", {"fields": ("organization", "role")}),
    )


admin.site.register(User, UserAdmin)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
