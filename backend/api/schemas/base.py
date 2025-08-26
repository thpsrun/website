"""
Base Schemas for Django Ninja API

This module contains base Pydantic schemas that are used across multiple endpoints.
These schemas replace Django REST Framework serializers and provide:
- Automatic validation
- Type hints and IDE support
- Automatic OpenAPI/Swagger documentation
- Better performance than DRF serializers

Key Concepts:
- BaseModel: Pydantic's base class for all schemas
- Field: Used for field validation and documentation
- Union/Optional: For conditional/optional fields
- create_model: Dynamic model creation for embeds

Schema Types:
- Response schemas: Define API response structure
- Request schemas: Define expected input data
- Embed schemas: Handle conditional nested data
- Error schemas: Standardize error responses
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Standard error response schema.

    This replaces the inconsistent error handling from DRF
    and provides a standardized error response format.

    Attributes:
        error: The error message
        details: Optional additional error details
        code: HTTP status code (for reference)

    Example Response:
        {
            "error": "Game ID or slug does not exist",
            "details": null,
            "code": 404
        }
    """

    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    code: int = Field(..., description="HTTP status code")


class ValidationErrorResponse(BaseModel):
    """
    Validation error response schema.

    Used when request data fails validation.
    Provides detailed field-level error information.

    Attributes:
        error: General error message
        validation_errors: Field-specific validation errors
        code: HTTP status code
    """

    error: str = Field(default="Validation failed")
    validation_errors: Dict[str, List[str]] = Field(
        ..., description="Field validation errors"
    )
    code: int = Field(default=422)


class PaginatedResponse(BaseModel):
    """
    Base pagination response schema.

    Provides consistent pagination structure across all paginated endpoints.
    This is an improvement over DRF's pagination which varied by serializer.

    Attributes:
        count: Total number of items
        next: URL for next page (null if last page)
        previous: URL for previous page (null if first page)
        results: The actual data array
    """

    count: int = Field(..., description="Total number of items")
    next: Optional[str] = Field(None, description="URL for next page")
    previous: Optional[str] = Field(None, description="URL for previous page")
    results: List[Dict[str, Any]] = Field(..., description="Page data")


class BaseEmbedSchema(BaseModel):
    """
    Base schema for handling embeds.

    Django Ninja improvement: Instead of conditionally including/excluding fields
    in serializers like DRF, we use Union types to handle optional embedded data.
    This provides better type safety and clearer API documentation.

    The embed system works by:
    1. Checking query parameters for requested embeds
    2. Using Union types to return either the embedded data or None
    3. Automatic validation ensures only valid embeds are requested

    Example:
        # Without embed: categories = None
        # With embed: categories = [CategorySchema(...), ...]
        categories: Optional[List['CategorySchema']] = None
    """

    class Config:
        # Allow Django ORM models to be converted to Pydantic schemas
        from_attributes = True
        # Allow forward references for circular imports
        arbitrary_types_allowed = True
        # Include None values in JSON output (important for embeds)
        exclude_none = False


class TimestampMixin(BaseModel):
    """
    Mixin for models that have timestamp fields.

    Provides consistent timestamp handling across schemas.
    Uses ISO format for API responses which is better than
    DRF's default timestamp handling.

    Attributes:
        created_at: When the record was created
        updated_at: When the record was last updated
    """

    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        # Ensure datetime fields are serialized in ISO format
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class SlugMixin(BaseModel):
    """
    Mixin for models that have automatically generated slugs.

    Many of the SRL models auto-generate slugs from names.
    This mixin provides consistent slug handling.

    Attributes:
        slug: URL-friendly version of the name
        name: Human-readable name
    """

    name: str = Field(..., description="Human-readable name")
    slug: str = Field(..., description="URL-friendly slug")


# Embed validation utilities
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


def validate_embeds(endpoint: str, requested_embeds: List[str]) -> List[str]:
    """
    Validate that requested embeds are allowed for the endpoint.

    This provides better error messages than the DRF implementation
    and centralizes embed validation logic.

    Args:
        endpoint: The API endpoint name (e.g., "games", "categories")
        requested_embeds: List of requested embed fields

    Returns:
        List of invalid embeds (empty if all valid)

    Example:
        invalid = validate_embeds("games", ["categories", "invalid"])
        # Returns: ["invalid"]
    """
    valid_for_endpoint: Set[str] = VALID_EMBEDS.get(endpoint, set())
    return [embed for embed in requested_embeds if embed not in valid_for_endpoint]
