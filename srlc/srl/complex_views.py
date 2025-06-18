from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render

from .leaderboard_view import Leaderboard
from .models import Games, NowStreaming, Players, Runs


def PlayerProfile(request, name):
    """View that gathers all of the information on a player before passing it to a template.

    This view processes practically all of the information about a player in the `Players` model.
    This includes information about all fo their speedruns, metadata (to include social media),
    and additional statistics about their placements within the community.

    Args:
        name (str): The display name of the player being returned.

    Returns:
        render (request, template, context): Request is sent to a specific template, which includes
        the context needed to dynamically generate the webpage.
    """
    try:
        player = Players.objects.get(name__iexact=name)
    except Players.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except Exception:
        return render(request, "srl/500.html")

    games = Games.objects.only("id", "name", "release", "slug").all().order_by("name")

    main_runs = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"])
        .select_related("game", "player")
        .only(
            "id",
            "game__id",
            "game__name",
            "game__release",
            "subcategory",
            "player__id",
            "player__name",
            "player__awards",
            "time",
            "time_secs",
            "timenl",
            "timenl_secs",
            "timeigt",
            "timeigt_secs",
            "video",
            "arch_video",
            "url",
            "points",
            "place",
            "v_date",
            "vid_status",
        )
        .main()
        .filter(Q(player_id=player.id) | Q(player2_id=player.id))
        .annotate(o_date=TruncDate("v_date"))
    )

    il_runs = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"])
        .select_related("game", "player", "level")
        .only(
            "id",
            "game__id",
            "game__name",
            "game__release",
            "subcategory",
            "level__id",
            "level__name",
            "player__id",
            "player__name",
            "player__awards",
            "time",
            "time_secs",
            "timenl",
            "timenl_secs",
            "timeigt",
            "timeigt_secs",
            "video",
            "arch_video",
            "url",
            "points",
            "place",
            "v_date",
            "vid_status",
        )
        .il()
        .filter(player_id=player.id)
        .annotate(o_date=TruncDate("v_date"))
    )

    total_runs = len(main_runs) + len(il_runs)

    main_runs = main_runs.filter(obsolete=False)
    il_runs = il_runs.filter(obsolete=False)

    # hidden_cats   = VariableValues.objects.filter(hidden=True)
    # main_runs     = main_runs.exclude(values__in=hidden_cats)

    # For co-op categories, runners could be player 1 or player 2 and it
    # would count as two different runs.
    # This would remove the slower of the two and not count it towards points.
    if main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)"):
        exclude = (
            main_runs.filter(subcategory__contains="Co-Op")
            .order_by("-points")
            .values("id")
        )[1:]
        main_runs = main_runs.exclude(id__in=exclude)

    main_points = sum(run.points for run in main_runs)
    il_points = sum(run.points for run in il_runs)
    total_points = main_points + il_points

    leaderboard = Leaderboard(request, 3)
    u_game_names = games.order_by("release").values_list("name", "release")

    if isinstance(leaderboard, tuple):
        for index, item in enumerate(leaderboard[0]):
            if item["player"] == player.name:
                player_rank = index + 1
                break

        for index, item in enumerate(leaderboard[1]):
            if item["player"] == player.name:
                main_rank = index + 1
                break
            else:
                main_rank = 0

        for index, item in enumerate(leaderboard[2]):
            if item["player"] == player.name:
                il_rank = index + 1
                break
            else:
                il_rank = 0

        player_count = len(leaderboard[0])
        main_count = len(leaderboard[1])
        il_count = len(leaderboard[2])

        award_set = []
        for award in player.awards.all():
            award_set.append([award.name, award.image.name.rsplit("/")[-1]])

        context = {
            "player": player,
            "main_runs": main_runs,
            "il_runs": il_runs,
            "main_points": main_points,
            "il_points": il_points,
            "total_points": total_points,
            "total_runs": total_runs,
            "player_rank": player_rank,
            "main_rank": main_rank,
            "il_rank": il_rank,
            "player_count": player_count,
            "main_count": main_count,
            "il_count": il_count,
            "unique_game_names": u_game_names,
            "awards": award_set,
        }
        return render(request, "srl/player_profile.html", context)


