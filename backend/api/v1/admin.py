from __future__ import annotations

from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe
from rest_framework_api_key.models import APIKey

from api.v1.models import RoleAPIKey

admin.site.unregister(APIKey)


class RoleFilter(SimpleListFilter):
    """Filter API keys by role."""

    title = "Role"
    parameter_name = "role"

    def lookups(self, request, model_admin):  # type: ignore
        return RoleAPIKey.ROLE_CHOICES

    def queryset(self, request, queryset: QuerySet[RoleAPIKey]) -> QuerySet[RoleAPIKey]:
        if self.value():
            return queryset.filter(role=self.value())
        return queryset


class LastUsedFilter(SimpleListFilter):
    """Filter API keys by last used time."""

    title = "Last Used"
    parameter_name = "last_used"

    def lookups(self, request, model_admin):  # type: ignore
        return [
            ("today", "Today"),
            ("week", "This Week"),
            ("month", "This Month"),
            ("never", "Never Used"),
            ("old", "Over 30 Days"),
        ]

    def queryset(self, request, queryset: QuerySet[RoleAPIKey]) -> QuerySet[RoleAPIKey]:
        del request  # unused
        now = timezone.now()
        if self.value() == "today":
            return queryset.filter(last_used__date=now.date())
        elif self.value() == "week":
            return queryset.filter(last_used__gte=now - timedelta(days=7))
        elif self.value() == "month":
            return queryset.filter(last_used__gte=now - timedelta(days=30))
        elif self.value() == "never":
            return queryset.filter(last_used__isnull=True)
        elif self.value() == "old":
            return queryset.filter(last_used__lt=now - timedelta(days=30))
        return queryset


