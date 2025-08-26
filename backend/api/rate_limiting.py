from __future__ import annotations

import hashlib
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

from .models import RoleAPIKey


# Approach 1: Django-ratelimit Integration
def api_ratelimit(rate: str = "100/m", key: str = "ip", block: bool = True) -> Callable[[Callable], Callable]:
    """
    Django-ratelimit decorator adapted for Django Ninja.

    Args:
        rate: Rate limit string (e.g., "100/m", "10/s", "1000/h")
        key: What to rate limit by ('ip', 'user', 'header:x-api-key')
        block: Whether to block or just mark the request

    Usage:
        @api_ratelimit(rate="50/m", key="header:x-api-key")
        @router.get("/limited-endpoint")
        def limited_view(request):
            return {"message": "Success"}
    """

    def decorator(func):
        # Apply django-ratelimit decorator
        @ratelimit(key=key, rate=rate, block=block)
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            try:
                return func(request, *args, **kwargs)
            except Ratelimited:
                return JsonResponse(
                    {
                        "error": "Rate limit exceeded",
                        "details": f"Maximum {rate} requests allowed",
                        "code": 429,
                    },
                    status=429,
                )

        return wrapper

    return decorator


# Approach 2: Role-based Rate Limiting
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
        "public": ("100/h", 100, 3600),  # 100 per hour
        "read_only": ("500/h", 500, 3600),  # 500 per hour
        "contributor": ("1000/h", 1000, 3600),  # 1000 per hour
        "moderator": ("2000/h", 2000, 3600),  # 2000 per hour
        "admin": ("5000/h", 5000, 3600),  # 5000 per hour
    }

    def __init__(self, cache_prefix: str = "api_rate_limit"):
        self.cache_prefix = cache_prefix

    def get_cache_key(self, identifier: str, window: str) -> str:
        """Generate cache key for rate limiting."""
        return f"{self.cache_prefix}:{identifier}:{window}"

    def get_rate_limit_info(self, request: HttpRequest) -> tuple:
        """
        Get rate limit information for the request.

        Returns:
            tuple: (role, limit_count, window_seconds, identifier)
        """
        # Check if request has API key
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            try:
                api_key_obj = RoleAPIKey.objects.get_from_key(api_key_header)
                if api_key_obj:
                    role = api_key_obj.role
                    identifier = f"key_{api_key_obj.id}"
                else:
                    # Invalid key, treat as public
                    role = "public"
                    identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
            except RoleAPIKey.DoesNotExist:
                role = "public"
                identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
        else:
            # No API key, use IP-based limiting
            role = "public"
            identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"

        rate_str, limit_count, window_seconds = self.ROLE_LIMITS[role]
        return role, limit_count, window_seconds, identifier

    def is_rate_limited(self, request: HttpRequest) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited.

        Returns:
            tuple: (is_limited: bool, rate_info: dict)
        """
        role, limit_count, window_seconds, identifier = self.get_rate_limit_info(
            request
        )

        # Create time window (current hour)
        current_time = int(time.time())
        window_start = current_time - (current_time % window_seconds)

        cache_key = self.get_cache_key(identifier, str(window_start))

        # Get current count
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

        # Increment counter
        cache.set(cache_key, current_count + 1, window_seconds)
        rate_info["current"] = current_count + 1

        return False, rate_info


# Global rate limiter instance
role_rate_limiter = RoleBasedRateLimit()


def role_based_rate_limit(func: Callable) -> Callable:
    """
    Decorator for role-based rate limiting on Django Ninja endpoints.

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

        # Add rate limit headers to successful responses
        response = func(request, *args, **kwargs)
        if hasattr(response, "headers"):
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(
                rate_info["limit"] - rate_info["current"]
            )
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])

        return response

    return wrapper


# Approach 3: Simple Redis-based Rate Limiter
class SimpleRateLimit:
    """
    Simple Redis-based rate limiter using sliding window.

    Usage:
        limiter = SimpleRateLimit(limit=100, window=60)  # 100 requests per minute

        @limiter.limit_by_key("header:x-api-key")
        @router.get("/endpoint")
        def view(request):
            return {"message": "Success"}
    """

    def __init__(self, limit: int = 100, window: int = 60):
        self.limit = limit
        self.window = window

    def limit_by_key(self, key_type: str = "ip"):
        """
        Rate limit decorator.

        Args:
            key_type: 'ip', 'header:x-api-key', 'user', or custom function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(request: HttpRequest, *args, **kwargs):
                # Get the key to rate limit by
                if key_type == "ip":
                    rate_key = request.META.get("REMOTE_ADDR", "unknown")
                elif key_type.startswith("header:"):
                    header_name = key_type.split(":", 1)[1]
                    rate_key = request.headers.get(header_name, "unknown")
                elif key_type == "user":
                    rate_key = getattr(request.user, "id", "anonymous")
                else:
                    rate_key = "default"

                # Create cache key
                cache_key = f"simple_rate_limit:{hashlib.md5(str(rate_key).encode()).hexdigest()}"

                # Check current count
                current_time = int(time.time())
                window_start = current_time - self.window

                # Simple sliding window using cache
                requests_key = f"{cache_key}:{current_time // 60}"  # Per minute buckets
                current_count = cache.get(requests_key, 0)

                if current_count >= self.limit:
                    return JsonResponse(
                        {
                            "error": "Rate limit exceeded",
                            "details": f"Maximum {self.limit} requests per {self.window} seconds",
                            "code": 429,
                        },
                        status=429,
                    )

                # Increment counter
                cache.set(requests_key, current_count + 1, self.window)

                return func(request, *args, **kwargs)

            return wrapper

        return decorator


# Pre-configured rate limiters for common use cases
standard_limit = SimpleRateLimit(limit=100, window=60)  # 100/minute
strict_limit = SimpleRateLimit(limit=10, window=60)  # 10/minute
loose_limit = SimpleRateLimit(limit=1000, window=60)  # 1000/minute