def PlayerHistory(request, name):
    """View that gathers all of the information on a player's speedrun history.

    This view processes practically all of the speedruns within the database belonging to the
    specified player. This includes obsolete speedruns (those that are no longer ranked or have a
    worse time versus their personal best).

    Args:
        name (str): The display name of the player being returned.

    Returns:
        render (request, template, context): Request is sent to a specific template, which includes
        the context needed to dynamically generate the webpage.
    """
    try:
        player = Players.objects.get(name__iexact=name)
    except Players.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except Exception:
        return render(request, "srl/500.html")

    games = Games.objects.all().order_by("name")
    main_runs = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"])
        .main()
        .filter(Q(player_id=player.id) | Q(player2_id=player.id))
        .annotate(o_date=TruncDate("date"))
        .order_by("-o_date")
    )

    il_runs = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"])
        .il()
        .filter(player_id=player.id)
        .annotate(o_date=TruncDate("date"))
        .order_by("subcategory")
    )

    # For co-op, runners could be player 1 or 2 and it would count as two runs.
    # This would remove the slower of the two and not count it towards points.
    if main_runs.filter(subcategory__contains="Co-Op"):
        exclude = (
            main_runs.filter(subcategory__contains="Co-Op")
            .order_by("-points")
            .values("id")
        )[1:]
        main_runs = main_runs.exclude(id__in=exclude)

    award_set = []
    for award in player.awards.all():
        award_set.append([award.name, award.image.name.rsplit("/")[-1]])

    u_game_names = games.order_by("release").values_list("name", "release")

    context = {
        "player": player,
        "main_runs": main_runs,
        "il_runs": il_runs,
        "unique_game_names": u_game_names,
    }

    return render(request, "srl/player_profile.html", context)


def FG_Leaderboard(request):
    """View that displays a leaderboard the combined points for a runner across all games.

    This view gathers the combined point values of all runners across all games and generates a
    dynamic webpage (to include searching).

    Returns:
        render (request, template, context): Request is sent to a specific template, which includes
        the context needed to dynamically generate the webpage.
    """
    leaderboard = Leaderboard(request, 1)

    paginator = Paginator(leaderboard, 50)
    page_number = request.GET.get("page")
    leaderboard_page = paginator.get_page(page_number)
    rank_start = leaderboard_page.start_index()

    for item in leaderboard_page:
        item["rank"] = rank_start
        rank_start += 1

    context = {"leaderboard": leaderboard_page}

    return render(request, "srl/leaderboard.html", context)


def IL_Leaderboard(request, game_slug):
    """View that displays a leaderboard the combined points for a runner for a specific IL game.

    This view gathers the combined point values of all runners across for a specific game's ILs
    and generates a dynamic webpage (to include searching).

    Args:
        game_slug (str): The slug (abbreviation) for a game from the `Games` model.

    Returns:
        render (request, template, context): Request is sent to a specific template, which includes
        the context needed to dynamically generate the webpage.
    """
    try:
        game = Games.objects.get(slug=game_slug)
    except Games.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except Exception:
        return render(request, "srl/500.html")

    leaderboard = Leaderboard(request, 2, game_slug)

    paginator = Paginator(leaderboard, 50)
    page_number = request.GET.get("page")
    leaderboard_page = paginator.get_page(page_number)
    rank_start = leaderboard_page.start_index()

    for item in leaderboard_page:
        item["rank"] = rank_start
        rank_start += 1

    context = {
        "leaderboard": leaderboard_page,
        "game_name": game.name,
        "game_slug": game_slug,
    }

    return render(request, "srl/leaderboard.html", context)


def search_leaderboard(request):
    """Used in cases when a leaderboard is paginated; this will allow you to look up a runner"""
    search_query = request.GET.get("search", "")
    players_all = Players.objects.all()
    players = Players.objects.filter(name__icontains=search_query)

    leaderboard_all = []
    leaderboard = []

    for player in players_all:
        main_points = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .main()
            .filter(obsolete=False, points__gt=0)
            .filter(Q(player_id=player.id) | Q(player2_id=player.id))
            .aggregate(total_points=Sum("points"))
        )["total_points"]

        il_points = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .il()
            .filter(obsolete=False, player_id=player.id, points__gt=0)
            .aggregate(total_points=Sum("points"))
        )["total_points"]

        all_points = main_points + il_points

        if player.countrycode:
            countrycode = player.countrycode.id
        else:
            countrycode = None

        leaderboard_all.append(
            {"player": player, "countrycode": countrycode, "total_points": all_points}
        )

    leaderboard_all = sorted(
        leaderboard_all, key=lambda x: x["total_points"], reverse=True
    )

    for rank, item in enumerate(leaderboard_all, start=1):
        if item["player"].name in players.values_list("name", flat=True):

            if all_points > 0:
                leaderboard_item = {
                    "player": item["player"].name,
                    "total_points": item["total_points"],
                    "countrycode": item["countrycode"],
                    "rank": rank,
                }
                leaderboard.append(leaderboard_item)

    return JsonResponse(leaderboard, safe=False)


