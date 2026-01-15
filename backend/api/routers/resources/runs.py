from typing import List, Optional, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import (
    Categories,
    Games,
    Levels,
    Players,
    RunPlayers,
    Runs,
    RunVariableValues,
    Variables,
    VariableValues,
)

from api.docs.runs import RUNS_ALL, RUNS_DELETE, RUNS_GET, RUNS_POST, RUNS_PUT
from api.permissions import admin_auth, moderator_auth, public_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.runs import RunCreateSchema, RunSchema, RunUpdateSchema

router = Router()


def apply_run_embeds(
    run: Runs,
    embed_fields: List[str],
) -> dict:
    """Apply requested embeds to a run instance.

    This is the most complex embed function of all of the endpoints due to the
    complex relations it will have with other models.
    """
    embeds = {}

    if "game" in embed_fields and run.game:
        embeds["game"] = {
            "id": run.game.id,
            "name": run.game.name,
            "slug": run.game.slug,
            "release": run.game.release.isoformat(),
            "boxart": run.game.boxart,
            "twitch": run.game.twitch,
            "defaulttime": run.game.defaulttime,
            "idefaulttime": run.game.idefaulttime,
            "pointsmax": run.game.pointsmax,
            "ipointsmax": run.game.ipointsmax,
        }

    if "category" in embed_fields and run.category:
        embeds["category"] = {
            "id": run.category.id,
            "name": run.category.name,
            "slug": run.category.slug,
            "type": run.category.type,
            "url": run.category.url,
            "rules": run.category.rules,
            "appear_on_main": run.category.appear_on_main,
            "archive": run.category.archive,
        }

    if "level" in embed_fields and run.level:
        embeds["level"] = {
            "id": run.level.id,
            "name": run.level.name,
            "slug": run.level.slug,
            "url": run.level.url,
            "rules": run.level.rules,
        }

    # When player or player2 are in the embed field, it will relate their country codes
    # to the query and fill in additional information about the player(s) of the run.
    if "player" in embed_fields or "player2" in embed_fields:
        run_players = run.players.select_related("player__countrycode").order_by(
            "order"
        )

        for rp in run_players:
            player_data = {
                "id": rp.player.id,
                "name": (rp.player.nickname if rp.player.nickname else rp.player.name),
                "url": rp.player.url,
                "country": (
                    rp.player.countrycode.name if rp.player.countrycode else None
                ),
                "pronouns": rp.player.pronouns,
                "twitch": rp.player.twitch,
                "youtube": rp.player.youtube,
                "twitter": rp.player.twitter,
                "bluesky": rp.player.bluesky,
            }

            if rp.order == 1 and "player" in embed_fields:
                embeds["player"] = player_data
            elif rp.order == 2 and "player2" in embed_fields:
                embeds["player2"] = player_data

    if "variables" in embed_fields:
        try:
            run_variables = RunVariableValues.objects.filter(run=run).select_related(
                "variable", "value"
            )

            variables_data = []
            for rv in run_variables:
                if rv.variable and rv.value:
                    variables_data.append(
                        {
                            "variable": {
                                "id": rv.variable.id,
                                "name": rv.variable.name,
                                "slug": rv.variable.slug,
                                "scope": rv.variable.scope,
                            },
                            "value": {
                                "value": rv.value.value,
                                "name": rv.value.name,
                                "slug": rv.value.slug,
                            },
                        }
                    )

            embeds["variables"] = variables_data
        except Exception:
            embeds["variables"] = []

    return embeds


@router.get(
    "/{id}",
    response=Union[RunSchema, ErrorResponse],
    summary="Get Run by ID",
    description="""
    Retrieve a single run by its ID with full details and optional embeds.

    **Supported Parameters:**
    - `id` (str): Unique ID of the run being queried.
    - `embed` (Optional[list]): Comma-separated list of resources to embed.

    **Supported Embeds:**
    - `game`: Includes the metadata of the game related to the run queried.
    - `category`: Includes the metadata of the category related to the run queried.
    - `level`: Include the metadata of the level related to the run queried (if an IL run).
    - `player`: Includes the metadata of player 1's player information.
    - `player2`: Include the metadata of player 2's player information (if a Co-Op run).
    - `variables`: Include the metadata of the variables and values related to the run.

    **Examples:**
    - `/runs/y8dwozoj` - Basic run data.
    - `/runs/y8dwozoj?embed=game,player` - Include game and player.
    - `/runs/y8dwozoj?embed=player,player2,variables` - Co-op run with variables.
    - `/runs/y8dwozoj?embed=game,category,level,player` - Full run details.
    """,
    auth=public_auth,
    openapi_extra=RUNS_GET,
)
def get_run(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
) -> Union[RunSchema, ErrorResponse]:
    """Get a single run by ID."""
    if len(id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    # Checks to see what embeds are being used versus what is allowed
    # via this endpoint. It will return an error to the client if they
    # have an embed type not supported.
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("runs", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={
                    "valid_embeds": [
                        "game",
                        "category",
                        "level",
                        "player",
                        "player2",
                        "variables",
                    ]
                },
                code=400,
            )

    try:
        run = (
            Runs.objects.filter(id__iexact=id)
            .select_related("game", "category", "level", "platform", "approver")
            .prefetch_related(
                "runplayers_set__player",
                "runvariablevalues_set__variable",
                "runvariablevalues_set__value",
            )
            .first()
        )
        if not run:
            return ErrorResponse(
                error="Run ID does not exist",
                details=None,
                code=404,
            )

        run_data = RunSchema.model_validate(run)

        if embed_fields:
            embed_data = apply_run_embeds(run, embed_fields)
            for field, data in embed_data.items():
                setattr(run_data, field, data)

        return run_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve run", details={"exception": str(e)}, code=500
        )


