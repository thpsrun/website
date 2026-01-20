from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from pydantic import BaseModel, Field, field_serializer


# Literal types for model choices - these match the Django model choices exactly
RunTypeType = Literal["main", "il"]
RunStatusType = Literal["verified", "new", "rejected"]
CategoryTypeType = Literal["per-level", "per-game"]
VariableScopeType = Literal["global", "full-game", "all-levels", "single-level"]
LeaderboardTimeType = Literal["realtime", "realtime_noloads", "ingame"]


class ErrorResponse(BaseModel):
    """Standardized error response schema for the API.

    Provides consistent error response format for all API endpoints.

    Attributes:
        error (str): Error message sent to the client.
        details (Optional[Dict[str, Any]]): Additional details related to the error.
    """

    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response schema for the API.

    Used when requested data fails validation with field-specific error details.

    Attributes:
        error (str): Error message sent to the client.
        validation_errors (Dict[str, List[str]]): Field-specific validation errors.
    """

    error: str = Field(default="Validation failed")
    validation_errors: Dict[str, List[str]] = Field(
        ..., description="Field validation errors"
    )


class PaginatedResponse(BaseModel):
    """Standardized pagination response schema for the API.

    Attributes:
        count (int): Total number of items being returned.
        next (Optional[str]): URL for the next page.
        previous (Optional[str]): URL for previous page.
        results (List[Dict[str, Any]]): Actual data being returned.
    """

    count: int = Field(..., description="Total number of items")
    next: Optional[str] = Field(default=None, description="URL for next page")
    previous: Optional[str] = Field(default=None, description="URL for previous page")
    results: List[Dict[str, Any]] = Field(..., description="Page data")


class BaseEmbedSchema(BaseModel):
    """Base schema for handling embeds within the API.

    Provides embed system to include related data in API responses.
    """

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        exclude_none = False


class TimestampMixin(BaseModel):
    """Pydantic mixin for models with timestamp fields.

    Standardizes timestamp handling and ensures ISO format serialization.

    Attributes:
        created_at (Optional[datetime]): When the object was created.
        updated_at (Optional[datetime]): When the object was last updated.
    """

    created_at: Optional[datetime] = Field(default=None, description="Created")
    updated_at: Optional[datetime] = Field(default=None, description="Last Updated")

    @field_serializer("created_at", "updated_at")
    @classmethod
    def serialize_datetime(cls, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format."""
        return value.isoformat() if value else None


class SlugMixin(BaseModel):
    """Pydantic mixin for models with generated slugs.

    Attributes:
        name (str): Human-readable name of an object.
        slug (str): URL-friendly name of the object.
    """

    name: str = Field(..., description="Human-readable name")
    slug: str = Field(..., description="URL-friendly slug")


VALID_EMBEDS: Dict[str, Set[str]] = {
    "games": {"categories", "levels", "platforms"},
    "categories": {"game", "variables", "values"},
    "levels": {"game", "variables", "values"},
    "variables": {"game", "category", "level", "values"},
    "players": {"country", "awards", "runs"},
    "runs": {"game", "category", "level", "variables"},
    "guides": {"game", "tags"},
    "tags": set(),
}


def validate_embeds(
    endpoint: str,
    embeds: List[str],
) -> List[str]:
    """Validation to ensure requested embeds are allowed on the endpoint.

    Args:
        endpoint (str): API endpoint name.
        embeds (List[str]): List of requested embed fields.

    Returns:
        List[str]: List of invalid embeds; empty if all valid.
    """
    valid_for_endpoint: Set[str] = VALID_EMBEDS.get(endpoint, set())
    return [embed for embed in embeds if embed not in valid_for_endpoint]