def ILGameLeaderboard(request, slug, category=None):
    """View that displays a leaderboard for a specific game that supports individual levels.

    This view gathers the speedruns and players for a specified game and ranks them in a leaderboard
    that includes their points, when they achieved the run, and other metadata.

    Args:
        slug (str): The slug (abbreviation) for a game from the `Games` model.
            - When set to `thps4`, it will render an "extended" leaderboard.
        category (str): None by default. Currently unused.

    Returns:
        render (request, template, context): Request is sent to a specific template, which includes
        the context needed to dynamically generate the webpage.
    """
    try:
        game = Games.objects.filter(slug__iexact=slug)
        players = Players.objects.all()
        ilruns = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .il()
            .filter(game_id=game[0].id, points__gt=0, obsolete=False)
        )
    except Games.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except Exception:
        return render(request, "srl/500.html")

    if "thps4/ils" in request.path_info:
        lb_output = Leaderboard(request, 4, slug)

        if isinstance(lb_output, tuple):
            wr_count = lb_output[0]
            old_runs = lb_output[1]
    else:
        wr_count = None
        old_runs = None

    runs_list = []

    if category is None:
        il_categories = sorted(
            [
                subcategory[0]
                for subcategory in ilruns.values_list("subcategory").distinct()
            ]
        )

        for run in ilruns:
            if run.player is not None:
                for player in [run.player.id]:
                    if player is not None:
                        player = players.filter(id=player)[0]
                        defaulttime = run.game.idefaulttime

                        if defaulttime == "realtime":
                            run_time = run.time
                        elif defaulttime == "realtime_noloads":
                            run_time = run.timenl
                        elif defaulttime == "ingame":
                            run_time = run.timeigt

                        # Sometimes the defaulttime of a game doesn't line up.
                        # This code will iterate through the time, timenl and timeigt variables to
                        # find one that does not equal 0.
                        # Obviously there will be niche scenarios where one is
                        # more preferred over the other, but will revist this
                        if run_time == "0":
                            times = [
                                (run.time, "realtime"),
                                (run.timenl, "realtime_noloads"),
                                (run.timeigt, "ingame"),
                            ]

                            run_time, defaulttime = next(
                                ((time, label) for time, label in times if time != "0"),
                                ("0", None),
                            )

                        cc = (
                            player.countrycode.id
                            if player and player.countrycode
                            else None
                        )

                        cc_name = (
                            player.countrycode.name
                            if player and player.countrycode
                            else None
                        )

                        run_add = {
                            "player": player.name if player else "Anonymous",
                            "nickname": player.nickname if player.nickname else None,
                            "countrycode": cc,
                            "countryname": cc_name,
                            "place": run.place,
                            "defaulttime": defaulttime,
                            "time": run_time,
                            "points": run.points,
                            "date": run.date,
                            "subcategory": run.subcategory,
                            "url": run.url,
                            "video": run.video,
                            "other_video": run.arch_video,
                        }

                    runs_list.append(run_add)

            leaderboard = sorted(runs_list, key=lambda x: x["place"], reverse=False)

    context = {
        "players": players,
        "runs": leaderboard,
        "wr_count": wr_count,
        "old_runs": old_runs,
        "subcategories": il_categories,
        "game_slug": slug,
        "selected_category": category,
    }

    if "thps4/ils" in request.path_info:
        return render(request, "srl/il_leaderboard_expanded.html", context)
    else:
        return render(request, "srl/il_leaderboard.html", context)


