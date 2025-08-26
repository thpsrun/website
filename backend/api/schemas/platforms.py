"""
Platform Schemas for Django Ninja API

Schemas for the Platforms model. Platforms represent gaming systems
that games can be played on (PC, PlayStation, Xbox, etc.).

This is a simple model with no complex relationships, making it
a good starting point for the Django Ninja conversion.

Key Features:
- Auto-generated slugs from platform names
- Simple validation and typing
- Used as embedded data in Games schema
"""

from typing import Optional

from pydantic import Field

from .base import BaseEmbedSchema, SlugMixin


class PlatformSchema(SlugMixin, BaseEmbedSchema):
    """
    Platform schema for API responses.

    Represents a gaming platform (PC, PS2, Xbox, etc.) that games
    can be played on. This is a straightforward schema with no embeds.

    Attributes:
        id: Speedrun.com platform ID
        name: Platform name (e.g., "PlayStation 2")
        slug: URL-friendly version (e.g., "playstation-2")

    Example Response:
        {
            "id": "8gej2n93",
            "name": "PlayStation 2",
            "slug": "playstation-2"
        }
    """

    id: str = Field(
        ..., max_length=10, description="Speedrun.com platform ID", example="8gej2n93"
    )
    name: str = Field(
        ..., max_length=30, description="Platform name", example="PlayStation 2"
    )
    slug: str = Field(
        ...,
        max_length=30,
        description="URL-friendly platform slug",
        example="playstation-2",
    )


class PlatformCreateSchema(BaseEmbedSchema):
    """
    Schema for creating new platforms.

    Used for POST /platforms endpoints.
    The slug will be auto-generated from the name.
    """

    name: str = Field(..., max_length=30)
    # Note: slug is auto-generated in the model's save() method


class PlatformUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating platforms.

    Used for PUT/PATCH /platforms/{id} endpoints.
    All fields optional for partial updates.
    """

    name: Optional[str] = Field(None, max_length=30)
