import time
from functools import wraps
from typing import Any, Callable, Dict

from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils import timezone

from api.models import RoleAPIKey


class RoleBasedRateLimit:
    """
    Custom rate limiter with different limits per API key role.

    Rate limits by role:
    - public: 100 requests/hour (for unauthenticated)
    - read_only: 500 requests/hour
    - contributor: 1000 requests/hour
    - moderator: 2000 requests/hour
    - admin: 5000 requests/hour
    """

    ROLE_LIMITS = {
        "public": ("100/h", 100, 3600),
        "read_only": ("500/h", 500, 3600),
        "contributor": ("1000/h", 1000, 3600),
        "moderator": ("2000/h", 2000, 3600),
        "admin": ("5000/h", 5000, 3600),
    }

    def __init__(
        self,
        cache_prefix: str = "api_rate_limit",
    ):
        self.cache_prefix = cache_prefix

    def get_cache_key(
        self,
        identifier: str,
        window: str,
    ) -> str:
        """Generate cache key for rate limiting."""
        return f"{self.cache_prefix}:{identifier}:{window}"

    def get_rate_limit_info(
        self,
        request: HttpRequest,
    ) -> tuple:
        """Get rate limit information for the request.

        Returns:
            tuple: (role, limit_count, window_seconds, identifier)
        """
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            try:
                api_key_obj = RoleAPIKey.objects.get_from_key(api_key_header)
                if api_key_obj:
                    role = api_key_obj.role
                    identifier = f"key_{api_key_obj.id}"
                else:
                    role = "public"
                    identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
            except RoleAPIKey.DoesNotExist:
                role = "public"
                identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
        else:
            role = "public"
            identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"

        rate_str, limit_count, window_seconds = self.ROLE_LIMITS[role]
        return role, limit_count, window_seconds, identifier

    def is_rate_limited(
        self,
        request: HttpRequest,
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request should be rate limited.

        Returns:
            tuple: (is_limited: bool, rate_info: dict)
        """
        role, limit_count, window_seconds, identifier = self.get_rate_limit_info(
            request
        )

        current_time = int(time.time())
        window_start = current_time - (current_time % window_seconds)

        cache_key = self.get_cache_key(identifier, str(window_start))

        current_count = cache.get(cache_key, 0)

        rate_info = {
            "role": role,
            "limit": limit_count,
            "current": current_count,
            "window_seconds": window_seconds,
            "reset_time": window_start + window_seconds,
            "identifier": identifier,
        }

        if current_count >= limit_count:
            return True, rate_info

        cache.set(cache_key, current_count + 1, window_seconds)
        rate_info["current"] = current_count + 1

        return False, rate_info


role_rate_limiter = RoleBasedRateLimit()


def role_based_rate_limit(
    func: Callable,
) -> Callable:
    """Decorator for role-based rate limiting on Django Ninja endpoints.

    Usage:
        @role_based_rate_limit
        @router.get("/protected-endpoint")
        def protected_view(request):
            return {"message": "Success"}
    """

    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        is_limited, rate_info = role_rate_limiter.is_rate_limited(request)

        if is_limited:
            reset_time = timezone.datetime.fromtimestamp(rate_info["reset_time"])
            return JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "details": {
                        "role": rate_info["role"],
                        "limit": rate_info["limit"],
                        "current": rate_info["current"],
                        "reset_time": reset_time.isoformat(),
                        "message": f"Rate limit exceeded for {rate_info['role']} role. "
                        f"Limit: {rate_info['limit']} requests per hour.",
                    },
                    "code": 429,
                },
                status=429,
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset_time"]),
                    "Retry-After": str(rate_info["reset_time"] - int(time.time())),
                },
            )

        response = func(request, *args, **kwargs)
        if hasattr(response, "headers"):
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(
                rate_info["limit"] - rate_info["current"]
            )
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])

        return response

    return wrapper
