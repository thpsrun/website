from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response schema for the API.

    This provides a much better error handler for the API to return to the client since this
    standardizes the response format.

    Attributes:
        error (str): The error message sent to the client.
        details (Optional[dict[str, Any]]): Used to provide additional details related to the error.
        code (int): The HTTP status code - https://en.wikipedia.org/wiki/List_of_HTTP_status_codes.
    """

    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    code: int = Field(..., description="HTTP status code")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema for the API.

    This is used when the requested data fails any sort of validation. This should also provide some
    verbose information for the client to understand what caused the error.

    Attributes:
        error (str): The error message sent to the client.
        validation_errors (dict[str, List[str]]): Any field-specific validation errors.
        code (int): The HTTP status code - https://en.wikipedia.org/wiki/List_of_HTTP_status_codes.
    """

    error: str = Field(default="Validation failed")
    validation_errors: Dict[str, List[str]] = Field(
        ..., description="Field validation errors"
    )
    code: int = Field(default=422)


class PaginatedResponse(BaseModel):
    """Standardized pagination response schema for the API.

    This provides a consistent pagination structure for all endpoints that support it.

    Attributes:
        count (int): Total number of items begin returned to the client.
        next (Optional[str]): The URL for the next page (will return null if none after).
        previous (Optional[str]): The URL for previous page (will return null if first page).
        results (List[Dict[str, Any]]): The actual data being returned.
    """

    count: int = Field(..., description="Total number of items")
    next: Optional[str] = Field(default=None, description="URL for next page")
    previous: Optional[str] = Field(default=None, description="URL for previous page")
    results: List[Dict[str, Any]] = Field(..., description="Page data")


class BaseEmbedSchema(BaseModel):
    """Based schema for handling embeds within the API.

    This API utilizes an embed system to add additional context and information to what is being
    queried by the user.
    """

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        exclude_none = False


class TimestampMixin(BaseModel):
    """Pydantic mixin for models that have different timestamp fields.

    `Guides` and any other new models may have different timestamps that need to be returned to the
    client. This helps standardize it and ensures the ISO format is properly formatted.

    Attributes:
        created_at (Optional[datetime]): When the object was originally created.
        updated_at (Optional[datetime]): When the object was last updated by anybody.
    """

    created_at: Optional[datetime] = Field(default=None, description="Created")
    updated_at: Optional[datetime] = Field(default=None, description="Last Updated")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class SlugMixin(BaseModel):
    """Pydantic mixing for models that have generated slugs.

    This mainly helps to provide consistent slug handling.

    Attributes:
        name (str): The human-readable name of an object (to include symbols).
        slug (str): The URL-friendly name of the object (removing all symbols but dashes).
    """

    name: str = Field(..., description="Human-readable name")
    slug: str = Field(..., description="URL-friendly slug")


VALID_EMBEDS: Dict[str, Set[str]] = {
    "games": {"categories", "levels", "platforms"},
    "categories": {"game", "variables", "values"},
    "levels": {"game", "variables", "values"},
    "variables": {"game", "category", "level", "values"},
    "players": {"country", "awards", "runs"},
    "runs": {"game", "category", "level", "players", "variables"},
    "guides": {"game", "tags"},
    "tags": set(),
}


def validate_embeds(
    endpoint: str,
    embeds: List[str],
) -> List[str]:
    """Validation to ensure the requested embeds from the client are allowed on the endpoint.

    This is a consolidated validation function to help with ensuring that endpoints can only accept
    the embeds of which they are assigned. If an endpoint doesn't have that embed, it will return
    that as a list to a raise an error to the client.

    Args:
        endpoint (str): API endpoint name.
        embeds (List[str]): List of requested embed fields.

    Returns:
        List of invalid embeds; empty if all valid.
    """
    valid_for_endpoint: Set[str] = VALID_EMBEDS.get(endpoint, set())
    return [embed for embed in embeds if embed not in valid_for_endpoint]
