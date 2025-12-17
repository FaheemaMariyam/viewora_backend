from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsApprovedBroker(BasePermission):
    def has_permission(self, request, view):
        p = request.user.profile
        return p.role == 'broker' and p.is_admin_approved


class IsApprovedSeller(BasePermission):
    def has_permission(self, request, view):
        p = request.user.profile
        return p.role == 'seller' and p.is_admin_approved
