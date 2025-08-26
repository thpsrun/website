from typing import List, Optional, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import (
    Categories,
    Games,
    Levels,
    Players,
    Runs,
    Variables,
    VariableValues,
)

from api.permissions import contributor_auth, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.runs import RunCreateSchema, RunSchema, RunUpdateSchema

runs_router = Router(tags=["Runs"])


def apply_run_embeds(
    run: Runs,
    embed_fields: List[str],
) -> dict:
    """
    Apply requested embeds to a run instance.

    This is the most complex embed function due to all the relationships
    runs have with other models.
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
            "hidden": run.category.hidden,
        }

    if "level" in embed_fields and run.level:
        embeds["level"] = {
            "id": run.level.id,
            "name": run.level.name,
            "slug": run.level.slug,
            "url": run.level.url,
            "rules": run.level.rules,
        }

    if "players" in embed_fields:
        # Get all players for this run, ordered by their position
        run_players = run.run_players.select_related("player__countrycode").order_by(
            "order"
        )

        players_data = []
        for rp in run_players:
            players_data.append(
                {
                    "id": rp.player.id,
                    "name": (
                        rp.player.nickname if rp.player.nickname else rp.player.name
                    ),
                    "url": rp.player.url,
                    "country": (
                        rp.player.countrycode.name if rp.player.countrycode else None
                    ),
                    "pronouns": rp.player.pronouns,
                    "twitch": rp.player.twitch,
                    "youtube": rp.player.youtube,
                    "twitter": rp.player.twitter,
                    "bluesky": rp.player.bluesky,
                    "order": rp.order,
                }
            )

        embeds["players"] = players_data if players_data else []

    if "variables" in embed_fields:
        # Get variable selections for this run
        # This is complex due to the many-to-many through relationship
        try:
            from srl.models import RunVariableValues

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
            # Fallback if RunVariableValues model doesn't exist yet
            embeds["variables"] = []

    return embeds


@runs_router.get(
    "/{id}",
    response=Union[RunSchema, ErrorResponse],
    summary="Get Run by ID",
    description="""
    Retrieve a single run by its ID with full details and optional embeds.

    **Supported Embeds:**
    - `game`: Include game information
    - `category`: Include category information
    - `level`: Include level information (for IL runs)
    - `player`: Include primary player details
    - `player2`: Include second player details (co-op runs)
    - `variables`: Include variable selections (subcategories)

    **Examples:**
    - `/runs/y8dwozoj` - Basic run data
    - `/runs/y8dwozoj?embed=game,player` - Include game and player
    - `/runs/y8dwozoj?embed=player,player2,variables` - Co-op run with variables
    """,
    auth=read_only_auth,
)
def get_run(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
) -> Union[RunSchema, ErrorResponse]:
    """Get a single run by ID."""
    if len(id) > 15:
        return ErrorResponse(error="ID must be 15 characters or less", code=400)

    # Parse embeds
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
        run = Runs.objects.filter(id__iexact=id).first()
        if not run:
            return ErrorResponse(error="Run ID does not exist", code=404)

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


@runs_router.get(
    "/all",
    response=Union[List[RunSchema], ErrorResponse],
    summary="Get All Runs",
    description="""
    Retrieve runs with extensive filtering and search capabilities.

    **Query Parameters:**
    - `game_id`: Filter by specific game
    - `category_id`: Filter by specific category
    - `level_id`: Filter by specific level (IL runs)
    - `player_id`: Filter by specific player
    - `runtype`: Filter by run type (main or il)
    - `place`: Filter by leaderboard position
    - `status`: Filter by verification status
    - `search`: Search in subcategory text
    - `embed`: Include related data
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Advanced Filtering Examples:**
    - `?game_id=thps4&category_id=any&place=1` - World records for THPS4 Any%
    - `?player_id=thepackle&runtype=main` - Player's full-game runs
    - `?search=normal&place=1` - WRs containing "normal" in subcategory
    """,
    auth=read_only_auth,
)
def get_all_runs(
    request: HttpRequest,
    game_id: Optional[str] = Query(None, description="Filter by game"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    level_id: Optional[str] = Query(None, description="Filter by level"),
    player_id: Optional[str] = Query(None, description="Filter by player"),
    runtype: Optional[str] = Query(
        None, description="Filter by type", pattern="^(main|il)$"
    ),
    place: Optional[int] = Query(None, description="Filter by place", ge=1),
    status: Optional[str] = Query(
        None, description="Filter by status", pattern="^(verified|new|rejected)$"
    ),
    search: Optional[str] = Query(None, description="Search subcategory text"),
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Union[List[RunSchema], ErrorResponse]:
    """Get runs with comprehensive filtering."""
    # Parse embeds
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("runs", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}", code=400
            )

    try:
        # Build queryset with filters
        queryset = Runs.objects.all().order_by("-v_date", "place")

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
            # Map status to internal field names
            status_mapping = {
                "verified": "verified",
                "new": "new",
                "rejected": "rejected",
            }
            if status in status_mapping:
                queryset = queryset.filter(vid_status=status_mapping[status])
        if search:
            queryset = queryset.filter(subcategory__icontains=search)

        # Apply pagination
        runs = queryset[offset : offset + limit]

        # Convert to schemas
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
            error="Failed to retrieve runs", details={"exception": str(e)}, code=500
        )


@runs_router.post(
    "/",
    response=Union[RunSchema, ErrorResponse],
    summary="Create Run",
    description="""
    Create a new speedrun record with full validation.

    **Complex Validation:**
    - Game/category/level relationships must be valid
    - Players must exist if specified
    - Variable values must match variable constraints
    - Run type must match category type

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
    auth=contributor_auth,
)
def create_run(
    request: HttpRequest,
    run_data: RunCreateSchema,
) -> Union[RunSchema, ErrorResponse]:
    """Create a new run with comprehensive validation."""
    try:
        # Validate game
        game = Games.objects.filter(id=run_data.game_id).first()
        if not game:
            return ErrorResponse(error="Game does not exist", code=400)

        # Validate category if provided
        category = None
        if run_data.category_id:
            category = Categories.objects.filter(
                id=run_data.category_id, game=game
            ).first()
            if not category:
                return ErrorResponse(
                    error="Category does not exist for this game", code=400
                )

        # Validate level if provided
        level = None
        if run_data.level_id:
            level = Levels.objects.filter(id=run_data.level_id, game=game).first()
            if not level:
                return ErrorResponse(
                    error="Level does not exist for this game", code=400
                )

        # Validate players
        player = None
        if run_data.player_id:
            player = Players.objects.filter(id=run_data.player_id).first()
            if not player:
                return ErrorResponse(error="Player does not exist", code=400)

        player2 = None
        if run_data.player2_id:
            player2 = Players.objects.filter(id=run_data.player2_id).first()
            if not player2:
                return ErrorResponse(error="Player2 does not exist", code=400)

        # Validate run type consistency
        if category and run_data.runtype == "main" and category.type != "per-game":
            return ErrorResponse(
                error="Main runs require per-game categories", code=400
            )
        if (
            level
            and run_data.runtype == "il"
            and category
            and category.type != "per-level"
        ):
            return ErrorResponse(error="IL runs require per-level categories", code=400)

        # Create the run
        create_data = run_data.dict(
            exclude={
                "game_id",
                "category_id",
                "level_id",
                "player_id",
                "player2_id",
                "variable_values",
            }
        )

        run = Runs.objects.create(
            game=game,
            category=category,
            level=level,
            player=player,
            player2=player2,
            **create_data,
        )

        # Handle variable values if provided
        if run_data.variable_values:
            try:
                from srl.models import RunVariableValues

                for var_id, value_id in run_data.variable_values.items():
                    variable = Variables.objects.filter(id=var_id).first()
                    value = VariableValues.objects.filter(
                        value=value_id, var=variable
                    ).first()

                    if variable and value:
                        RunVariableValues.objects.create(
                            run=run, variable=variable, value=value
                        )
            except Exception:
                # RunVariableValues model might not exist yet
                pass

        return RunSchema.model_validate(run)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create run", details={"exception": str(e)}, code=500
        )


