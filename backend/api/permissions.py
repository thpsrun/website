from typing import Any, Dict, Optional

from django.http import HttpRequest
from django.utils import timezone
from ninja.security import APIKeyHeader

from api.models import RoleAPIKey


class HasRoleAPIKey:
    """
    Custom permission class for RoleAPIKey model.

    Validates API keys against the RoleAPIKey model and checks role permissions.
    This replaces rest_framework's BaseHasAPIKey since we removed DRF.
    """

    def has_permission(self, request: HttpRequest, view: Any) -> bool:
        """Check if request has valid API key."""
        api_key_header: Optional[str] = request.headers.get("X-API-Key")
        if not api_key_header:
            return False

        try:
            api_key_obj: Optional[RoleAPIKey] = RoleAPIKey.objects.get_from_key(
                api_key_header
            )
            return api_key_obj is not None
        except RoleAPIKey.DoesNotExist:
            return False


class RoleBasedAPIKeyAuth(APIKeyHeader):
    """
    Django Ninja authentication class with role-based permissions.

    Validates API keys and ensures they have sufficient role permissions.
    Updates last_used timestamp when keys are successfully validated.
    """

    param_name = "X-API-Key"

    def __init__(
        self,
        required_role: str = "read_only",
    ) -> None:
        """
        Initialize with required role.

        Args:
            required_role: Minimum role required ('read_only', 'contributor', 'moderator', 'admin')
        """
        self.required_role: str = required_role
        super().__init__()

    def authenticate(
        self,
        request: HttpRequest,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Validate API key and check role permissions.

        Args:
            request: HTTP request object
            key: API key from X-API-Key header

        Returns:
            Dict with API key info if authorized, None if unauthorized
        """
        try:
            api_key_obj: Optional[RoleAPIKey] = RoleAPIKey.objects.get_from_key(key)
            if not api_key_obj:
                return None

            # Check if key has sufficient role permissions
            if not api_key_obj.has_role(self.required_role):
                return None

            # Update last used timestamp (async to avoid blocking)
            api_key_obj.last_used = timezone.now()
            api_key_obj.save(update_fields=["last_used"])

            return {
                "api_key": key,
                "api_key_obj": api_key_obj,
                "role": api_key_obj.role,
                "name": api_key_obj.name,
                "created_by": api_key_obj.created_by,
            }

        except RoleAPIKey.DoesNotExist:
            pass

        return None


class PublicOrRoleAuth:
    """
    Hybrid authentication: allows public GET requests, requires API key for other methods.

    This replaces the old ReadOnlyAuth with proper role checking.
    """

    def __init__(self, required_role: str = "read_only") -> None:
        """
        Initialize with required role for non-GET requests.

        Args:
            required_role: Minimum role required for non-GET requests
        """
        self.required_role: str = required_role
        self.role_auth: RoleBasedAPIKeyAuth = RoleBasedAPIKeyAuth(required_role)

    def __call__(self, request: HttpRequest) -> Optional[Dict[str, Any]]:
        """
        Authenticate based on HTTP method.

        Args:
            request: HTTP request object

        Returns:
            Auth info dict or None if unauthorized
        """
        # Allow GET requests without authentication
        if request.method == "GET":
            return {"role": "public", "authenticated": False, "public_access": True}

        # Require valid API key with sufficient role for other methods
        api_key_header: Optional[str] = request.headers.get("X-API-Key")
        if not api_key_header:
            return None

        return self.role_auth.authenticate(request, api_key_header)


# Pre-configured auth instances for common use cases
public_auth: PublicOrRoleAuth = PublicOrRoleAuth(
    "read_only"
)  # GET public, others need read_only+
read_only_auth: RoleBasedAPIKeyAuth = RoleBasedAPIKeyAuth("read_only")
contributor_auth: RoleBasedAPIKeyAuth = RoleBasedAPIKeyAuth("contributor")
moderator_auth: RoleBasedAPIKeyAuth = RoleBasedAPIKeyAuth("moderator")
admin_auth: RoleBasedAPIKeyAuth = RoleBasedAPIKeyAuth("admin")

# Backward compatibility
api_key_required: RoleBasedAPIKeyAuth = read_only_auth
