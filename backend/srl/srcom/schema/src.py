from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Not everything is defined for these Pydantic models, just pretty much anything
# that is needed for the project.


# PLATFORM SCHEMA #
class SrcPlatformModel(BaseModel):
    """Base model for SRC Platforms."""

    id: str
    name: str


# GAMES SCHEMA #
class SrcGamesNames(BaseModel):
    """Embedded model to show a game's name and Twitch name."""

    international: str
    twitch: Optional[str] = None


class SrcGamesRuleset(BaseModel):
    """Embedded model to show a game's default timing method."""

    model_config = ConfigDict(populate_by_name=True)
    defaulttime: str = Field(..., alias="default-time")


class SrcGamesBoxArtUri(BaseModel):
    """Embedded model to show a game's boxart."""

    uri: str


class SrcGamesAssets(BaseModel):
    """Embedded model to show a game's aseets."""

    model_config = ConfigDict(populate_by_name=True)
    cover_large: SrcGamesBoxArtUri = Field(..., alias="cover-large")


class SrcGamesModel(BaseModel):
    """Base model for SRC Games."""

    model_config = ConfigDict(populate_by_name=True)
    id: str
    abbreviation: str
    names: SrcGamesNames
    release_date: str = Field(..., alias="release-date")
    ruleset: SrcGamesRuleset
    platforms: List[SrcPlatformModel]
    assets: SrcGamesAssets


# CATEGORIES/LEVEL SCHEMA #
class SrcCategoriesLevelsScope(BaseModel):
    """Embedded model to show a category or level's scope type."""

    type: str


class SrcCategoriesLevelsLinks(BaseModel):
    """Embedded model to show the link structure within a category or level data."""

    rel: str
    uri: str


class SrcCategoriesModel(BaseModel):
    """Base model for SRC Categories."""

    model_config = ConfigDict(populate_by_name=True)
    id: str
    name: str
    type: str
    scope: SrcCategoriesLevelsScope
    weblink: str
    rules: Optional[str] = None
    game: SrcGamesModel

    @field_validator("game", mode="before")
    @classmethod
    def unwrap_game(cls, v):
        if v is None:
            return []
        elif isinstance(v, dict) and "data" in v:
            return v["data"]
        return v


class SrcLevelsModel(BaseModel):
    """Base model for SRC Levels."""

    id: str
    name: str
    weblink: str
    rules: Optional[str] = None
    links: List[SrcCategoriesLevelsLinks]

    @property
    def game(self) -> Optional[str]:
        for link in self.links:
            if link.rel == "game":
                return link.uri.rstrip("/").split("/")[-1]


# VARIABLE VALUES SCHEMA #
class SrcVariableValuesValue(BaseModel):
    """Embedded model to show a VariableValue's information."""

    label: str
    rules: Optional[str] = None


class SrcVariableValuesModel(BaseModel):
    """Base model for SRC Values within a Variable."""

    values: Dict[str, SrcVariableValuesValue]
    default: Optional[str] = None


# VARIABLES SCHEMA #
class SrcVariableScope(BaseModel):
    """Embedded model for scope type of an SRC Variable."""

    type: str
    level: Optional[str] = None


class SrcVariablesModel(BaseModel):
    """Base model for SRC Variables with embedded Values."""

    model_config = ConfigDict(populate_by_name=True)
    id: str
    name: str
    category: Optional[str] = None
    scope: SrcVariableScope
    mandatory: bool = False
    obsoletes: bool = False
    is_subcategory: bool = Field(default=False, alias="is-subcategory")
    values: SrcVariableValuesModel
    links: List[SrcCategoriesLevelsLinks]

    @property
    def game(self) -> Optional[str]:
        for link in self.links:
            if link.rel == "game":
                return link.uri.rstrip("/").split("/")[-1]


# RUNS SCHEMA #
class SrcRunsLinks(BaseModel):
    links: Optional[List[str]]


class SrcRunsSystem(BaseModel):
    """Embedded model for system information for an SRC Run."""

    platform: str
    emulated: bool
    region: Optional[str]


class SrcRunsStatus(BaseModel):
    """Embedded model for status information for an SRC Run."""

    model_config = ConfigDict(populate_by_name=True)
    status: str
    examiner: str
    verify_date: Optional[datetime] = Field(default=None, alias="verify-date")


class SrcRunsPlayers(BaseModel):
    """Embedded model for player information for an SRC Run."""

    rel: str
    id: Optional[str]
    uri: Optional[str]


class SrcRunsTimes(BaseModel):
    """Embedded model for timing information for an SRC Run."""

    primary_t: float = 0
    realtime_t: float = 0
    realtime_noloads_t: float = 0
    ingame_t: float = 0


class SrcRunsModel(BaseModel):
    """Base Model for SRC Runs with embedded Values."""

    id: str
    weblink: str
    game: str
    level: Optional[str]
    category: Optional[str]
    videos: List[SrcRunsLinks]
    comment: Optional[str]
    status: SrcRunsStatus
    players: List[SrcRunsPlayers]
    date: Optional[datetime]
    submitted: Optional[datetime]
    times: SrcRunsTimes
    system: SrcRunsSystem
    values: Dict[str, str]


# PLAYERS SCHEMA #
class SrcPlayersNames(BaseModel):
    international: str
    japanese: Optional[str]


class SrcPlayersModel(BaseModel):
    """Base Model for SRC Players with embedded Values."""

    id: str
    names: SrcPlayersNames
    pronouns: Optional[str] = None
    weblink: str
    location: Optional[dict] = None
    twitch: Optional[dict] = None
    youtube: Optional[dict] = None
    assets: Optional[dict] = None

    @property
    def country_code(self) -> Optional[str]:
        if self.location and self.location.get("country"):
            return self.location["country"].get("code")
        return None

    @property
    def country_name(self) -> Optional[str]:
        if self.location and self.location.get("country"):
            names = self.location["country"].get("names")
            if names:
                return names.get("international")
        return None

    @property
    def twitch_url(self) -> Optional[str]:
        if self.twitch:
            return self.twitch.get("uri")
        return None

    @property
    def youtube_url(self) -> Optional[str]:
        if self.youtube:
            return self.youtube.get("uri")
        return None

    @property
    def pfp(self) -> Optional[str]:
        if self.assets and self.assets.get("image"):
            return self.assets["image"].get("uri")
        return None
