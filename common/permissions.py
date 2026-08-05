from rest_framework.permissions import BasePermission


class IsOrgAdmin(BasePermission):
    """Only Admins of the user's own organization."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsOrgManagerOrAdmin(BasePermission):
    """Managers and Admins — not Viewers."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "manager")
        )


class IsSameOrganization(BasePermission):
    """
    Object-level check: user can only access objects
    belonging to their own organization.
    """
    def has_object_permission(self, request, view, obj):
        return obj.organization_id == request.user.organization_id