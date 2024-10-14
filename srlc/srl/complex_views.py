from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Sum,Q,Case,When,Value,CharField,Max,F
from .models import GameOverview,Players,Categories,MainRuns,ILRuns,NewRuns,NewWRs,CountryCodes,VariableValues

def PlayerProfile(request,name):
    try:
        player          = Players.objects.get(name__iexact=name)
    except Players.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")
    
    unique_game_names   = set()
    games               = GameOverview.objects.all().order_by("name")
    categories          = Categories.objects.all()
    main_runs           = MainRuns.objects.filter(Q(playerid=player.id) | Q(playerid2=player.id)).filter()
    il_runs             = ILRuns.objects.filter(playerid=player.id).filter()
    country             = CountryCodes.objects.filter(id=player.countrycode).values("name")[0]["name"]
    total_runs          = len(main_runs) + len(il_runs)
    
    main_runs           = main_runs.filter(obsolete=False)
    il_runs             = il_runs.filter(obsolete=False)

    hidden_cats         = VariableValues.objects.filter(hidden=True).values_list("valueid")
    main_runs           = main_runs.exclude(values__in=hidden_cats)

    if main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)"):
        exclude = main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)").order_by("-points").values("id")[1:]
        main_runs = main_runs.exclude(id__in=exclude)

    main_points         = sum(run.points for run in main_runs)
    il_points           = sum(run.points for run in il_runs)
    total_points        = main_points + il_points
    
    leaderboard         = Leaderboard(request,3)
    unique_game_names   = games.order_by("release").values_list("name","release")

    if isinstance(leaderboard,tuple):
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
        main_count   = len(leaderboard[1])
        il_count     = len(leaderboard[2])

        award_set = []
        for award in player.awards.all():
            award_set.append([award.name,award.image.name.rsplit("/")[-1]])

        context = {
            "player"            : player,
            "games"             : games,
            "categories"        : categories,
            "main_runs"         : main_runs,
            "il_runs"           : il_runs,
            "main_points"       : main_points,
            "il_points"         : il_points,
            "total_points"      : total_points,
            "total_runs"        : total_runs,
            "player_rank"       : player_rank,
            "main_rank"         : main_rank,
            "il_rank"           : il_rank,
            "player_count"      : player_count,
            "main_count"        : main_count,
            "il_count"          : il_count,
            "unique_game_names" : unique_game_names,
            "awards"            : award_set,
            "country"           : country
        }
        return render(request, "srl/player_profile.html", context)

