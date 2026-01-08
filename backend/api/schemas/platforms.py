from typing import Optional

from pydantic import Field

from .base import BaseEmbedSchema, SlugMixin


class PlatformSchema(SlugMixin, BaseEmbedSchema):
    """
    Platform schema for API responses.

    Represents a gaming platform (PC, PS2, Xbox, etc.) that games
    can be played on. This is a straightforward schema with no embeds.

    Attributes:
        id (str): Speedrun.com platform ID
        name (str): Platform name (e.g., "PlayStation 2")
        slug (str): URL-friendly version (e.g., "playstation-2")

    Example Response:
        {
            "id": "8gej2n93",
            "name": "PlayStation 2",
            "slug": "playstation-2"
        }
    """

    id: str = Field(..., max_length=10, description="Speedrun.com platform ID")
    name: str = Field(..., max_length=30, description="Platform name")
    slug: str = Field(..., max_length=30, description="URL-friendly platform slug")


class PlatformCreateSchema(BaseEmbedSchema):
    """
    Schema for creating new platforms.

    Used for POST /platforms endpoints.
    The slug will be auto-generated from the name.

    Attributes:
        name (str): Platform name
    """

    name: str = Field(..., description="Platform name")
    # Note: slug is auto-generated in the model's save() method


class PlatformUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating platforms.

    Used for PUT/PATCH /platforms/{id} endpoints.
    All fields optional for partial updates.

    Attributes:
        name (Optional[str]): Updated platform name
    """

    name: Optional[str] = Field(default=None, description="Updated platform name")
