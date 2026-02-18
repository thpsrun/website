from textwrap import dedent
from typing import TYPE_CHECKING, Annotated, Any

from django.http import HttpRequest
from ninja import Query, Router
from ninja.responses import codes_4xx
from pydantic import Field

from api.permissions import public_auth
from api.v1.schemas.base import ErrorResponse

if TYPE_CHECKING:
    pass

router = Router()


@router.get(
    "/player/{user}",
    response={200: list[dict[str, Any]], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Get Player's Run Information",
    description=dedent(
        """
    Gets information on a specific player, with optional embeds for a player's current approved
    full game and/or individual level speedruns (with an additional to include obsoletes).

    **Supported Embeds:**
    - `pbs`: Includes an embed for all current and approved speedruns for the specific player.
    - `obsoletes`: Includes an embed for ALL approvedspeedruns for a specific player, to include
        obsolete runs. This takes precedent over `pbs`.

    **Supported Parameters:**
    - `user` (str): Filter by specific player's name or unique ID.

    **Examples:**
    - `/website/player/bobby` - Gets all stat information for a player.
    - `/webiste/player/bobby?embed=pbs` - Gets all of Bobby's approved speedruns.
    - `/website/player/bobby?embed=pbs,obsoletes` - Gets ALL of Bobby's speedruns, regardless of
        if they are current. This takes precedent over `pbs`.

    """
    ),
    auth=public_auth,
    # openapi_extra=MAIN_PAGE_PLAYERS,
)
def get_player_data(
    request: HttpRequest,
    embed: Annotated[
        str | None,
        Query,
        Field(description="Comma-separated embed types"),
    ] = None,
) -> tuple[int, dict[str, Any] | ErrorResponse]:
    if not embed:
        return 400, ErrorResponse(
            error="Must specify embed types to retrieve",
            details={"valid_embed_types": ["obsoletes", "pbs"]},
        )

    embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
    valid_embed_types = {"obsoletes", "pbs"}
    invalid_embeds = [field for field in embed_fields if field not in valid_embed_types]

    if invalid_embeds:
        return 400, ErrorResponse(
            error=f"Invalid embed type(s): {', '.join(invalid_embeds)}",
            details={"valid_embed_types": list(valid_embed_types)},
        )

    try:
        response_data = {}

        if "obsoletes" in embed_fields:
            response_data["obsoletes"]
        elif "pbs" in embed_fields:
            response_data["pbs"]

        return 200, response_data
    except Exception as e:
        return 500, ErrorResponse(
            error="Server error!",
            details={"exception": str(e)},
        )