def Leaderboard(request,profile=None,game=None):
    players_all     = Players.objects.all()
    games_all       = GameOverview.objects.all()
    main_runs_all   = MainRuns.objects.exclude(place=0)
    il_runs_all     = ILRuns.objects.exclude(place=0)

    leaderboard     = []
    fg_leaderboard  = []
    il_leaderboard  = []

    for player in players_all:
        if profile == 1:
            main_runs = main_runs_all.filter(Q(playerid=player.id) | Q(playerid2=player.id))
            if main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)"):
                exclude = main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)").order_by("-points").values("id")[1:]

                main_runs = main_runs.exclude(id__in=exclude)

            main_points = main_runs.aggregate(total_points=Sum("points"))["total_points"] or 0

            leaderboard.append({
                "player"        : player.name,
                "nickname"      : player.nickname,
                "countrycode"   : player.countrycode,
                "total_points"  : main_points
            })

        elif profile == 2:
            game_id   = games_all.get(abbr=game).id
            il_runs   = il_runs_all.filter(playerid=player.id,gameid=game_id)
            il_wrs    = il_runs.filter(place=1).count() or 0
            il_points = il_runs.aggregate(total_points=Sum("points"))["total_points"] or 0
            
        elif profile == 4:
            game_id = games_all.get(abbr=game,points__gt=0).id
            il_runs = il_runs_all.filter(gameid=game_id).filter(points__gt=0)
            total_points = il_runs.aggregate(total_points=Sum("points"))["total_points"] or 0

            if total_points > 0:
                leaderboard.append({
                    "player"        : player.name,
                    "nickname"      : player.nickname,
                    "countrycode"   : player.countrycode,
                    "game"          : game,
                    "total_points"  : total_points
                })
        elif profile == 5:
            game_id     = games_all.get(abbr=game).id
            il_runs     = il_runs_all.filter(playerid=player.id,gameid=game_id)
            il_wrs      = il_runs.filter(place=1).count() or 0
        
            if il_wrs > 1:
                il_leaderboard.append({
                    "player"        : player.name,
                    "nickname"      : player.nickname,
                    "countrycode"   : player.countrycode,
                    "il_wrs"        : il_wrs
                })     
        else:
            main_runs = main_runs_all.filter(Q(playerid=player.id) | Q(playerid2=player.id))
            if main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)"):
                exclude = main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)").order_by("-points").values("id")[1:]

                main_runs = main_runs.exclude(id__in=exclude)

            main_points = main_runs.aggregate(total_points=Sum("points"))["total_points"] or 0
            il_points = il_runs_all.filter(playerid=player.id).aggregate(total_points=Sum("points"))["total_points"] or 0

            total_points = main_points + il_points

            leaderboard.append({
                "player"        : player.name,
                "nickname"      : player.nickname,
                "countrycode"   : player.countrycode,
                "total_points"  : total_points
            })

        if profile in [2,3]:
            if profile == 3:
                if main_points > 0:
                    fg_leaderboard.append({
                        "player"        : player.name,
                        "nickname"      : player.nickname,
                        "countrycode"   : player.countrycode,
                        "total_points"  : main_points
                    })
            if profile in [2,3]:
                if il_points > 0:
                    il_leaderboard.append({
                        "player"        : player.name,
                        "nickname"      : player.nickname,
                        "countrycode"   : player.countrycode,
                        "total_points"  : il_points
                    })            

    leaderboard         = sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)
    if profile == 1:
        fg_leaderboard  = sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)

        return fg_leaderboard
    elif profile == 2:
        il_leaderboard  = sorted(il_leaderboard, key=lambda x: x["total_points"], reverse=True)
        
        return il_leaderboard
    elif profile == 3:
        fg_leaderboard  = sorted(fg_leaderboard, key=lambda x: x["total_points"], reverse=True)
        il_leaderboard  = sorted(il_leaderboard, key=lambda x: x["total_points"], reverse=True)

        return leaderboard,fg_leaderboard,il_leaderboard
    elif profile == 4:
        leaderboard     = sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)

        rank_start = 1
        for rank, item in enumerate(leaderboard, start=rank_start):
            item["rank"] = rank

        return leaderboard
    elif profile == 5:
        il_wr_counts    = sorted(il_leaderboard, key=lambda x: x["il_wrs"], reverse=True)
        il_runs_old     = il_runs_all.filter(gameid=game_id,points=100).exclude(levelid="rdnoro6w").order_by("date").values_list("subcategory","time","date")[:10]

        return il_wr_counts,il_runs_old
    else:
        paginator           = Paginator(leaderboard, 50)
        page_number         = request.GET.get("page")
        leaderboard_page    = paginator.get_page(page_number)

        rank_start = leaderboard_page.start_index()
        for item in leaderboard_page:
            item["rank"] = rank_start
            rank_start += 1

        context = {
            "leaderboard": leaderboard_page
        }

        return render(request, "srl/leaderboard.html", context)
    
def FG_Leaderboard(request):
    leaderboard         = Leaderboard(request,1)

    if isinstance(leaderboard,tuple):
        paginator           = Paginator(leaderboard, 50)
        page_number         = request.GET.get("page")
        leaderboard_page    = paginator.get_page(page_number)
        rank_start          = leaderboard_page.start_index()

        for item in leaderboard_page:
            item["rank"] = rank_start
            rank_start += 1

        context = {
            "leaderboard": leaderboard_page
        }

        return render(request, "srl/leaderboard.html", context)

