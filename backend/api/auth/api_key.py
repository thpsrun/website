from __future__ import annotations

from typing import Optional

from django.http import HttpRequest
from ninja.security import APIKeyHeader
from rest_framework_api_key.models import APIKey


class APIKeyAuth(APIKeyHeader):
    """API key authentication for use with Django Ninja API endpoints.

    Using the django-rest-framework-api-key system, this is used to validate it. API keys need to
    be provided with the `X-API-Key` header.
    """

    param_name: str = "X-API-Key"

    def authenticate(
        self,
        request: HttpRequest,
        key: str,
    ) -> Optional[str]:
        """Validates the provided API key and ensures it is noted in the database.

        Args:
            request: The HTTP request object; goes unused.
            key: The API key from the X-API-Key header within the HTTP request.

        Returns:
            API key. Returns `None` if it is invalid.
        """
        try:
            api_key: Optional[APIKey] = APIKey.objects.get_from_key(key)
            if api_key:
                return key
        except APIKey.DoesNotExist:
            pass

        return None


class ReadOnlyAuth:
    """Read-only authentication for Django Ninja API endpoints.

    This authentication class allows:
    - GET requests without authentication.
    - All other methods (POST, PUT, DELETE, PATCH) require a valid API key. This API key can be
    created through the `django-rest-framework-api-key` module.
    """

    def __call__(
        self,
        request: HttpRequest,
    ) -> Optional[str]:
        """Authenticate the request based upon the HTTP method provided.

        This will authenticate the requested based upon the HTTP method provided. GET requests will
        automatically pass with no further authentication; all other methods will require a certain
        key, which is then based upon the role of the key.

        Args:
            request: The HTTP request object that will have the key to access the API.

        Returns:
            - `None` for GET requests.
            - API key validation result for other methods.
        """
        if request.method == "GET":
            pass

        api_key_auth: APIKeyAuth = APIKeyAuth()

        api_key: Optional[str] = request.headers.get(api_key_auth.param_name)
        if not api_key:
            return None

        return api_key_auth.authenticate(request, api_key)


api_key_required: APIKeyAuth = APIKeyAuth()
read_only_auth: ReadOnlyAuth = ReadOnlyAuth()
