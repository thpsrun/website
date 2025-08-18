from django.http import HttpRequest
from rest_framework.permissions import BasePermission


class ReadOnlyOrAuthenticated(BasePermission):
    """Permission model that allows read access to endpoints, but require auth for others.

    Custom permission to only allow read access without authentication, but require authentication
    for write operations. API Key will be required to access non-specified methods.
    """

    def has_permission(
        self,
        request: HttpRequest,
        _,
    ) -> bool:
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return bool(request.user and request.user.is_authenticated)