def IL_Leaderboard(request,game_abbr):
    try:
        game = GameOverview.objects.get(abbr=game_abbr)
    except GameOverview.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")
    
    leaderboard         = Leaderboard(request,2,game_abbr)

    if isinstance(leaderboard,tuple):
        paginator           = Paginator(leaderboard, 50)
        page_number         = request.GET.get("page")
        leaderboard_page    = paginator.get_page(page_number)
        rank_start          = leaderboard_page.start_index()

        for item in leaderboard_page:
            item["rank"] = rank_start
            rank_start += 1

        context = {
            "leaderboard"   : leaderboard_page,
            "game_name"     : game.name,
            "game_abbr"     : game_abbr
        }

        return render(request, "srl/leaderboard.html", context)

def search_leaderboard(request):
    search_query        = request.GET.get("search", "")
    players_all         = Players.objects.all()
    players             = Players.objects.filter(name__icontains=search_query)

    leaderboard_all     = []
    leaderboard         = []
    
    for player in players_all:
        main_points     = MainRuns.objects.filter(Q(playerid=player.id) | Q(playerid2=player.id)).filter(points__gt=0).aggregate(total_points=Sum("points"))["total_points"] or 0
        il_points       = ILRuns.objects.filter(playerid=player.id).filter(points__gt=0).aggregate(total_points=Sum("points"))["total_points"] or 0
        total_points    = main_points + il_points

        leaderboard_all.append({
            "player"        : player,
            "countrycode"   : player.countrycode,
            "total_points"  : total_points
        })

    leaderboard_all     = sorted(leaderboard_all, key=lambda x: x["total_points"], reverse=True)

    for rank, item in enumerate(leaderboard_all, start=1):
        if item["player"].name in players.values_list("name", flat=True):

            if total_points > 0:
                leaderboard_item = {
                    "player"        : item["player"].name,
                    "total_points"  : item["total_points"],
                    "countrycode"   : item["countrycode"],
                    "rank"          : rank
                }
                leaderboard.append(leaderboard_item)

    return JsonResponse(leaderboard, safe=False)

def OL_Leaderboard(request):
    countries       = CountryCodes.objects.all()
    players         = Players.objects.all()
    p_countries     = players.filter(countrycode__isnull=False).values_list("countrycode",flat=True).distinct()
    country_filter  = countries.filter(id__in=p_countries).order_by("id")
    main_runs       = MainRuns.objects.filter(points__gt=0)

    runs_list = []

    for country in country_filter:
        player_filter   = players.filter(countrycode=country.id).values_list("id",flat=True)
        run_filter      = main_runs.filter(playerid__in=player_filter).filter(place__in=[1,2,3])

        country_output = {
            "countrycode"   : country.id,
            "countryname"   : country.name,
            "first_places"  : run_filter.filter(place=1).count(),
            "second_places" : run_filter.filter(place=2).count(),
            "third_places"  : run_filter.filter(place=3).count()
        }

        runs_list.append(country_output)

    olympics = sorted(runs_list, key=lambda x: x["first_places"], reverse=True)

    context = {
        "olympics": olympics
    }

    return render(request, "srl/ol_leaderboard.html", context)
    
def RG_Leaderboard(request):
    countries       = CountryCodes.objects.all()
    players         = Players.objects.all()
    p_countries     = players.filter(countrycode__isnull=False).values_list("countrycode",flat=True).distinct()
    null_countries  = players.filter(countrycode__isnull=True)
    country_filter  = countries.filter(id__in=p_countries).order_by("name")
    main_runs       = MainRuns.objects.filter(points__gt=0)
    il_runs         = ILRuns.objects.filter(points__gt=0)

    runs_list = []

    for country in p_countries:
        country_players = players.filter(countrycode=country)

        for player in country_players:
            main_points     = main_runs.filter(Q(playerid=player.id) | Q(playerid2=player.id)).aggregate(total_points=Sum("points"))["total_points"] or 0
            il_points       = il_runs.filter(playerid=player.id).aggregate(total_points=Sum("points"))["total_points"] or 0
            total_points    = main_points + il_points

            try:
                countrycode = player.countrycode
                countryname = countries.filter(id=country).values("name")[0]["name"]
            except:
                countrycode = ""
                countryname = "Unknown"

            leaderboard_item = {
                "player"        : player.name,
                "nickname"      : player.nickname,
                "countrycode"   : countrycode,
                "countryname"   : countryname,
                "points"        : total_points
            }

            runs_list.append(leaderboard_item)

    for player in null_countries:
        main_points     = main_runs.filter(Q(playerid=player.id) | Q(playerid2=player.id)).aggregate(total_points=Sum("points"))["total_points"] or 0
        il_points       = il_runs.filter(playerid=player.id).aggregate(total_points=Sum("points"))["total_points"] or 0
        total_points    = main_points + il_points

        leaderboard_item = {
            "player"        : player.name,
            "nickname"      : player.nickname,
            "countrycode"   : "",
            "countryname"   : "Unknown",
            "points"        : total_points
        }

        runs_list.append(leaderboard_item)

    leaderboard = sorted(runs_list, key=lambda x: x["points"], reverse=True)

    context = {
        "players"       : players,
        "countries"     : country_filter,
        "leaderboard"   : leaderboard
    }

    return render(request, "srl/rg_leaderboard.html", context)