def GameLeaderboard(request, slug, category=None):
    """View that displays a leaderboard for a specific game that supports full game speedruns.

    This view gathers the `Runs` and `Players` for a specified game and ranks them in a leaderboard
    that includes their points, when they achieved the run, and other metadata.

    Args:
        slug (str): The slug (abbreviation) for a game from the `Games` model.
        category (str): None by default. Currently unused.

    Returns:
        render (request, template, context): Request is sent to a specific template, which includes
        the context needed to dynamically generate the webpage.
    """
    try:
        game = Games.objects.get(slug=slug)
        players = Players.objects.all()
        mainruns = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .main()
            .filter(game_id=game.id, points__gt=0, obsolete=False)
        )
        # hidden_cats = VariableValues.objects.filter(hidden=True)
    except Games.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except Exception:
        return render(request, "srl/500.html")

    runs_list = []

    if category is None:
        categories = sorted(
            [
                subcategory[0]
                for subcategory in mainruns.values_list("subcategory").distinct()
            ]
        )

        for run in mainruns:
            defaulttime = game.defaulttime

            if run.player is not None and run.player.id:
                player = players.get(id=run.player.id)
            else:
                player = "Anonymous"

            if run.player2 is not None and run.player2.id:
                player2 = players.get(id=run.player2.id)
            else:
                player2 = "Anonymous"

            if defaulttime == "realtime":
                run_time = run.time
            elif defaulttime == "realtime_noloads":
                run_time = run.timenl
            elif defaulttime == "ingame":
                run_time = run.timeigt

            # Sometimes the defaulttime of a game doesn't line up.
            # This code will iterate through the time, timenl and timeigt variables to
            # find one that does not equal 0.
            # Obviously there will be niche scenarios where one is
            # more preferred over the other, but will revist this
            if run_time == "0":
                times = [
                    (run.time, "realtime"),
                    (run.timenl, "realtime_noloads"),
                    (run.timeigt, "ingame"),
                ]

                run_time, defaulttime = next(
                    ((time, label) for time, label in times if time != "0"), ("0", None)
                )

            run_add = {
                "player": player.name if player != "Anonymous" else player,
                "nickname": player.nickname if player != "Anonymous" else None,
                "place": run.place,
                "defaulttime": defaulttime,
                "time": run_time,
                "points": run.points,
                "date": run.date,
                "subcategory": run.subcategory,
                "url": run.url,
                "video": run.video,
                "other_video": run.arch_video,
            }

            if player != "Anonymous":
                cc = player.countrycode.id if player.countrycode is not None else None

                cc_name = (
                    player.countrycode.name if player.countrycode is not None else None
                )

                run_add.update(
                    {
                        "countrycode": cc,
                        "countryname": cc_name,
                    }
                )

            if "co-op" in run.subcategory.lower():
                player2_name = player2.name if player2 != "Anonymous" else "Anonymous"
                player2_nn = player2.nickname if player2 != "Anonymous" else None

                player2_cc = (
                    player2.countrycode.id
                    if player2 != "Anonymous" and player2.countrycode
                    else None
                )

                player2_cn = (
                    player2.countrycode.name
                    if player2 != "Anonymous" and player2.countrycode
                    else None
                )

                run_add.update(
                    {
                        "player2": player2_name,
                        "player2nickname": player2_nn,
                        "countrycode2": player2_cc,
                        "countryname2": player2_cn,
                    }
                )

            runs_list.append(run_add)

        leaderboard = sorted(runs_list, key=lambda x: x["place"], reverse=False)

    context = {
        "players": players,
        "runs": leaderboard,
        "subcategories": categories,
        "game_slug": slug,
        "selected_category": category,
    }

    return render(request, "srl/il_leaderboard.html", context)


def MainPage(request):
    """View that displays the main page for the entire website/project.

    This view gathers the world records, most recent speedruns/world records, and those currently
    marked as streaming, then returns it to be dynamically rendered.

    Returns:
        render (request, template, context): Request is sent to a specific template, which includes
        the context needed to dynamically generate the webpage.
    """
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
    run_list = []
    wrs_data = []
    runs_data = []

    for game in exempt_games:
        exclusion_filter |= Q(game__name__icontains=game)

    streamers = NowStreaming.objects.all()
    runs = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"], obsolete=True)
        .exclude(exclusion_filter)
        .main()
        .filter(place=1, subcategory__in=subcategories)
        .order_by("-subcategory")
        .annotate(o_date=TruncDate("date"))
    )

    # Next blocks of code are checks to group runs together within the same game and subcategory.
    # In some circumstances, world records are ties.
    # This makes it so it display properly on the main page (as opposed to two rows,
    # they are on a combined row).
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
                record["players"].append(
                    {"player": run.player, "url": run.url, "date": run.o_date}
                )

    # Sorts runs within the run_list by the game release date, oldest first.
    run_list = sorted(grouped_runs, key=lambda x: x["game"].release, reverse=False)

    # Sometimes v_date (verify_date) is null; this can happen if the runs on a leaderboard are
    # super old. Essentially grabs the newest 5 runs for WRs (place=1) and PBs (place>1).
    wrs = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"])
        .select_related("game", "player")
        .only(
            "id",
            "game__slug",
            "player__name",
            "player__nickname",
            "subcategory",
            "time",
            "time_secs",
            "timenl",
            "timenl_secs",
            "timeigt",
            "timeigt_secs",
            "url",
        )
        .filter(place=1, obsolete=False, v_date__isnull=False)
        .order_by("-v_date")
    )[:5]

    pbs = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"])
        .select_related("game", "player")
        .only(
            "id",
            "game__slug",
            "player__name",
            "player__nickname",
            "subcategory",
            "time",
            "time_secs",
            "timenl",
            "timenl_secs",
            "timeigt",
            "timeigt_secs",
            "url",
        )
        .filter(place__gt=1, obsolete=False, v_date__isnull=False)
        .order_by("-v_date")
    )[:5]

    for pb in pbs:
        runs_data.append(pb)

    for wr in wrs:
        wrs_data.append(wr)

    context = {
        "streamers": streamers,
        "runs": run_list,
        "new_runs": runs_data,
        "new_wrs": wrs_data,
    }

    return render(request, "srl/main.html", context)
