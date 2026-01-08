from typing import List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Games, Levels, Variables, VariableValues

from api.auth.api_key import api_admin_check, api_moderator_check, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.levels import LevelCreateSchema, LevelSchema, LevelUpdateSchema

router = Router()

# START OPENAPI DOCUMENTATION #
LEVELS_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "592pxj8d",
                        "name": "Alcatraz",
                        "slug": "alcatraz",
                        "url": "https://speedrun.com/thps34/individual_levels#Alcatraz",
                        "rules": "",
                        "game": {
                            "id": "n2680o1p",
                            "name": "Tony Hawk's Pro Skater 3+4",
                            "slug": "thps34",
                            "release": "2002-10-23",
                            "boxart": "https://example.com/boxart.jpg",
                            "twitch": "Tony Hawk's Pro Skater 3+4",
                            "defaulttime": "realtime",
                            "idefaulttime": "realtime",
                            "pointsmax": 1000,
                            "ipointsmax": 100,
                        },
                        "variables": [
                            {
                                "id": "5lygdn8q",
                                "name": "Platform",
                                "slug": "platform",
                                "scope": "single-level",
                                "all_cats": False,
                                "hidden": False,
                                "values": [
                                    {
                                        "value": "pc",
                                        "name": "PC",
                                        "slug": "pc",
                                        "hidden": False,
                                        "rules": "",
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Level could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "592pxj8d",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Level ID",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "game,variables,values",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: game, variables, values",
        },
    ],
}

LEVELS_POST = {
    "responses": {
        201: {
            "description": "Level created successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "592pxj8d",
                        "name": "Alcatraz",
                        "slug": "alcatraz",
                        "url": "https://speedrun.com/thps34/individual_levels#Alcatraz",
                        "rules": "Rulez.",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or game does not exist."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["name", "game_id"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "Alcatraz",
                            "description": "LEVEL NAME",
                        },
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "GAME ID THIS LEVEL BELONGS TO",
                        },
                        "rules": {
                            "type": "string",
                            "example": "Rulez.",
                            "description": "LEVEL RULES",
                        },
                    },
                },
                "example": {
                    "name": "Alcatraz",
                    "game_id": "n2680o1p",
                    "rules": "Rulez.",
                },
            }
        },
    },
}

LEVELS_PUT = {
    "responses": {
        200: {
            "description": "Level updated successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "592pxj8d",
                        "name": "Alcatraz",
                        "slug": "alcatraz",
                        "url": "https://speedrun.com/thps4/individual_levels#Alcatraz",
                        "rules": "Rulez.",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or game does not exist."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Level does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "592pxj8d",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Level ID to update",
        },
    ],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "Alcatraz",
                            "description": "UPDATED LEVEL NAME",
                        },
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "UPDATED GAME ID",
                        },
                        "rules": {
                            "type": "string",
                            "example": "Rulez.",
                            "description": "UPDATED LEVEL RULES",
                        },
                    },
                },
                "example": {
                    "name": "Alcatraz Updated",
                    "rules": "Rulez.",
                },
            }
        },
    },
}

LEVELS_DELETE = {
    "responses": {
        200: {
            "description": "Level deleted successfully!",
            "content": {
                "application/json": {
                    "example": {"message": "Level 'Alcatraz' deleted successfully"}
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Level does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "592pxj8d",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Level ID to delete",
        },
    ],
}

LEVELS_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "592pxj8d",
                            "name": "Alcatraz",
                            "slug": "alcatraz",
                            "url": "https://speedrun.com/thps34/individual_levels#Alcatraz",
                            "rules": "Rulez.",
                        },
                        {
                            "id": "29vjx18k",
                            "name": "Kona",
                            "slug": "kona",
                            "url": "https://speedrun.com/thps34/individual_levels#Kona",
                            "rules": "Rulez.",
                        },
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "game_id",
            "in": "query",
            "example": "thps4",
            "schema": {"type": "string"},
            "description": "Filter by game ID",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "game,variables",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds",
        },
        {
            "name": "limit",
            "in": "query",
            "example": 50,
            "schema": {"type": "integer", "minimum": 1, "maximum": 100},
            "description": "Results per page (default 50, max 100)",
        },
        {
            "name": "offset",
            "in": "query",
            "example": 0,
            "schema": {"type": "integer", "minimum": 0},
            "description": "Results to skip (default 0)",
        },
    ],
}
# END OPENAPI DOCUMENTATION #


def apply_level_embeds(
    level: Levels,
    embed_fields: List[str],
) -> dict:
    """When requested in the `embed_fields` of a level instance, this will apply the embeds."""
    embeds = {}

    if "game" in embed_fields:
        if level.game:
            embeds["game"] = {
                "id": level.game.id,
                "name": level.game.name,
                "slug": level.game.slug,
                "release": level.game.release.isoformat(),
                "boxart": level.game.boxart,
                "twitch": level.game.twitch,
                "defaulttime": level.game.defaulttime,
                "idefaulttime": level.game.idefaulttime,
                "pointsmax": level.game.pointsmax,
                "ipointsmax": level.game.ipointsmax,
            }

    if "variables" in embed_fields or "values" in embed_fields:
        variables = Variables.objects.filter(
            game=level.game, level=level, scope="single-level"
        ).order_by("name")

        all_level_vars = Variables.objects.filter(
            game=level.game, scope="all-levels"
        ).order_by("name")

        all_variables = list(variables) + list(all_level_vars)

        variables_data = []
        for var in all_variables:
            var_data = {
                "id": var.id,
                "name": var.name,
                "slug": var.slug,
                "scope": var.scope,
                "hidden": var.archive,
            }

            if "values" in embed_fields:
                values = VariableValues.objects.filter(var=var).order_by("name")
                var_data["values"] = [
                    {
                        "value": val.value,
                        "name": val.name,
                        "slug": val.slug,
                        "hidden": val.archive,
                        "rules": val.rules,
                    }
                    for val in values
                ]

            variables_data.append(var_data)

        embed_key = "values" if "values" in embed_fields else "variables"
        embeds[embed_key] = variables_data

    return embeds