def GameSelection(request):
    games       = GameOverview.objects.all().order_by("name")
    categories  = Categories.objects.all()
    main_runs   = MainRuns.objects.all()
    il_runs     = ILRuns.objects.all()

    context = {
        "games"         : games,
        "categories"    : categories,
        "main_runs"     : main_runs,
        "il_runs"       : il_runs,
    }
    return render(request, "srl/game_selection.html", context)

def ILGameLeaderboard(request,abbr,category=None):
    if "thps4/ils" in request.path_info:
        lb_output   = Leaderboard(request,5,abbr)

        if isinstance(lb_output,tuple):
            wr_count    = lb_output[0]
            old_runs    = lb_output[1]
    else:
        wr_count    = None
        old_runs    = None

    try:
        game        = GameOverview.objects.filter(abbr=abbr)
        players     = Players.objects.all()
        ilruns      = ILRuns.objects.filter(gameid=game[0].id).filter(points__gt=0)
    except GameOverview.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")

    runs_list    = []
    
    if category == None:
        il_categories = [subcategory[0] for subcategory in ilruns.values_list("subcategory").distinct()]

        for run in ilruns:
            if run.player is not None:
                for player in [run.player.id]:
                    if player != None:
                        player = players.filter(id=player)[0]

                        run_add = {
                            "player"        : player.name,
                            "nickname"      : player.nickname,
                            "countrycode"   : player.countrycode,
                            "place"         : run.place,
                            "defaulttime"   : game[0].defaulttime,
                            "time"          : run.time,
                            "points"        : run.points,
                            "date"          : run.date,
                            "subcategory"   : run.subcategory,
                            "url"           : run.url
                        }
                    else:
                        run_add = {
                            "player"        : "Anonymous",
                            "nickname"      : None,
                            "countrycode"   : None,
                            "place"         : run.place,
                            "defaulttime"   : game[0].defaulttime,
                            "time"          : run.time,
                            "points"        : run.points,
                            "date"          : run.date,
                            "subcategory"   : run.subcategory,
                            "url"           : run.url
                        }

                    runs_list.append(run_add)

            leaderboard = sorted(runs_list, key=lambda x: x["points"], reverse=True)

    context = {
        "players"           : players,
        "runs"              : leaderboard,
        "wr_count"          : wr_count,
        "old_runs"          : old_runs,
        "subcategories"     : il_categories,
        "game_abbr"         : abbr,
        "selected_category" : category
    }

    if "thps4/ils" in request.path_info:
        return render(request, "srl/il_leaderboard_expanded.html", context)
    else:
        return render(request, "srl/il_leaderboard.html", context)

