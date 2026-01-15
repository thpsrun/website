from __future__ import annotations

import json
import logging
from typing import Callable, Optional

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from api.models import RoleAPIKey

logger = logging.getLogger(__name__)

MAX_LOG_BODY_SIZE = 10000


class APIActivityLogMiddleware:
    """Middleware to log API activities to Django admin Recent Actions.

    This captures API calls that modify data (POST, PUT, PATCH, DELETE) and
    creates LogEntry records so they appear in the Django admin's Recent Actions section.
    """

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        response = self.get_response(request)

        if (
            request.path.startswith("/api/v1/")
            and request.method in ["POST", "PUT", "PATCH", "DELETE"]
            and response.status_code < 400
        ):
            self.log_api_activity(request, response)

        return response

    def log_api_activity(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> None:
        """Log API activity to Django admin."""
        try:
            user_id = self.get_api_user_id(request)
            if not user_id:
                return

            action_flag = self.get_action_flag(request.method)
            if not action_flag:
                return

            object_info = self.extract_object_info(request)
            if not object_info:
                return

            content_type, object_id, object_repr = object_info

            change_message = self.create_change_message(request, response)

            LogEntry.objects.create(
                user_id=user_id,
                content_type=content_type,
                object_id=object_id,
                object_repr=object_repr,
                action_flag=action_flag,
                change_message=change_message,
                action_time=timezone.now(),
            )

        except Exception as e:
            # Don't break API calls if logging fails
            logger.warning(
                f"Failed to log API activity: {e}",
                exc_info=True,
                extra={"path": request.path, "method": request.method},
            )

    def get_api_user_id(
        self,
        request: HttpRequest,
    ) -> Optional[int]:
        """Get user ID from API key or create/get an API user.

        Since API calls don't have traditional Django users, we'll create
        a special user account for API activities.
        """
        try:
            api_key_header = request.headers.get("X-API-Key")
            if not api_key_header:
                return None

            api_key_obj = RoleAPIKey.objects.get_from_key(api_key_header)
            if not api_key_obj:
                return None

            username = f"api_key_{api_key_obj.name}".replace(" ", "_").replace(
                "-", "_"
            )[:150]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": "API Key",
                    "last_name": api_key_obj.name,
                    "email": f"{username}@api.thpsrun.local",
                    "is_active": False,
                    "is_staff": False,
                },
            )

            return user.id

        except Exception as e:
            logger.warning(f"Failed to get/create API user: {e}", exc_info=True)
            return None

    def get_action_flag(self, method: str) -> Optional[int]:
        """Convert HTTP method to Django admin action flag."""
        method_mapping = {
            "POST": ADDITION,
            "PUT": CHANGE,
            "PATCH": CHANGE,
            "DELETE": DELETION,
        }
        return method_mapping.get(method)

    def extract_object_info(
        self,
        request: HttpRequest,
    ) -> Optional[tuple[ContentType, Optional[str], str]]:
        """
        Extract object information from the API request.


        Returns tuple of (ContentType, object_id, object_repr) or None.
        """
        try:
            path = request.path

            model_mappings = {
                "/api/v1/games/": "srl.games",
                "/api/v1/categories/": "srl.categories",
                "/api/v1/levels/": "srl.levels",
                "/api/v1/players/": "srl.players",
                "/api/v1/runs/": "srl.runs",
                "/api/v1/platforms/": "srl.platforms",
                "/api/v1/variables/": "srl.variables",
            }

            app_label, model_name = None, None
            for path_prefix, model_path in model_mappings.items():
                if path.startswith(path_prefix):
                    app_label, model_name = model_path.split(".")
                    break

            if not app_label or not model_name:
                return None

            try:
                content_type = ContentType.objects.get(
                    app_label=app_label, model=model_name
                )
            except ContentType.DoesNotExist:
                return None

            path_parts = [p for p in path.split("/") if p]

            if request.method == "POST":
                object_id = None
                object_repr = f"New {model_name.title()}"
            else:
                if len(path_parts) >= 4:
                    potential_id = path_parts[3]
                    object_id = potential_id
                    object_repr = f"{model_name.title()} {potential_id}"
                else:
                    object_id = None
                    object_repr = f"{model_name.title()} (bulk operation)"

            return content_type, object_id, object_repr

        except Exception as e:
            logger.warning(
                f"Failed to extract object info from request: {e}",
                exc_info=True,
                extra={"path": request.path},
            )
            return None

    def create_change_message(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> str:
        """Create a descriptive change message for the log entry."""
        try:
            method = request.method

            api_key_name = "Unknown"
            api_key_header = request.headers.get("X-API-Key")
            if api_key_header:
                try:
                    api_key_obj = RoleAPIKey.objects.get_from_key(api_key_header)
                    if api_key_obj:
                        api_key_name = api_key_obj.name
                except Exception as e:
                    logger.warning(
                        f"Failed to retrieve API key name: {e}", exc_info=True
                    )

            messages: dict[str, str] = {
                "POST": f"Created via API (Key: {api_key_name})",
                "PUT": f"Updated via API (Key: {api_key_name})",
                "PATCH": f"Partially updated via API (Key: {api_key_name})",
                "DELETE": f"Deleted via API (Key: {api_key_name})",
            }

            base_message = messages.get(
                method or "", f"{method} via API (Key: {api_key_name})"
            )

            if hasattr(request, "body") and request.body:
                try:
                    if len(request.body) > MAX_LOG_BODY_SIZE:
                        base_message += " | Data: [Request body too large for logging]"
                    else:
                        body = request.body.decode("utf-8")
                        if len(body) < 500:
                            data = json.loads(body)
                            safe_data = {}
                            for key, value in data.items():
                                if key.lower() not in [
                                    "password",
                                    "secret",
                                    "token",
                                    "key",
                                ]:
                                    safe_data[key] = value

                            if safe_data:
                                base_message += f" | Data: {json.dumps(safe_data)}"
                except Exception as e:
                    logger.warning(
                        f"Failed to parse/sanitize request body for logging: {e}",
                        exc_info=True,
                    )

            return base_message[:255]
        except Exception as e:
            logger.warning(
                f"Failed to create change message: {e}",
                exc_info=True,
                extra={"method": request.method},
            )
            return f"API {request.method} operation"