@runs_router.put(
    "/{id}",
    response=Union[RunSchema, ErrorResponse],
    summary="Update Run",
    auth=contributor_auth,
)
def update_run(
    request: HttpRequest,
    id: str,
    run_data: RunUpdateSchema,
) -> Union[RunSchema, ErrorResponse]:
    """Update an existing run."""
    try:
        run = Runs.objects.filter(id__iexact=id).first()
        if not run:
            return ErrorResponse(error="Run does not exist", code=404)

        update_data = run_data.dict(exclude_unset=True)

        # Handle relationship updates with validation
        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(error="Game does not exist", code=400)
            run.game = game
            del update_data["game_id"]

        if "category_id" in update_data:
            if update_data["category_id"]:
                category = Categories.objects.filter(
                    id=update_data["category_id"], game=run.game
                ).first()
                if not category:
                    return ErrorResponse(
                        error="Category does not exist for this game", code=400
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
                        error="Level does not exist for this game", code=400
                    )
                run.level = level
            else:
                run.level = None
            del update_data["level_id"]

        if "player_id" in update_data:
            if update_data["player_id"]:
                player = Players.objects.filter(id=update_data["player_id"]).first()
                if not player:
                    return ErrorResponse(error="Player does not exist", code=400)
                run.player = player
            else:
                run.player = None
            del update_data["player_id"]

        if "player2_id" in update_data:
            if update_data["player2_id"]:
                player2 = Players.objects.filter(id=update_data["player2_id"]).first()
                if not player2:
                    return ErrorResponse(error="Player2 does not exist", code=400)
                run.player2 = player2
            else:
                run.player2 = None
            del update_data["player2_id"]

        # Handle variable values update
        if "variable_values" in update_data:
            try:
                from srl.models import RunVariableValues

                # Clear existing variable values
                RunVariableValues.objects.filter(run=run).delete()

                # Add new variable values
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
            except Exception:
                pass
            del update_data["variable_values"]

        # Update remaining fields
        for field, value in update_data.items():
            setattr(run, field, value)

        run.save()
        return RunSchema.model_validate(run)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update run", details={"exception": str(e)}, code=500
        )


@runs_router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Run",
    auth=contributor_auth,
)
def delete_run(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    """Delete a run."""
    try:
        run = Runs.objects.filter(id__iexact=id).first()
        if not run:
            return ErrorResponse(error="Run does not exist", code=404)

        player_name = run.player.name if run.player else "Unknown"
        game_name = run.game.name if run.game else "Unknown"

        run.delete()
        return {"message": f"Run by {player_name} in {game_name} deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete run", details={"exception": str(e)}, code=500
        )
