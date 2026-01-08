from typing import Any, Dict

from django.db import models
from rest_framework_api_key.models import AbstractAPIKey


class RoleAPIKey(AbstractAPIKey):
    ROLE_CHOICES = [
        ("read_only", "Read Only"),
        ("contributor", "Contributor"),
        ("moderator", "Moderator"),
        ("admin", "Admin"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="read_only",
        help_text="Permission level for this API key",
    )

    description = models.TextField(
        blank=True, help_text="Optional description of what this key is used for"
    )

    created_by = models.CharField(
        max_length=100, blank=True, help_text="Who created this API key"
    )

    last_used = models.DateTimeField(
        null=True, blank=True, help_text="Last time this key was used"
    )

    class Meta:
        verbose_name = "Role API Key"
        verbose_name_plural = "Role API Keys"
        ordering = ["-created"]

    def __str__(self) -> str:
        return f"{self.name} ({self.role})"

    @property
    def role_display(self) -> str:
        """Get human-readable role name."""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    def has_role(self, required_role: str) -> bool:
        """
        Check if this API key has sufficient role permissions.

        Args:
            required_role: Minimum required role

        Returns:
            True if key has sufficient permissions
        """
        role_hierarchy: Dict[str, int] = {
            "read_only": 1,
            "contributor": 2,
            "moderator": 3,
            "admin": 4,
        }

        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to update last_used timestamp when needed."""
        super().save(*args, **kwargs)
