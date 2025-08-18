from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Players, Runs

from api.serializers.core import PlayerSerializer, RunSerializer


class API_PlayerRecords(APIView):
    """Viewset for viewing all records of a specific player.

    This viewset returns all main and IL runs associated with a player, including any embeds passed
    into the query.

    Methods:
        get:
            Returns a list of all speedruns for the given player, separated by main and IL.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Runs`, `Players`

    Allowed Queries:
        - `oldest`: Returns a list of the user's personal bests with the oldest listed first.
        - `newest`: Returns a list of the user's personal bests with the newest listed first.

    Allowed Embeds:
        - `categories`: Embeds each run's associated category into the response.
        - `levels`: Embeds each run's associated level into the response.
        - `games`: Embeds each run's associated game into the response.
        - `platforms`: Embeds each run's associated platform into the response.

    Embed Examples:
        `/players/123456/pbs?embed=games,categories`

    Example Response (JSON):
        ```
        {
            "id": "e8ew5p80",
            "name": "ThePackle",
            "nickname": "Packle",
            "url": "https://www.speedrun.com/user/ThePackle",
            "country": "United States",
            "pronouns": "He/Him",
            "twitch": "https://www.twitch.tv/ThePackle",
            "youtube": "https://www.youtube.com/user/ThePackle",
            "twitter": null,
            "ex_stream": false,
            "awards": [
                {
                    "name": "Most Helpful (2022)"
                }
            ],
            "stats": {
                "total_pts": 16389,
                "main_pts": 15251,
                "il_pts": 1138,
                "total_runs": 50
            },
            "main_runs": [
                {
                    "id": "2yw311nm",
                    "runtype": "main",
                    "game": "ok6qq06g",
                    "category": "5dwjv0kg",
                    "level": null,
                    "subcategory": "Classic (Normal, NG+)",
                    "place": 9,
                    "players": "e8ew5p80",
                    "date": "2016-02-06T02:22:10Z",
                    "times": {
                        "defaulttime": "realtime",
                        "time": "3m 17s",
                        "time_secs": 197.0,
                        "timenl": "0",
                        "timenl_secs": 0.0,
                        "timeigt": "3m 14s",
                        "timeigt_secs": 194.0
                    },
                    "system": {
                        "platform": "8gej2n93",
                        "emulated": false
                    },
                    "status": {
                        "vid_status": "verified",
                        "approver": "e8ew5p80",
                        "v_date": "2016-02-06T02:22:11Z",
                        "obsolete": false
                    },
                    "videos": {
                        "video": "http://www.twitch.tv/thepackle/v/41034089",
                        "arch_video": null
                    },
                    "variables": {
                        "gnxwz48v": "jqz2e2qp",
                        "5lyjpxgl": "21ge0vml"
                    },
                    "meta": {
                        "points": 375,
                        "url": "https://www.speedrun.com/thug2/run/2yw311nm"
                    }
                },
            ...
        }
        ```
    """

    ALLOWED_EMBEDS = {"categories", "levels", "games", "platforms"}

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a player's full record history based on its ID.

        This endpoint returns all full-game and individual level speedruns for a specific player.
        These runs are separated into `main_runs` and `il_runs`. The player can be looked up by
        either username or their ID. Results can include embedded data using the `embed` query
        parameter.

        Args:
            request (HttpRequest): The request object containing the information, queries, or embeds
            id (str): The exact ID or username of the player requesting to be returned.

        Returns:
            Response: A response object containing the JSON data of a player's speedruns.
        """

        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        embed_fields = request.GET.get("embed", "").split(",")
        embed_fields = [field.strip() for field in embed_fields if field.strip()]
        invalid_embeds = [
            field for field in embed_fields if field not in self.ALLOWED_EMBEDS
        ]

        if invalid_embeds:
            return Response(
                {"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        player = (
            Players.objects.filter(id__iexact=id).first()
            or Players.objects.filter(name__iexact=id).first()
        )

        if player:
            player_data = PlayerSerializer(player).data

            main_runs = Runs.objects.filter(
                runtype="main",
                player=player,
                obsolete=False,
            )
            il_runs = Runs.objects.filter(
                runtype="il",
                player=player,
                obsolete=False,
            )

            main_runs = main_runs.order_by("-v_date")
            il_runs = il_runs.order_by("-v_date")

            main_data = RunSerializer(
                main_runs, many=True, context={"embed": embed_fields}
            ).data
            il_data = RunSerializer(
                il_runs, many=True, context={"embed": embed_fields}
            ).data

            return Response({**player_data, "main_runs": main_data, "il_runs": il_data})
        else:
            return Response(
                {"ERROR": "Player ID or Name does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
