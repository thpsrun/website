from celery import chain
from django.db.models import Q
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import (
    Categories,
    Games,
    Levels,
    NowStreaming,
    Players,
    Runs,
    Variables,
    VariableValues,
)
from srl.tasks import update_player

from api.serializers import (
    CategorySerializer,
    GameSerializer,
    LevelSerializer,
    PlayerSerializer,
    PlayerSerializerPost,
    PlayerStreamSerializer,
    RunSerializer,
    StreamSerializer,
    StreamSerializerPost,
    ValueSerializer,
    VariableSerializer,
)
from api.tasks import normalize_src


class ReadOnlyOrAuthenticated(BasePermission):
    """
    Custom permission to only allow read access without authentication,
    but require authentication for write operations.
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user and request.user.is_authenticated


class API_Runs(APIView):
    """Viewset for viewing, creating, or editing speedruns.

    This viewset provides the standard actions for creating, editing, or viewing speedruns,
    including any embeds passed into the query.

    Methods:
        get:
            Returns a speedrun based on its ID.
        post:
            Creates a new speedrun based upon the ID after it has been properly queried through
            the Speedrun.com API.
        put:
            Updates (or creates) a new speedrun based upon the ID after it has been properly
            queried through the Speedrun.com API.

    Permissions:
        - `ReadOnlyOrAuthenticated`: GET requests are public, POST/PUT require authentication.

    Model: `Runs`

    Allowed Queries:
        - `status`: Returns a list of speedruns awaiting verification (if the run has `new` as its
        `vid_status`).
            Example: `/runs/all?query=status`

    Embeds:
        - `category`: Embeds the related category into the response.
        - `level`: Embeds the related level into the response (only for individual-level speedruns).
        - `game`: Embeds the related game into the response.
        - `variables`: Embeds all related variables and values into the response.
        - `platform`: Embeds the related platform into the response.
        - `players`: Embeds all related players into the response.
        - `record`: Embeds world record information for the related category into the response.

    Embed Examples:
        - `/runs/123456?embed=category,level,game`
        - `/runs/123456?embed=players`

    Example Response (JSON):
        ```
        {
            "id": "z5l9eljy",
            "runtype": "main",
            "game": "xldeeed3",
            "category": "rklge08d",
            "level": null,
            "subcategory": "Any% (5th Gen)",
            "place": 1,
            "players": "68w4mqxg",
            "date": "2025-04-16T06:08:44Z",
            "times": {
                "defaulttime": "ingame",
                "time": "25m 42s",
                "time_secs": 1542.0,
                "timenl": "0",
                "timenl_secs": 0.0,
                "timeigt": "0",
                "timeigt_secs": 0.0
            },
            "record": z5l9eljy,
            "system": {
                "platform": "wxeod9rn",
                "emulated": true
            },
            "status": {
                "vid_status": "verified",
                "approver": "pj0v90mx",
                "v_date": "2025-04-16T22:09:46Z",
                "obsolete": false
            },
            "videos": {
                "video": "https://youtu.be/Xay5dWSfDQY",
                "arch_video": null
            },
            "variables": {
                "ylq9qkv8": "rqv4kprq"
            },
            "meta": {
                "points": 1000,
                "url": "https://www.speedrun.com/thps4/run/z5l9eljy"
            },
            "description": "this is a description"
        }
        ```
    """

    ALLOWED_QUERIES = {"status", "latest", "latest-wrs", "latest-pbs", "records"}
    ALLOWED_EMBEDS = {
        "category",
        "level",
        "game",
        "variables",
        "platform",
        "players",
        "record",
    }
    permission_classes = [ReadOnlyOrAuthenticated]

    def _get_status_runs(self, embed_fields):
        """Get runs with 'new' status for status query."""
        new_runs = Runs.objects.filter(vid_status="new")
        return RunSerializer(
            new_runs, many=True, context={"embed": embed_fields}
        ).data

    def _get_latest_runs(self, embed_fields):
        """Get latest personal bests for latest query."""
        pbs = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .select_related(
                "game",
                "player",
                "player__countrycode",
            )
            .defer(
                "variables",
                "platform",
                "description",
            )
            .filter(place__gt=1, obsolete=False, v_date__isnull=False)
            .order_by("-v_date")
        )[:5]
        
        return RunSerializer(
            pbs, many=True, context={"embed": embed_fields}
        ).data

    def _get_latest_wrs(self, embed_fields):
        """Get latest world records for latest-wrs query."""
        wrs = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .select_related(
                "game",
                "player",
                "player__countrycode",
            )
            .defer(
                "variables",
                "platform",
                "description",
            )
            .filter(place=1, obsolete=False, v_date__isnull=False)
            .order_by("-v_date")
        )[:5]
        
        return RunSerializer(
            wrs, many=True, context={"embed": embed_fields}
        ).data

    def _get_latest_pbs(self, embed_fields):
        """Get latest personal bests for latest-pbs query (same as latest-wrs currently)."""
        wrs = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .select_related(
                "game",
                "player",
                "player__countrycode",
            )
            .defer(
                "variables",
                "platform",
                "description",
            )
            .filter(place=1, obsolete=False, v_date__isnull=False)
            .order_by("-v_date")
        )[:5]
        
        return RunSerializer(
            wrs, many=True, context={"embed": embed_fields}
        ).data

    def _get_records(self, embed_fields):
        """Get grouped world records for main categories."""
        subcategories = [
            "Any%",
            "Any% (6th Gen)",
            "100%",
            "Any% (No Major Glitches)",
            "All Goals & Golds (No Major Glitches)",
            "All Goals & Golds (All Careers)",
            "All Goals & Golds (6th Gen)",
            "Any% (6th Gen, Normal)",
            "100% (Normal)",
            "Any% (Beginner)",
            "100% (NSR)",
            "Story (Easy, NG+)",
            "100% (NG)",
            "Classic (Normal, NG+)",
            "Story Mode (Easy, NG+)",
            "Classic Mode (Normal)",
            "Any% (360/PS3)",
            "100% (360/PS3)",
            "Any% Tour Mode (All Tours, New Game)",
            "All Goals & Golds (All Tours, New Game)",
        ]

        exempt_games = [
            "GBA",
            "PSP",
            "GBC",
            "Category Extensions",
            "Remix",
            "Sk8land",
            "HD",
            "2x",
        ]

        exclusion_filter = Q()
        for game in exempt_games:
            exclusion_filter |= Q(game__name__icontains=game)

        runs = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"], obsolete=True)
            .exclude(exclusion_filter)
            .select_related(
                "game",
                "player",
                "player__countrycode",
            )
            .defer(
                "variables",
                "platform",
                "description",
            )
            .filter(runtype="main", place=1, subcategory__in=subcategories)
            .order_by("-subcategory")
            .annotate(o_date=TruncDate("date"))
        )

        # Group runs together within the same game and subcategory for ties
        grouped_runs = []
        seen_records = set()

        for run in runs:
            key = (run.game.slug, run.subcategory, run.time)
            if key not in seen_records:
                grouped_runs.append(
                    {
                        "game": run.game,
                        "subcategory": run.subcategory,
                        "time": run.time,
                        "players": [],
                    }
                )
                seen_records.add(key)

            for record in grouped_runs:
                if (
                    record["game"].slug == run.game.slug
                    and record["subcategory"] == run.subcategory
                    and record["time"] == run.time
                ):
                    from api.serializers import PlayerSerializer
                    record["players"].append(
                        {
                            "player": PlayerSerializer(run.player).data if run.player else None,
                            "url": run.url,
                            "date": run.o_date
                        }
                    )

        # Sort runs by game release date, oldest first
        run_list = sorted(grouped_runs, key=lambda x: x["game"].release, reverse=False)

        # Serialize game objects
        for run in run_list:
            if run["game"]:
                run["game"] = GameSerializer(run["game"]).data

        return run_list

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Returns a speedrun based on its ID.

        Args:
            request (Request): The request object containing the information, queries, or embeds.
            id (str): The exact ID of the speedrun requesting to be returned.
                - "all" is a valid `id`, but must be used in conjunction with a query.

        Returns:
            Response: A response object containing the JSON data of a speedrun.
        """

        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query_fields = request.GET.get("query", "").split(",")
        query_fields = [field.strip() for field in query_fields if field.strip()]
        invalid_queries = [
            field for field in query_fields if field not in self.ALLOWED_QUERIES
        ]

        if invalid_queries:
            return Response(
                {"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"},
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

        if id == "all":
            response_data = {}
            
            if "status" in query_fields:
                response_data["new_runs"] = self._get_status_runs(embed_fields)
                
            if "latest" in query_fields:
                response_data["latest_pbs"] = self._get_latest_runs(embed_fields)
                
            if "latest-wrs" in query_fields:
                response_data["latest_wrs"] = self._get_latest_wrs(embed_fields)
                
            if "latest-pbs" in query_fields:
                response_data["latest_pbs"] = self._get_latest_pbs(embed_fields)
                
            if "records" in query_fields:
                response_data["records"] = self._get_records(embed_fields)
                
            if response_data:
                return Response(response_data)
            else:
                return Response(
                    {"ERROR": "'all' can only be used with a query (status, latest, latest-wrs, latest-pbs, records)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            run = Runs.objects.filter(id__iexact=id).first()
            if run:
                return Response(
                    RunSerializer(run, context={"embed": embed_fields}).data,
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"ERROR": "run id provided does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )

    def post(
        self,
        _,
        id: str,
    ) -> HttpResponse:
        """Creates a new speedrun object based on its ID.

        After the `id` is given, the data is normalized, processed, and validated before it is
        added as a new `Runs` model object.

        Args:
            id (str): The exact ID of the speedrun requesting to be added to the database.

        Returns:
            Response: A response object containing the JSON data of a speedrun.
        """

        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        s_chain = chain(normalize_src.s(id))()
        normalize = s_chain.get()

        if normalize == "invalid":
            return Response(
                {"ERROR": "id provided does not belong to this leaderboard's games."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            run = Runs.objects.filter(id=id).first()
            if run:
                return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"ERROR": f"Unknown error - The run id {id} could not be called."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    def put(
        self,
        _,
        id,
    ) -> HttpResponse:
        """Updates (or creates) a speedrun object based on its ID.

        After the `id` is given, the data is normalized, processed, and validated before it is
        updated in the `Runs` model. If the `id` does not exist already, it is added.

        Args:
            id (str): The exact ID of the speedrun requesting to be updated or added to the database

        Returns:
            Response: A response object containing the JSON data of a speedrun.
        """

        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        s_chain = chain(normalize_src.s(id))()
        normalize = s_chain.get()

        if normalize == "invalid":
            return Response(
                {"ERROR": "id provided does not belong to this leaderboard's games."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            run = Runs.objects.filter(id=id).first()
            if run:
                return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"ERROR": f"Unknown error - The run id {id} could not be called."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class API_Players(APIView):
    """Viewset for viewing a specific player.

    This viewset provides the standard actions for viewing a specific player.

    Methods:
        get:
            Returns information on a player based on their username or ID.

    Permissions:
        - `ReadOnlyOrAuthenticated`: GET requests are public, PUT requires authentication.

    Model: `Players`

    Allowed Queries:
        - `streamexceptions`: Returns a list of users who are marked as exempt and wishing to not
        appear on streams.
            Example: `/players/all?query=streamexceptions`

    Example Response (JSON):
        ```
        {
            "id": "e8ew5p80",
            "name": "ThePackle",
            "nickname": "Packle",
            "url": "https://www.speedrun.com/user/ThePackle",
            "pfp": "pfp_link",
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
            }
        }
        ```
    """

    ALLOWED_QUERIES = {"streams"}
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Returns a specific player's information based on its ID.

        Args:
            request (Request): The request object containing the information, queries, or embeds.
            id (str): The exact ID or username of the player requesting to be returned.
                - "all" is a valid `id`, but must be used in conjunction with a query.

        Returns:
            Response: A response object containing the JSON data of a player.
        """

        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query_fields = request.GET.get("query", "").split(",")
        query_fields = [field.strip() for field in query_fields if field.strip()]
        invalid_queries = [
            field for field in query_fields if field not in self.ALLOWED_QUERIES
        ]

        if invalid_queries:
            return Response(
                {"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if id == "all":
            if "streams" in query_fields:
                players = Players.objects.only(
                    "id", "name", "twitch", "youtube", "ex_stream"
                ).filter(Q(twitch__isnull=False) | Q(youtube__isnull=False))

                return Response(
                    PlayerStreamSerializer(players, many=True).data,
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"ERROR": "'all' can only be used with a query (streams)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        player = (
            Players.objects.filter(id__iexact=id).first()
            or Players.objects.filter(name__iexact=id).first()
        )

        if player:
            return Response(PlayerSerializer(player).data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"ERROR": "Player ID or Name does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Forces the `player` object to be updated from the Speedrun.com API.

        After the `id` is given, the player's data will be normalized and their player information
        will be properly updated in the `Players` model.

        Args:
            id (str): The exact ID or player name of the player being updated.

        Returns:
            Response: A response object containing the JSON data of a speedrun.
        """

        if len(id) > 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        player = (
            Players.objects.only(
                "id",
                "name",
                "twitch",
                "youtube",
                "ex_stream",
            )
            .filter(
                Q(id__iexact=id) | Q(name__iexact=id),
            )
            .first()
        )

        if player:
            player_id = player.id

            if not request.data.get("ex_stream"):
                request.data.update({"ex_stream": player.ex_stream})

            if not request.data.get("nickname"):
                request.data.update({"nickname": player.nickname})

            serializer = PlayerSerializerPost(
                instance=player,
                data=request.data,
            )

            if serializer.is_valid():
                serializer.save()
                chain(update_player.s(player_id))()

                return Response(
                    serializer.data,
                    status=status.HTTP_202_ACCEPTED,
                )
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            try:
                chain(update_player.s(id))()

                return Response(
                    "ok",
                    status=status.HTTP_200_OK,
                )
            except AttributeError:
                return Response(
                    {"ERROR": "Player ID or name does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Exception:
                return Response(
                    {"ERROR": "An unknown error has occurred."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


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
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Returns a player's full record history based on its ID.

        This endpoint returns all full-game and individual level speedruns for a specific player.
        These runs are separated into `main_runs` and `il_runs`. The player can be looked up by
        either username or their ID. Results can include embedded data using the `embed` query
        parameter.

        Args:
            request (Request): The request object containing the information, queries, or embeds.
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


class API_Games(APIView):
    """Viewset for viewing a specific game or all games.

    This viewset provides game information, including any embeds passed into the query.

    Methods:
        get:
            Returns game information based on a game ID or slug, or all games if "all" is used.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Games`

    Allowed Embeds:
        - `categories`: Embeds all categories associated with the game into the response.
        - `levels`: Embeds all levels associated with the game into the response.
        - `platforms`: Embeds all supported platforms for the game into the response.

    Embed Example:
        `/games/thps4?embed=categories,platforms`
        `/games/all?embed=categories,levels,platforms`

    Example Response (JSON):
        ```
        {
            "id": "n2680o1p",
            "name": "Tony Hawk's Underground",
            "slug": "thug1",
            "release": "2003-10-28",
            "boxart": "https://www.speedrun.com/static/game/n2680o1p/cover?v=16c7cc8",
            "twitch": "Tony Hawk's Underground",
            "defaulttime": "ingame",
            "idefaulttime": "ingame",
            "pointsmax": 1000,
            "ipointsmax": 100
        }
        ```
    """

    ALLOWED_EMBEDS = {"categories", "levels", "platforms"}
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Returns a specific game's metadata based on its ID.

        If a game ID or slug is provided, returns that specific game's details. "All" can also be
        used to return a list for all games.Results can include embedded data using the `embed`
        query parameter.

        Args:
            request (Request): The request object containing the information, queries, or embeds.
            id (str): The exact ID of the game to be returned, or

        Returns:
            Response: A response object containing the JSON data of a game.
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

        if id == "all":
            games = Games.objects.all().order_by("release")
            return Response(
                GameSerializer(games, many=True, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )

        game = (
            Games.objects.filter(id__iexact=id).first()
            or Games.objects.filter(slug__iexact=id).first()
        )

        if game:
            return Response(
                GameSerializer(game, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Game ID or slug/abbreviation does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )


class API_Categories(APIView):
    """Viewset for viewing a specific category.

    This viewset returns information on a single category, including any embeds passed into the
    query.

    Methods:
        get:
            Returns category information based on its ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Categories`

    Allowed Embeds:
        - `game`: Embeds the game associated with the category into the response.
        - `variables`: Embeds all variables related to the category into the response.

    Embed Example:
        `/categories/123456?embed=variables`

    Example Response (JSON):
        ```
        {
            "id": "rklge08d",
            "name": "Any%",
            "type": "per-game",
            "url": "https://www.speedrun.com/thps4#Any",
            "hidden": false
        }
        ```
    """

    ALLOWED_EMBEDS = {"game", "variables"}
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Returns a single category and its metadata based on its ID.

        Parameters:
            request (Request): The request object containing the information, queries, or embeds.
            id (str): The exact ID of the category to be returned.

        Returns:
            Response: A response object containing the JSON data of a category.
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

        category = Categories.objects.filter(id__iexact=id).first()
        if category:
            return Response(
                CategorySerializer(category, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Category ID does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )


class API_Variables(APIView):
    """Viewset for viewing a specific variable.

    This viewset returns information on a single variable, including any embeds passed into the
    query.

    Methods:
        get:
            Returns variable information based on its ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Variables`

    Allowed Embeds:
        - `game`: Embeds the game associated with the variable into the response.
        - `values`: Embeds all values available for the variable into the response.

    Example:
        `/variables/123456?embed=values`

    Example Response (JSON):
        ```
        {
            "id": "ylq9qkv8",
            "name": "Version",
            "cat": "rklge08d",
            "all_cats": false,
            "scope": "full-game",
            "hidden": false
        }
        ```
    """

    ALLOWED_EMBEDS = {"game", "values"}
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Returns a single variable's metadata and values based on its ID.

        Parameters:
            request (Request): The request object containing the information, queries, or embeds.
            id (str): The exact ID of the variable to be returned.

        Returns:
            Response: A response object containing the JSON data of a variable.
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

        variables = Variables.objects.filter(id__iexact=id).first()
        if variables:
            return Response(
                VariableSerializer(variables, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Variable ID does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )


class API_Values(APIView):
    """Viewset for viewing a specific value.

    This viewset returns a value's data, including any embeds passed into the query.

    Methods:
        get:
            Returns value info based on its ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `VariableValues`

    Allowed Embeds:
        - `variable`: Embeds the full variable metadata associated with this value into the
        response.

    Embed Example:
        `/values/123456?embed=variable`

    Example Response (JSON):
        ```
        {
            "value": "5lek6rml",
            "name": "6th Gen",
            "hidden": false,
            "variable": "ylq9qkv8"
        }
        ```
    """

    ALLOWED_EMBEDS = {"variable"}
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Returns a single value's metadata and related variable based on its ID.

        Parameters:
            request (Request): The request object containing the information, queries, or embeds.
            id (str): The exact ID of the value to be returned.

        Returns:
            Response: A response object containing the JSON data of a value.
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

        value = VariableValues.objects.filter(value__iexact=id).first()

        if value:
            return Response(
                ValueSerializer(value, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Value ID does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


class API_Levels(APIView):
    """Viewset for viewing a specific level and its metadta.

    This viewset provides level metadata, including any embeds passed into the query.

    Methods:
        get:
            Returns level information based on its ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Levels`

    Allowed Embeds:
        - `game`: Embeds the game associated with the category into the response.

    Embed Example:
        `/levels/123456?embed=game`

    Example Response (JSON):
        ```
        {
            "id": "29vkxe3d",
            "name": "Slam City Jam",
            "url": "https://www.speedrun.com/thug1/Slam_City_Jam"
        }
        ```
    """

    ALLOWED_EMBEDS = {"game"}
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> HttpResponse:
        """Returns a single level based on its ID.

        Parameters:
            request (Request): The request object containing the information, queries, or embeds.
            id (str): The exact ID of the level to be returned.

        Returns:
            Response: A response object containing the JSON data of a level.
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

        levels = Levels.objects.filter(id__iexact=id).first()

        if levels:
            return Response(
                LevelSerializer(levels, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Level ID does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )


class API_Streams(APIView):
    """Viewset for viewing, creating, editing, or deleting a user's livestream status.

    This viewset provides the standard actions for creating, editing, or viewing a user's livestream
    status.

    Methods:
        get:
            Returns all currently available livestreams (no ID provided).
        post:
            Creates a new livestream entry after it passes validation.
        put:
            Updates (or creates) a new livestream entry after it passes validation.
        delete:
            Removes a livestream entry completely.

    Permissions:
        - `ReadOnlyOrAuthenticated`: GET requests are public, POST/PUT/DELETE require authentication.

    Model: `NowStreaming`

    Example Response (JSON):
        ```
        [
            {
                "streamer": {
                    "player": "TH126",
                    "twitch": "https://www.twitch.tv/TH126",
                    "youtube": "https://www.youtube.com/user/TH126"
                },
                "game": {
                    "id": "w6jgk3x6",
                    "name": "Tony Hawk's Pro Skater 3+4",
                    "twitch": "Tony Hawk's Pro Skater 3+4"
                },
                "title": "THPS3+4 Speedruns for World Record",
                "offline_ct": 1,
                "stream_time": "2025-04-17T18:00:00Z"
            }
        ]
        ```
    """
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        _,
    ) -> HttpResponse:
        """Returns a list of all available streams currently in the database."""
        return Response(
            StreamSerializer(NowStreaming.objects.all(), many=True).data,
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        """Creates a new livestream object.

        Args:
            request (Request): JSON information that must pass validation before being added.
        """
        serializer = StreamSerializerPost(data=request.data)

        streamcheck = NowStreaming.objects.filter(
            Q(streamer__name__iexact=request.data["streamer"])
            | Q(streamer__id__iexact=request.data["streamer"])
        ).exists()

        if not streamcheck:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"ERROR": "Stream from this player already exists."},
                status=status.HTTP_409_CONFLICT,
            )

    def put(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        """Updates (or creates) a livestream object.

        Args:
            request (Request): JSON information that must pass validation before being added.
        """
        stream = NowStreaming.objects.filter(
            Q(streamer__name__iexact=request.data["streamer"])
            | Q(streamer__id__iexact=request.data["streamer"])
            | Q(streamer__twitch__icontains=request.data["streamer"])
        ).first()

        serializer = StreamSerializerPost(instance=stream, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=(
                    status.HTTP_202_ACCEPTED if stream else status.HTTP_201_CREATED
                ),
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        """Removes a livestream object.

        Args:
            request (Request): JSON information that must pass validation before being deleted.
        """
        stream = NowStreaming.objects.filter(
            Q(streamer__name__iexact=request.data["streamer"])
            | Q(streamer__id__iexact=request.data["streamer"])
            | Q(streamer__twitch__icontains=request.data["streamer"])
        ).first()

        if stream:
            stream.delete()
            return Response("ok", status=status.HTTP_200_OK)
        else:
            return Response(
                {"ERROR": f"{request.data['streamer']} is not in the model."},
                status=status.HTTP_400_BAD_REQUEST,
            )
