from typing import Optional

from pydantic import Field

from api.schemas.base import BaseEmbedSchema, SlugMixin


class PlatformSchema(SlugMixin, BaseEmbedSchema):
    """Base schema for `Platforms` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the platform.
        name (str): Platform name (e.g., "PlayStation 2").
        slug (str): URL-friendly version (e.g., "playstation-2").
    """

    id: str = Field(..., max_length=10, description="Speedrun.com platform ID")
    name: str = Field(..., max_length=30, description="Platform name")
    slug: str = Field(..., max_length=30, description="URL-friendly platform slug")


class PlatformCreateSchema(BaseEmbedSchema):
    """Schema for creating new platforms.

    Attributes:
        name (str): Platform name.
    """

    name: str = Field(..., description="Platform name")


class PlatformUpdateSchema(BaseEmbedSchema):
    """Schema for updating platforms.

    Attributes:
        name (Optional[str]): Updated platform name.
    """

    name: Optional[str] = Field(default=None, description="Updated platform name")