@router.get(
    "/all",
    response=Union[List[RunSchema], ErrorResponse],
    summary="Get All Runs",
    description="""
    Retrieve runs with extensive filtering and search capabilities.

    **Supported Parameters:**
    - `game_id` (Optional[str]): Filter by specific game ID or slug
    - `category_id` (Optional[str]): Filter by specific category ID
    - `level_id` (Optional[str]): Filter by specific level ID (for IL runs)
    - `player_id` (Optional[str]): Filter by specific player ID
    - `runtype` (Optional[str]): Filter by run type (`main` or `il`)
    - `place` (Optional[int]): Filter by leaderboard position
    - `status` (Optional[str]): Filter by verification status (`verified`, `new`, or `rejected`)
    - `search`: Search in subcategory text
    - `embed`: Comma-separated list of resources to embed
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Examples:**
    - `/runs/all?game_id=thps4` - All runs for THPS4
    - `/runs/all?game_id=thps4&category_id=any&place=1` - THPS4 Any% world records
    - `/runs/all?player_id=v8lponvj&runtype=main` - Player's full-game runs
    - `/runs/all?search=normal&place=1&status=verified` - Verified WRs with "normal" in subcategory
    - `/runs/all?game_id=thps4&level_id=alcatraz&embed=player,game` - Alcatraz ILs with embeds
    """,
    auth=public_auth,
    openapi_extra=RUNS_ALL,
)
def get_all_runs(
    request: HttpRequest,
    game_id: Optional[str] = Query(
        None,
        description="Filter by game",
    ),
    category_id: Optional[str] = Query(
        None,
        description="Filter by category",
    ),
    level_id: Optional[str] = Query(
        None,
        description="Filter by level",
    ),
    player_id: Optional[str] = Query(
        None,
        description="Filter by player",
    ),
    runtype: Optional[str] = Query(
        None,
        description="Filter by type",
        pattern="^(main|il)$",
    ),
    place: Optional[int] = Query(
        None,
        description="Filter by place",
        ge=1,
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status",
        pattern="^(verified|new|rejected)$",
    ),
    search: Optional[str] = Query(
        None,
        description="Search subcategory text",
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
) -> Union[List[RunSchema], ErrorResponse]:
    # Checks to see what embeds are being used versus what is allowed
    # via this endpoint. It will return an error to the client if they
    # have an embed type not supported.
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("runs", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
                code=400,
            )

    try:
        queryset = Runs.objects.all().order_by("-v_date", "place")

        # If parameters are fulfilled by the client, this will further
        # drill down what the client is looking for.
        if game_id:
            queryset = queryset.filter(Q(game__id=game_id) | Q(game__slug=game_id))
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        if level_id:
            queryset = queryset.filter(level__id=level_id)
        if player_id:
            queryset = queryset.filter(
                Q(player__id=player_id) | Q(player2__id=player_id)
            )
        if runtype:
            queryset = queryset.filter(runtype=runtype)
        if place:
            queryset = queryset.filter(place=place)
        if status:
            status_mapping = {
                "verified": "verified",
                "new": "new",
                "rejected": "rejected",
            }
            if status in status_mapping:
                queryset = queryset.filter(vid_status=status_mapping[status])
        if search:
            queryset = queryset.filter(subcategory__icontains=search)

        runs = queryset[offset : offset + limit]

        run_schemas = []
        for run in runs:
            run_data = RunSchema.model_validate(run)

            if embed_fields:
                embed_data = apply_run_embeds(run, embed_fields)
                for field, data in embed_data.items():
                    setattr(run_data, field, data)

            run_schemas.append(run_data)

        return run_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve runs",
            details={"exception": str(e)},
            code=500,
        )