def GameLeaderboard(request,abbr,category=None):
    try:
        game        = GameOverview.objects.filter(abbr=abbr)
        players     = Players.objects.all()
        mainruns    = MainRuns.objects.filter(gameid=game[0].id).filter(points__gt=0)
        hidden_cats = VariableValues.objects.filter(hidden=True).values_list("valueid")
    except GameOverview.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")
    
    runs_list = []

    if category == None:
        mainruns    = mainruns.exclude(values__in=hidden_cats)

        categories  = [subcategory[0] for subcategory in mainruns.values_list("subcategory").distinct()]

        for run in mainruns:    
            if run.player is not None and run.player.id:
                player = players.filter(id=run.player.id)[0]
            else:
                player = "Anonymous"

            if run.player2 is not None and run.player2.id:
                player2 = players.filter(id=run.player2.id)[0]
            else:
                player2 = "Anonymous"

            if player != "Anonymous":
                run_add = {
                    "player"        : player.name,
                    "nickname"      : player.nickname,
                    "countrycode"   : player.countrycode,
                    "place"         : run.place,
                    "defaulttime"   : game[0].defaulttime,
                    "time"          : run.time,
                    "points"        : run.points,
                    "date"          : run.date,
                    "subcategory"   : run.subcategory,
                    "url"           : run.url
                }

                if run.subcategory == "Classic Mode - Co-Op (Normal)":
                    if player2 != "Anonymous":
                        run_add.update({"player2":player2.name})
                        run_add.update({"player2nickname":player2.nickname})
                        run_add.update({"countrycode2":player2.countrycode})
                    else:
                        run_add.update({"player2":"Anonymous"})
                        run_add.update({"player2nickname":None})
                        run_add.update({"countrycode2":None})
            else:
                run_add = {
                    "player"        : player,
                    "countrycode"   : None,
                    "place"         : run.place,
                    "defaulttime"   : game[0].defaulttime,
                    "time"          : run.time,
                    "points"        : run.points,
                    "date"          : run.date,
                    "subcategory"   : run.subcategory,
                    "url"           : run.url
                }

            runs_list.append(run_add)

        
        leaderboard = sorted(runs_list, key=lambda x: x["points"], reverse=True)

    context = {
        "players"               : players,
        "runs"                  : leaderboard,
        "subcategories"         : categories,
        "game_abbr"             : abbr,
        "selected_category"     : category
    }

    return render(request, "srl/il_leaderboard.html", context)

def MainPage(request):
    subcategories = ["Any%", "Any% (6th Gen)", "100%", "Any% (No Major Glitches)", "All Goals & Golds (No Major Glitches)", "All Goals & Golds (All Careers)", "All Goals & Golds (6th Gen)", "Any% (Beginner)", "100% (NSR)", "Story (Easy, NG+)", "100% (NG)", "Classic (Normal, NG+)", "Story Mode (Easy, NG+)", "Classic Mode (Normal)", "Any% (360/PS3)", "100% (360/PS3)"]
    #runs         = MainRuns.objects.filter(place=1,points__gt=0,subcategory__in=subcategories)

    runs = MainRuns.objects.filter(place=1,subcategory__in=subcategories).order_by(
        Case(*[When(subcategory=subcategories, then=Value(pos)) for pos, subcategories in enumerate(subcategories)], output_field=CharField())
    )

    run_list      = []
    wrs_data      = []
    runs_data     = []
    exempt_games  = ["GBA","PSP","GBC","Category Extensions","Remix","Sk8land","HD","2x"]

    for run in runs:
        if run.game and run.player:
            gamename = run.game.name

            if not any(game in gamename for game in exempt_games):
                run_list.append(run)

    run_list = sorted(run_list, key=lambda x: x.game.release, reverse=False)

    pbs = NewRuns.objects.order_by("-timeadded")[:5]
    wrs = NewWRs.objects.order_by("-timeadded")[:5]
    
    for pb in pbs:
        try: run = MainRuns.objects.get(id=pb.id)
        except: run = ILRuns.objects.get(id=pb.id)
        
        if run:
            runs_data.append(run)

    for wr in wrs:
        try: run = MainRuns.objects.get(id=wr.id)
        except: run = ILRuns.objects.get(id=wr.id)

        if run:
            wrs_data.append(run)

    context = {
        "runs"      : run_list,
        "new_runs"  : runs_data,
        "new_wrs"   : wrs_data,
    }

    return render(request, "srl/main.html", context)

