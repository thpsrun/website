from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional, Tuple

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.encoding import force_str

from .models import RoleAPIKey


class APIActivityLogMiddleware:
    """
    Middleware to log API activities to Django admin Recent Actions.
    
    This captures API calls that modify data (POST, PUT, PATCH, DELETE) and 
    creates LogEntry records so they appear in the Django admin's Recent Actions section.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        
        # Only log for API endpoints that modify data
        if (request.path.startswith('/api/v1/') and 
            request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and
            response.status_code < 400):  # Only log successful requests
            
            self.log_api_activity(request, response)
        
        return response
    
    def log_api_activity(self, request: HttpRequest, response: HttpResponse) -> None:
        """Log API activity to Django admin."""
        try:
            # Get the API key user info
            user_id = self.get_api_user_id(request)
            if not user_id:
                return
            
            # Determine action type
            action_flag = self.get_action_flag(request.method)
            if not action_flag:
                return
            
            # Extract object info from URL
            object_info = self.extract_object_info(request)
            if not object_info:
                return
            
            content_type, object_id, object_repr = object_info
            
            # Create change message
            change_message = self.create_change_message(request, response)
            
            # Create log entry
            LogEntry.objects.create(
                user_id=user_id,
                content_type=content_type,
                object_id=object_id,
                object_repr=object_repr,
                action_flag=action_flag,
                change_message=change_message,
                action_time=timezone.now()
            )
            
        except Exception as e:
            # Don't break API calls if logging fails
            pass
    
    def get_api_user_id(self, request: HttpRequest) -> Optional[int]:
        """
        Get user ID from API key or create/get an API user.
        
        Since API calls don't have traditional Django users, we'll create
        a special user account for API activities.
        """
        try:
            # Check if we have API key auth info
            api_key_header = request.headers.get('X-API-Key')
            if not api_key_header:
                return None
            
            # Get the API key object
            api_key_obj = RoleAPIKey.objects.get_from_key(api_key_header)
            if not api_key_obj:
                return None
            
            # Get or create a user for this API key
            username = f"api_key_{api_key_obj.name}".replace(' ', '_').replace('-', '_')[:150]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': 'API Key',
                    'last_name': api_key_obj.name,
                    'email': f'{username}@api.thpsrun.local',
                    'is_active': False,  # Not a real login user
                    'is_staff': False,
                }
            )
            
            return user.id
            
        except Exception:
            return None
    
    def get_action_flag(self, method: str) -> Optional[int]:
        """Convert HTTP method to Django admin action flag."""
        method_mapping = {
            'POST': ADDITION,
            'PUT': CHANGE,
            'PATCH': CHANGE,
            'DELETE': DELETION,
        }
        return method_mapping.get(method)
    
    def extract_object_info(self, request: HttpRequest) -> Optional[Tuple[ContentType, Optional[str], str]]:
        """
        Extract object information from the API request.
        
        Returns tuple of (ContentType, object_id, object_repr) or None.
        """
        try:
            path = request.path
            
            # Map API paths to Django models
            model_mappings = {
                '/api/v1/games/': 'srl.games',
                '/api/v1/categories/': 'srl.categories', 
                '/api/v1/levels/': 'srl.levels',
                '/api/v1/players/': 'srl.players',
                '/api/v1/runs/': 'srl.runs',
                '/api/v1/platforms/': 'srl.platforms',
                '/api/v1/variables/': 'srl.variables',
            }
            
            # Find matching model
            app_label, model_name = None, None
            for path_prefix, model_path in model_mappings.items():
                if path.startswith(path_prefix):
                    app_label, model_name = model_path.split('.')
                    break
            
            if not app_label or not model_name:
                return None
            
            # Get ContentType
            try:
                content_type = ContentType.objects.get(
                    app_label=app_label,
                    model=model_name
                )
            except ContentType.DoesNotExist:
                return None
            
            # Extract object ID from URL (for single object operations)
            path_parts = [p for p in path.split('/') if p]
            
            if request.method == 'POST':
                # For POST, we don't have an ID yet, use generic representation
                object_id = None
                object_repr = f"New {model_name.title()}"
            else:
                # For PUT/PATCH/DELETE, try to get ID from URL
                if len(path_parts) >= 4:  # /api/v1/games/some_id
                    potential_id = path_parts[3]
                    object_id = potential_id
                    object_repr = f"{model_name.title()} {potential_id}"
                else:
                    object_id = None
                    object_repr = f"{model_name.title()} (bulk operation)"
            
            return content_type, object_id, object_repr
            
        except Exception:
            return None
    
    def create_change_message(self, request: HttpRequest, response: HttpResponse) -> str:
        """Create a descriptive change message for the log entry."""
        try:
            method = request.method
            path = request.path
            
            # Get API key name for context
            api_key_name = "Unknown"
            api_key_header = request.headers.get('X-API-Key')
            if api_key_header:
                try:
                    api_key_obj = RoleAPIKey.objects.get_from_key(api_key_header)
                    if api_key_obj:
                        api_key_name = api_key_obj.name
                except:
                    pass
            
            # Create base message
            messages = {
                'POST': f'Created via API (Key: {api_key_name})',
                'PUT': f'Updated via API (Key: {api_key_name})', 
                'PATCH': f'Partially updated via API (Key: {api_key_name})',
                'DELETE': f'Deleted via API (Key: {api_key_name})',
            }
            
            base_message = messages.get(method, f'{method} via API (Key: {api_key_name})')
            
            # Add request data for context (but limit size)
            if hasattr(request, 'body') and request.body:
                try:
                    body = request.body.decode('utf-8')
                    if len(body) < 500:  # Only include small request bodies
                        data = json.loads(body)
                        # Only include safe fields
                        safe_data = {}
                        for key, value in data.items():
                            if key.lower() not in ['password', 'secret', 'token', 'key']:
                                safe_data[key] = value
                        
                        if safe_data:
                            base_message += f" | Data: {json.dumps(safe_data)}"
                except:
                    pass
            
            return base_message[:255]  # Django LogEntry.change_message max length
            
        except Exception:
            return f"API {request.method} operation"