@router.post(
    "/",
    response=Union[RunSchema, ErrorResponse],
    summary="Create Run",
    description="""
    Create a new speedrun record with full validation.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**

    **Complex Validation:**
    - Game/category/level relationships must be valid.
    - Players must exist if specified.
    - Variable values must match variable constraints.
    - Run type must match category type.

    **Request Body:**
    - `game_id` (str): Game ID the run belongs to.
    - `category_id` (Optional[str]): Category ID the run belongs to.
    - `level_id` (Optional[str]): Level ID (for IL runs).
    - `player_ids` (Optional[List[str]]): List of player IDs in order of participation.
    - `runtype` (str): Run type (`main` or `il`).
    - `place` (int): Leaderboard position.
    - `subcategory` (Optional[str]): Human-readable subcategory description.
    - `time` (Optional[str]): Formatted time string (e.g., "1:23.456").
    - `time_secs` (Optional[float]): Time in seconds (for sorting/calculations).
    - `video` (Optional[str]): Video URL.
    - `date` (Optional[datetime]): Submission date (ISO format).
    - `v_date` (Optional[datetime]): Verification date (ISO format).
    - `url` (str): Speedrun.com URL.
    - `variable_values` (Optional[Dict[str, str]]): Variable value selections as key-value pairs.

    **Variable Values Format:**
    ```json
    {
        "variable_values": {
            "variable_id_1": "value_id_1",
            "variable_id_2": "value_id_2"
        }
    }
    ```
    """,
    auth=moderator_auth,
    openapi_extra=RUNS_POST,
)
def create_run(
    request: HttpRequest,
    run_data: RunCreateSchema,
) -> Union[RunSchema, ErrorResponse]:
    try:
        game = Games.objects.filter(id=run_data.game_id).first()
        if not game:
            return ErrorResponse(
                error="Game does not exist",
                details=None,
                code=400,
            )

        category = None
        if run_data.category_id:
            category = Categories.objects.filter(
                id=run_data.category_id, game=game
            ).first()
            if not category:
                return ErrorResponse(
                    error="Category does not exist for this game",
                    details=None,
                    code=400,
                )

        level = None
        if run_data.level_id:
            level = Levels.objects.filter(id=run_data.level_id, game=game).first()
            if not level:
                return ErrorResponse(
                    error="Level does not exist for this game",
                    details=None,
                    code=400,
                )

        players_list = []
        if run_data.player_ids:
            for player_id in run_data.player_ids:
                player = Players.objects.filter(id=player_id).first()
                if not player:
                    return ErrorResponse(
                        error=f"Player with ID '{player_id}' does not exist",
                        details=None,
                        code=400,
                    )
                players_list.append(player)

        if category and run_data.runtype == "main" and category.type != "per-game":
            return ErrorResponse(
                error="Main runs require per-game categories",
                details=None,
                code=400,
            )
        if (
            level
            and run_data.runtype == "il"
            and category
            and category.type != "per-level"
        ):
            return ErrorResponse(
                error="IL runs require per-level categories",
                details=None,
                code=400,
            )

        create_data = run_data.model_dump(
            exclude={
                "game_id",
                "category_id",
                "level_id",
                "player_ids",
                "variable_values",
            }
        )

        run = Runs.objects.create(
            game=game,
            category=category,
            level=level,
            **create_data,
        )

        for index, player in enumerate(players_list, start=1):
            RunPlayers.objects.create(run=run, player=player, order=index)

        if run_data.variable_values:
            try:
                for var_id, value_id in run_data.variable_values.items():
                    variable = Variables.objects.filter(id=var_id).first()
                    value = VariableValues.objects.filter(
                        value=value_id, var=variable
                    ).first()

                    if variable and value:
                        RunVariableValues.objects.create(
                            run=run, variable=variable, value=value
                        )
            except Exception as e:
                return ErrorResponse(
                    error="Run Update Failed (Variables)",
                    details={"exception": str(e)},
                    code=500,
                )

        return RunSchema.model_validate(run)

    except Exception as e:
        return ErrorResponse(
            error="Run Creation Failed",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{id}",
    response=Union[RunSchema, ErrorResponse],
    summary="Update Run",
    description="""
    Updates the run based on its unique ID.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**

    **Supported Parameters:**
    - `id` (str): Unique ID of the run being edited.

    **Request Body:**
    - `game_id` (Optional[str]): Updated game ID.
    - `category_id` (Optional[str]): Updated category ID.
    - `level_id` (Optional[str]): Updated level ID (for IL runs).
    - `player_ids` (Optional[List[str]]): Updated list of player IDs in order of participation.
    - `runtype` (Optional[str]): Updated run type (`main` or `il`).
    - `place` (Optional[int]): Updated leaderboard position.
    - `subcategory` (Optional[str]): Updated human-readable subcategory description.
    - `time` (Optional[str]): Updated formatted time string (e.g., "1:23.456").
    - `time_secs` (Optional[float]): Updated time in seconds (for sorting/calculations).
    - `video` (Optional[str]): Updated video URL.
    - `date` (Optional[datetime]): Updated submission date (ISO format).
    - `v_date` (Optional[datetime]): Updated verification date (ISO format).
    - `url` (Optional[str]): Updated Speedrun.com URL.
    - `variable_values` (Optional[Dict[str, str]]): Updated variable value selections as key-value pairs.
    """,
    auth=moderator_auth,
    openapi_extra=RUNS_PUT,
)
def update_run(
    request: HttpRequest,
    id: str,
    run_data: RunUpdateSchema,
) -> Union[RunSchema, ErrorResponse]:
    try:
        run = (
            Runs.objects.filter(id__iexact=id)
            .select_related("game", "category", "level", "platform", "approver")
            .prefetch_related(
                "runplayers_set__player",
                "runvariablevalues_set__variable",
                "runvariablevalues_set__value",
            )
            .first()
        )
        if not run:
            return ErrorResponse(
                error="Run Doesn't Exist",
                details=None,
                code=404,
            )

        update_data = run_data.model_dump(exclude_unset=True)

        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(
                    error="Game Doesn't Exist",
                    details=None,
                    code=400,
                )
            run.game = game
            del update_data["game_id"]

        if "category_id" in update_data:
            if update_data["category_id"]:
                category = Categories.objects.filter(
                    id=update_data["category_id"], game=run.game
                ).first()
                if not category:
                    return ErrorResponse(
                        error="Category Doesn't Exist for This Game",
                        details=None,
                        code=400,
                    )
                run.category = category
            else:
                run.category = None
            del update_data["category_id"]

        if "level_id" in update_data:
            if update_data["level_id"]:
                level = Levels.objects.filter(
                    id=update_data["level_id"], game=run.game
                ).first()
                if not level:
                    return ErrorResponse(
                        error="Level Doesn't Exist for This Game",
                        details=None,
                        code=400,
                    )
                run.level = level
            else:
                run.level = None
            del update_data["level_id"]

        if "player_ids" in update_data:
            RunPlayers.objects.filter(run=run).delete()

            if update_data["player_ids"]:
                for index, player_id in enumerate(update_data["player_ids"], start=1):
                    player = Players.objects.filter(id=player_id).first()
                    if not player:
                        return ErrorResponse(
                            error=f"Player ID '{player_id}' Doesn't Exist",
                            details=None,
                            code=400,
                        )
                    RunPlayers.objects.create(run=run, player=player, order=index)

            del update_data["player_ids"]

        if "variable_values" in update_data:
            try:
                RunVariableValues.objects.filter(run=run).delete()

                if update_data["variable_values"]:
                    for var_id, value_id in update_data["variable_values"].items():
                        variable = Variables.objects.filter(id=var_id).first()
                        value = VariableValues.objects.filter(
                            value=value_id, var=variable
                        ).first()

                        if variable and value:
                            RunVariableValues.objects.create(
                                run=run, variable=variable, value=value
                            )
            except Exception as e:
                return ErrorResponse(
                    error="Run Update Failed (Variables)",
                    details={"exception": str(e)},
                    code=500,
                )

            del update_data["variable_values"]

        for field, value in update_data.items():
            setattr(run, field, value)

        run.save()
        return RunSchema.model_validate(run)

    except Exception as e:
        return ErrorResponse(
            error="Run Update Failed",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Run",
    description="""
    Deletes the selected run by its ID.

    **REQUIRES ADMIN ACCESS.**

    **Supported Parameters:**
    - `id` (str): Unique ID of the run being deleted.
    """,
    auth=admin_auth,
    openapi_extra=RUNS_DELETE,
)
def delete_run(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        run = (
            Runs.objects.filter(id__iexact=id)
            .select_related("game", "category", "level", "platform", "approver")
            .prefetch_related(
                "runplayers_set__player",
                "runvariablevalues_set__variable",
                "runvariablevalues_set__value",
            )
            .first()
        )
        if not run:
            return ErrorResponse(
                error="Run does not exist",
                details=None,
                code=404,
            )

        game_name = run.game.name if run.game else "Unknown"
        run_players = run.players.all()
        player_names = (
            ", ".join([p.name for p in run_players])
            if run_players.exists()
            else "Anonymous"
        )

        run.delete()
        return {"message": f"Run by {player_names} in {game_name} deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete run",
            details={"exception": str(e)},
            code=500,
        )