def MonthlyLeaderboard(request,year,month=None):
    def add_run(main_runs,il_runs,type,month=None):
        export = {}
        for run in main_runs:
            if run["player__name"] in export:
                export[run["player__name"]]["points"] += run["points"]
            else:
                try: export[run["player__name"]] = {"nickname": run["player__nickname"], "countrycode": run["player__countrycode__id"], "points": run["points"], "runs": 1}
                except: export[run["player__name"]] = {"nickname": run["player__nickname"], "countrycode": None, "points": run["points"], "runs": 1}

        for run in il_runs:
            if run["player__name"] in export:
                export[run["player__name"]]["points"] += run["points"]
            else:
                try: export[run["player__name"]] = {"nickname": run["player__nickname"], "countrycode": run["player__countrycode__id"], "points": run["points"], "runs": 1}
                except: export[run["player__name"]] = {"nickname": run["player__nickname"], "countrycode": None, "points": run["points"], "runs": 1}

        if type == 1:
            for player in export:
                export[player]["runs"] = len(MainRuns.objects.filter(date__year=year,player__name=player))
                export[player]["runs"] += len(ILRuns.objects.filter(date__year=year,player__name=player))
        else:
            for player in export:
                export[player]["runs"] = len(MainRuns.objects.filter(date__year=year,date__month=month,player__name=player))
                export[player]["runs"] += len(ILRuns.objects.filter(date__year=year,date__month=month,player__name=player))

        return export
    
    def calculate_ranks(export):
        rank_start      = 1
        previous_points = 0
        previous_rank   = 1
        for rank, item in enumerate(export, start=rank_start):
            if previous_points == item[1]["points"]:
                item[1]["rank"] = previous_rank
                rank_start += 1
            else:
                item[1]["rank"] = rank
                previous_points = item[1]["points"]
                previous_rank   = rank
                rank_start      += 1
        
        return export

    def init_leaderboard(year,months_query=None):
        if months_query == None:
            main_runs   = MainRuns.objects.filter(date__year=year).values("player__name","player__id","player__countrycode__id","player__nickname","points").annotate(max_time_date=Max("date")).filter(date=F("max_time_date"))
            il_runs     = ILRuns.objects.filter(date__year=year).values("player__name","player__id","player__countrycode__id","player__nickname","points").annotate(max_time_date=Max("date")).filter(date=F("max_time_date"))
            
            export = add_run(main_runs,il_runs,1)
            export = sorted(export.items(), key=lambda x: x[1]["points"], reverse=True)
            export = calculate_ranks(export)
                
            return export
        else:
            player_totals = {}
            for month in months_query:
                main_runs   = MainRuns.objects.filter(date__year=year,date__month=month).values("player__name","player__id","player__countrycode__id","player__nickname","points").annotate(max_time_date=Max("date")).filter(date=F("max_time_date"))
                il_runs     = ILRuns.objects.filter(date__year=year,date__month=month).values("player__name","player__id","player__countrycode__id","player__nickname","points").annotate(max_time_date=Max("date")).filter(date=F("max_time_date"))
                
                export = add_run(main_runs,il_runs,0,month)
                export = sorted(export.items(), key=lambda x: x[1]["points"], reverse=True)
                export = calculate_ranks(export)

                player_totals[month] = export
            
            return player_totals
        
    main_run_dates  = MainRuns.objects.filter(date__year__gte=2024).dates("date","month")
    il_run_dates    = ILRuns.objects.filter(date__year__gte=2024).dates("date","month")

    months_output = {}
    for run_month in main_run_dates:
        months_output[int(run_month.strftime("%m"))] = run_month.strftime("%B %Y")

    for run_month in il_run_dates:
        months_output[int(run_month.strftime("%m"))] = run_month.strftime("%B %Y")

    if year < 2024: raise Exception
    else: int(year)
    if month:
        if month < 1 or month > 12: month = 1
        else: int(month)

    context = {
        "player_totals" : init_leaderboard(year,months_output) if month != None else init_leaderboard(year,None),
        "months"        : sorted(months_output.items(), key=lambda x: x[1], reverse=True),
        "year_query"    : year,
        "month_query"   : month if month != None else None,
    }

    return render(request, "srl/monthly_leaderboard.html", context)
    #except:
        #return redirect("/overall/2024/1")