@admin.register(RoleAPIKey)
class RoleAPIKeyAdmin(admin.ModelAdmin):
    """Django admin interface for managing RoleAPIKey instances."""

    list_display = [
        "name",
        "role_badge",
        "created_by",
        "last_used_display",
        "created",
        "is_revoked",
        "expires_soon",
    ]

    list_filter = [
        RoleFilter,
        LastUsedFilter,
        "revoked",
        "created",
    ]

    search_fields = ["name", "created_by", "description"]

    readonly_fields = [
        "id",
        "prefix",
        "hashed_key",
        "created",
        "last_used",
        "api_key_preview",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "role", "description", "created_by")},
        ),
        (
            "Key Information",
            {
                "fields": ("api_key_preview", "prefix", "hashed_key"),
                "classes": ("collapse",),
            },
        ),
        (
            "Status & Timestamps",
            {
                "fields": ("revoked", "expiry_date", "created", "last_used"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["revoke_keys", "extend_expiry"]

    @admin.display(
        description="Role",
        ordering="role",
    )
    def role_badge(
        self,
        obj: RoleAPIKey,
    ) -> SafeString:
        """Display role as a colored badge."""
        colors: dict[str, str] = {
            "admin": "#dc3545",
            "moderator": "#fd7e14",
            "contributor": "#20c997",
            "read_only": "#6c757d",
        }
        color: str = colors.get(obj.role, "#6c757d")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display(),
        )

    @admin.display(
        description="Last Used",
        ordering="last_used",
    )
    def last_used_display(
        self,
        obj: RoleAPIKey,
    ) -> SafeString:
        """Display last used time with relative formatting."""
        if not obj.last_used:
            return mark_safe('<em style="color: #6c757d;">Never</em>')

        now = timezone.now()
        diff = now - obj.last_used

        if diff.days == 0:
            if diff.seconds < 3600:
                return format_html(
                    '<span style="color: #28a745;">{}m ago</span>', diff.seconds // 60
                )
            else:
                return format_html(
                    '<span style="color: #28a745;">{}h ago</span>', diff.seconds // 3600
                )
        elif diff.days < 7:
            return format_html(
                '<span style="color: #ffc107;">{}d ago</span>', diff.days
            )
        elif diff.days < 30:
            return format_html(
                '<span style="color: #fd7e14;">{}d ago</span>', diff.days
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">{}d ago</span>', diff.days
            )

    @admin.display(
        description="Expires",
        ordering="expiry_date",
    )
    def expires_soon(
        self,
        obj: RoleAPIKey,
    ) -> SafeString | str:
        """Show if key expires soon."""
        if not obj.expiry_date:
            return "-"

        now = timezone.now()
        if obj.expiry_date <= now:
            return mark_safe('<span style="color: #dc3545;">❌ Expired</span>')

        days_until_expiry: int = (obj.expiry_date - now).days
        if days_until_expiry <= 7:
            return format_html(
                '<span style="color: #dc3545;">⚠️ {}d</span>', days_until_expiry
            )
        elif days_until_expiry <= 30:
            return format_html(
                '<span style="color: #ffc107;">⚠️ {}d</span>', days_until_expiry
            )

        return format_html(
            '<span style="color: #28a745;">✅ {}d</span>', days_until_expiry
        )

    @admin.display(
        description="Revoked",
        ordering="revoked",
    )
    def is_revoked(
        self,
        obj: RoleAPIKey,
    ) -> SafeString:
        """Show revocation status with icon."""
        if obj.revoked:
            return mark_safe('<span style="color: #dc3545;">❌ Yes</span>')
        return mark_safe('<span style="color: #28a745;">✅ Active</span>')

    @admin.display(
        description="API Key (Masked)",
    )
    def api_key_preview(
        self,
        obj: RoleAPIKey,
    ) -> str:
        """Show masked API key for security."""
        if obj.prefix:
            return f"{obj.prefix}.{'*' * 20}..."
        return "Key will be generated on save"

    def save_model(
        self,
        request: HttpRequest,
        obj: RoleAPIKey,
        form: ModelForm,
        change: bool,
    ) -> None:
        """Override save to show the generated key to admin user."""
        if not change:
            api_key, key = RoleAPIKey.objects.create_key(
                name=obj.name,
                role=obj.role,
                description=obj.description,
                created_by=obj.created_by or request.user.username,
            )

            obj.pk = api_key.pk
            obj.id = api_key.id
            obj.prefix = api_key.prefix
            obj.hashed_key = api_key.hashed_key
            obj.created = api_key.created

            messages.success(
                request,
                format_html(
                    "<strong>API Key Created Successfully!</strong><br><br>"
                    "<strong>Name:</strong> {}<br>"
                    "<strong>Role:</strong> {}<br>"
                    '<strong>Key:</strong> <code style="background: #f8f9fa; padding: 4px 8px; '
                    'font-family: monospace; color: #e83e8c;">{}</code><br><br>'
                    "<strong>⚠️ IMPORTANT:</strong> Save this key now! This won't appear again!<br>"
                    "Use it in API requests with the <code>X-API-Key</code> header.",
                    api_key.name,
                    api_key.get_role_display(),
                    key,
                ),
            )

            return
        else:
            super().save_model(request, obj, form, change)

    @admin.action(
        description="Revoke selected API keys",
    )
    def revoke_keys(
        self,
        request: HttpRequest,
        queryset: QuerySet[RoleAPIKey],
    ) -> None:
        """Bulk action to revoke selected API keys."""
        count = queryset.update(revoked=True)
        self.message_user(
            request, f"Successfully revoked {count} API key(s).", messages.SUCCESS
        )

    @admin.action(
        description="Extend expiry by 90 days",
    )
    def extend_expiry(
        self,
        request: HttpRequest,
        queryset: QuerySet[RoleAPIKey],
    ) -> None:
        """Bulk action to extend expiry by 90 days."""
        now = timezone.now()
        new_expiry = now + timedelta(days=90)
        count = queryset.update(expiry_date=new_expiry)
        self.message_user(
            request,
            f"Extended expiry for {count} API key(s) to {new_expiry.date()}.",
            messages.SUCCESS,
        )

    def get_form(
        self,
        request,
        obj=None,
        **kwargs,
    ):
        """Customize the form for creating/editing API keys."""
        form = super().get_form(request, obj, **kwargs)

        if not obj and "created_by" in form.base_fields:
            form.base_fields["created_by"].initial = request.user.username

        return form

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """Limit who can change API keys."""
        return request.user.is_superuser or request.user.has_perm(
            "api.change_roleapikey"
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """Limit who can delete API keys."""
        return request.user.is_superuser or request.user.has_perm(
            "api.delete_roleapikey"
        )