@router.get(
    "/{id}",
    response=Union[LevelSchema, ErrorResponse],
    summary="Get Level by ID",
    description="""
    Retrieve a single level based upon its ID, including optional embedding.

    **Supported Embeds:**
    - `game`: Includes the metadata of the game the level belongs to
    - `variables`: Include metadata of the variables belonging to this level
    - `values`: Include all metadata for each variable and its values

    **Examples:**
    - `/levels/592pxj8d` - Get level by ID
    - `/levels/592pxj8d?embed=game` - Get level with game info
    - `/levels/592pxj8d?embed=variables,values` - Get level with variables and values
    """,
    auth=read_only_auth,
    openapi_extra=LEVELS_GET,
)
def get_level(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
) -> Union[LevelSchema, ErrorResponse]:
    if len(id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("levels", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={"valid_embeds": ["game", "variables", "values"]},
                code=400,
            )

    try:
        level = Levels.objects.filter(id__iexact=id).first()
        if not level:
            return ErrorResponse(
                error="Level ID does not exist",
                details=None,
                code=404,
            )

        level_data = LevelSchema.model_validate(level)

        if embed_fields:
            embed_data = apply_level_embeds(level, embed_fields)
            for field, data in embed_data.items():
                setattr(level_data, field, data)

        return level_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve level", details={"exception": str(e)}, code=500
        )


@router.get(
    "/all",
    response=Union[List[LevelSchema], ErrorResponse],
    summary="Get All Levels",
    description="""
    Retrieves all levels within a `Games` object, including optional embedding.

    **Supported Embeds:**
    - `game`: Includes the metadata of the game the level belongs to
    - `variables`: Include metadata of the variables belonging to this level
    - `values`: Include all metadata for each variable and its values

    **Supported Parameters:**
    - `game_id`: Filter by specific game ID or its slug
    - `embed`: Comma-separated list of resources to embed
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Examples:**
    - `/levels/all` - Get all levels
    - `/levels/all?game_id=thps4` - Get all levels for THPS4
    - `/levels/all?game_id=thps4&embed=game` - Get THPS4 levels with game info
    - `/levels/all?limit=10&offset=20` - Get levels 21-30
    """,
    auth=read_only_auth,
    openapi_extra=LEVELS_ALL,
)
def get_all_levels(
    request: HttpRequest,
    game_id: Optional[str] = Query(
        None,
        description="Filter by game ID",
    ),
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of returned objects (default 50, less than 100)",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset from 0",
    ),
) -> Union[List[LevelSchema], ErrorResponse]:
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("levels", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
                code=400,
            )

    try:
        queryset = Levels.objects.all().order_by("name")

        if game_id:
            queryset = queryset.filter(game__id=game_id)

        levels = queryset[offset : offset + limit]

        level_schemas = []
        for level in levels:
            level_data = LevelSchema.model_validate(level)

            if embed_fields:
                embed_data = apply_level_embeds(level, embed_fields)
                for field, data in embed_data.items():
                    setattr(level_data, field, data)

            level_schemas.append(level_data)

        return level_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve levels", details={"exception": str(e)}, code=500
        )


@router.post(
    "/",
    response=Union[LevelSchema, ErrorResponse],
    summary="Create Level",
    description="""
    Creates a brand new level.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=LEVELS_POST,
)
def create_level(
    request: HttpRequest,
    level_data: LevelCreateSchema,
) -> Union[LevelSchema, ErrorResponse]:
    try:
        game = Games.objects.filter(id=level_data.game_id).first()
        if not game:
            return ErrorResponse(
                error="Game does not exist",
                details=None,
                code=404,
            )

        level = Levels.objects.create(
            game=game,
            **{k: v for k, v in level_data.model_dump().items() if k != "game_id"},
        )

        return LevelSchema.model_validate(level)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create level",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{id}",
    response=Union[LevelSchema, ErrorResponse],
    summary="Update Level",
    description="""
    Updates the level based on its unique ID.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=LEVELS_PUT,
)
def update_level(
    request: HttpRequest,
    id: str,
    level_data: LevelUpdateSchema,
) -> Union[LevelSchema, ErrorResponse]:
    try:
        level = Levels.objects.filter(id__iexact=id).first()
        if not level:
            return ErrorResponse(
                error="Level does not exist",
                details=None,
                code=404,
            )

        update_data = level_data.model_dump(exclude_unset=True)
        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(
                    error="Game does not exist",
                    details=None,
                    code=404,
                )
            level.game = game
            del update_data["game_id"]

        for field, value in update_data.items():
            setattr(level, field, value)

        level.save()
        return LevelSchema.model_validate(level)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update level",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Level",
    description="""
    Deletes the selected level by its ID.

    **REQUIRES ADMIN ACCESS.**
    """,
    auth=api_admin_check,
    openapi_extra=LEVELS_DELETE,
)
def delete_level(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        level = Levels.objects.filter(id__iexact=id).first()
        if not level:
            return ErrorResponse(
                error="Level does not exist",
                details=None,
                code=404,
            )

        name = level.name
        level.delete()
        return {"message": f"Level '{name}' deleted successfully"}
    except Exception as e:
        return ErrorResponse(
            error="Failed to delete level",
            details={"exception": str(e)},
            code=500,
        )
