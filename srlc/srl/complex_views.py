######################################################################################################################################################
### File Name: complex_views.py
### Author: ThePackle
### Description: Script that holds a lot of the complex views (webpages) for the project.
### Dependencies: srl/models
######################################################################################################################################################
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Sum,Q,Max,F
from django.db.models.functions import TruncDate
from .models import GameOverview,Players,MainRuns,ILRuns,VariableValues

## PlayerProfile grabs all of the unique information for a single user
## (e.g., username, nickname, main runs, individual level runs, etc.) and context's them
## so the webpage can render them.
def PlayerProfile(request,name):
    try:
        player = Players.objects.get(name__iexact=name)
    except Players.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")
    
    games         = GameOverview.objects.all().order_by("name")
    main_runs     = MainRuns.objects.filter(Q(player_id=player.id) | Q(player2_id=player.id)).annotate(o_date=TruncDate("date"))
    il_runs       = ILRuns.objects.filter(player_id=player.id).annotate(o_date=TruncDate("date"))
    total_runs    = len(main_runs) + len(il_runs)
    
    main_runs     = main_runs.filter(obsolete=False)
    il_runs       = il_runs.filter(obsolete=False)

    hidden_cats   = VariableValues.objects.filter(hidden=True).values_list("value")
    main_runs     = main_runs.exclude(values__in=hidden_cats)

    if main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)"):
        exclude   = main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)").order_by("-points").values("id")[1:]
        main_runs = main_runs.exclude(id__in=exclude)

    main_points   = sum(run.points for run in main_runs)
    il_points     = sum(run.points for run in il_runs)
    total_points  = main_points + il_points
    
    leaderboard   = Leaderboard(request,3)
    u_game_names  = games.order_by("release").values_list("name","release")

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
            "unique_game_names" : u_game_names,
            "awards"            : award_set,
        }
        return render(request, "srl/player_profile.html", context)
    
def PlayerHistory(request,name):
    try:
        player = Players.objects.get(name__iexact=name)
    except Players.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")
    
    games      = GameOverview.objects.all().order_by("name")
    main_runs  = MainRuns.objects.filter(Q(player_id=player.id) | Q(player2_id=player.id)).annotate(o_date=TruncDate("date"))
    il_runs    = ILRuns.objects.filter(player_id=player.id).annotate(o_date=TruncDate("date"))

    if main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)"):
        exclude = main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)").order_by("-points").values("id")[1:]
        main_runs = main_runs.exclude(id__in=exclude)

    unique_game_names   = games.order_by("release").values_list("name","release")

def Leaderboard(request,profile=None,game=None):
    players_all     = Players.objects.all()
    games_all       = GameOverview.objects.all()
    main_runs_all   = MainRuns.objects.exclude(place=0).filter(obsolete=False)
    il_runs_all     = ILRuns.objects.exclude(place=0).filter(obsolete=False)

    leaderboard     = []
    fg_leaderboard  = []
    il_leaderboard  = []

    for player in players_all:
        if profile == 1:
            main_runs = main_runs_all.filter(Q(player_id=player.id) | Q(player2_id=player.id))
            if main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)"):
                exclude = main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)").order_by("-points").values("id")[1:]

                main_runs = main_runs.exclude(id__in=exclude)

            main_points = main_runs.aggregate(total_points=Sum("points"))["total_points"] or 0

            leaderboard.append({
                "player"        : player.name,
                "nickname"      : player.nickname,
                "countrycode"   : player.countrycode.id if player.countrycode is not None else None,
                "countryname"   : player.countrycode.name if player.countrycode is not None else None,
                "total_points"  : main_points
            })

        elif profile == 2:
            game_id   = games_all.get(abbr=game).id
            il_runs   = il_runs_all.filter(player_id=player.id,game_id=game_id)
            il_wrs    = il_runs.filter(place=1).count() or 0
            il_points = il_runs.aggregate(total_points=Sum("points"))["total_points"] or 0
            
        elif profile == 4:
            game_id = games_all.get(abbr=game,points__gt=0).id
            il_runs = il_runs_all.filter(game_id=game_id).filter(points__gt=0)
            total_points = il_runs.aggregate(total_points=Sum("points"))["total_points"] or 0

            if total_points > 0:
                leaderboard.append({
                    "player"        : player.name,
                    "nickname"      : player.nickname,
                    "countrycode"   : player.countrycode.id if player.countrycode is not None else None,
                    "countryname"   : player.countrycode.name if player.countrycode is not None else None,
                    "game"          : game,
                    "total_points"  : total_points
                })
        elif profile == 5:
            game_id     = games_all.get(abbr=game).id
            il_runs     = il_runs_all.filter(player_id=player.id,game_id=game_id).order_by("subcategory")
            il_wrs      = il_runs.filter(place=1).count() or 0
        
            if il_wrs > 1:
                il_leaderboard.append({
                    "player"        : player.name,
                    "nickname"      : player.nickname,
                    "countrycode"   : player.countrycode.id if player.countrycode is not None else None,
                    "countryname"   : player.countrycode.name if player.countrycode is not None else None,
                    "il_wrs"        : il_wrs
                })     
        else:
            main_runs = main_runs_all.filter(Q(player_id=player.id) | Q(player2_id=player.id))
            if main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)"):
                exclude = main_runs.filter(subcategory="Classic Mode - Co-Op (Normal)").order_by("-points").values("id")[1:]

                main_runs = main_runs.exclude(id__in=exclude)

            main_points = main_runs.aggregate(total_points=Sum("points"))["total_points"] or 0
            il_points = il_runs_all.filter(player_id=player.id).aggregate(total_points=Sum("points"))["total_points"] or 0

            total_points = main_points + il_points

            leaderboard.append({
                "player"        : player.name,
                "nickname"      : player.nickname,
                "countrycode"   : player.countrycode.id if player.countrycode is not None else None,
                "countryname"   : player.countrycode.name if player.countrycode is not None else None,
                "total_points"  : total_points
            })

        if profile in [2,3]:
            if profile == 3:
                if main_points > 0:
                    fg_leaderboard.append({
                        "player"        : player.name,
                        "nickname"      : player.nickname,
                        "countrycode"   : player.countrycode.id if player.countrycode is not None else None,
                        "countryname"   : player.countrycode.name if player.countrycode is not None else None,
                        "total_points"  : main_points
                    })
            if profile in [2,3]:
                if il_points > 0:
                    il_leaderboard.append({
                        "player"        : player.name,
                        "nickname"      : player.nickname,
                        "countrycode"   : player.countrycode.id if player.countrycode is not None else None,
                        "countryname"   : player.countrycode.name if player.countrycode is not None else None,
                        "total_points"  : il_points
                    })            

    leaderboard = sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)
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
        il_runs_old     = il_runs_all.filter(game_id=game_id,points=100).exclude(level_id="rdnoro6w").order_by("date").annotate(o_date=TruncDate("date")).values_list("subcategory","time","o_date")[:10]

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

### FG_Leaderboard is used as the COMBINED points of ALL full game runs. It heavily uses the Leaderboard function above.
def FG_Leaderboard(request):
    leaderboard         = Leaderboard(request,1)

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

### IL_Leaderboard is the COMBINED IL leaderboards for a single game. It heavily uses the Leaderboard function above.
def IL_Leaderboard(request,game_abbr):
    try:
        game = GameOverview.objects.get(abbr=game_abbr)
    except GameOverview.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")
    
    leaderboard         = Leaderboard(request,2,game_abbr)

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

### search_leaderboard is used on the /overall web page (the one that combines IL and Full game points).
### This is pretty much how the searching portion works.
def search_leaderboard(request):
    search_query        = request.GET.get("search", "")
    players_all         = Players.objects.all()
    players             = Players.objects.filter(name__icontains=search_query)

    leaderboard_all     = []
    leaderboard         = []
    
    for player in players_all:
        main_points     = MainRuns.objects.filter(obsolete=False).filter(Q(player_id=player.id) | Q(player2_id=player.id)).filter(points__gt=0).aggregate(total_points=Sum("points"))["total_points"] or 0
        il_points       = ILRuns.objects.filter(obsolete=False,player_id=player.id,points__gt=0).aggregate(total_points=Sum("points"))["total_points"] or 0
        total_points    = main_points + il_points

        leaderboard_all.append({
            "player"        : player,
            "countrycode"   : player.countrycode.id if player.countrycode is not None else None,
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
        ilruns      = ILRuns.objects.filter(game_id=game[0].id).filter(points__gt=0,obsolete=False)
    except GameOverview.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")

    runs_list    = []
    
    if category == None:
        il_categories = sorted([subcategory[0] for subcategory in ilruns.values_list("subcategory").distinct()])

        for run in ilruns:
            if run.player is not None:
                for player in [run.player.id]:
                    if player != None:
                        player = players.filter(id=player)[0]
                        defaulttime = run.game.idefaulttime

                        if defaulttime == "realtime":
                            run_time = run.time
                        elif defaulttime == "realtime_noloads":
                            run_time = run.timenl
                        elif defaulttime == "ingame":
                            run_time = run.timeigt

                        ### Sometimes the defaulttime of a game does not line up with a speedrun.
                        ### This code will iterate through the time, timenl and timeigt variables to find one that does not equal "0".
                        ### Obviously there will be niche scenarios where one is more preferred over the other, but will revist this
                        if run_time == "0":
                            times = [(run.time, "realtime"), (run.timenl, "realtime_noloads"), (run.timeigt, "ingame")]
                            run_time, defaulttime = next(
                                ((time, label) for time, label in times if time != "0"),
                                ("0", None)
                            )
                    
                        run_add = {
                            "player"      : player.name if player else "Anonymous",
                            "nickname"    : player.nickname if player.nickname else None,
                            "countrycode" : player.countrycode.id if player and player.countrycode else None,
                            "countryname" : player.countrycode.name if player and player.countrycode else None,
                            "place"       : run.place,
                            "defaulttime" : defaulttime,
                            "time"        : run_time,
                            "points"      : run.points,
                            "date"        : run.date,
                            "subcategory" : run.subcategory,
                            "url"         : run.url,
                            "video"       : run.video,
                            "other_video" : run.arch_video
                        }

                    runs_list.append(run_add)

            leaderboard = sorted(runs_list, key=lambda x: x["place"], reverse=False)

    context = {
        "players"           : players,
        "runs"              : leaderboard,
        "wr_count"          : wr_count,
        "old_runs"          : old_runs,
        "subcategories"     : il_categories,
        "game_abbr"         : abbr,
        "selected_category" : category,
    }

    if "thps4/ils" in request.path_info:
        return render(request, "srl/il_leaderboard_expanded.html", context)
    else:
        return render(request, "srl/il_leaderboard.html", context)

### GameLeaderboard is the def used for full-game leaderboards.
def GameLeaderboard(request,abbr,category=None):
    ### Basic check to see if the game exists. If it doesn't work, returns a no exist; if it breaks, 500.
    try:
        game        = GameOverview.objects.get(abbr=abbr)
        players     = Players.objects.all()
        mainruns    = MainRuns.objects.filter(game_id=game.id).filter(points__gt=0,obsolete=False)
        hidden_cats = VariableValues.objects.filter(hidden=True).values_list("value")
    except GameOverview.DoesNotExist:
        return render(request, "srl/resource_no_exist.html")
    except:
        return render(request, "srl/500.html")
    
    runs_list = []

    if category == None:
        mainruns    = mainruns.exclude(values__in=hidden_cats)
        categories  = sorted([subcategory[0] for subcategory in mainruns.values_list("subcategory").distinct()])

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

            ### Sometimes the defaulttime of a game does not line up with a speedrun.
            ### This code will iterate through the time, timenl and timeigt variables to find one that does not equal "0".
            ### Obviously there will be niche scenarios where one is more preferred over the other, but will revist this
            if run_time == "0":
                times = [(run.time, "realtime"), (run.timenl, "realtime_noloads"), (run.timeigt, "ingame")]
                run_time, defaulttime = next(
                    ((time, label) for time, label in times if time != "0"),
                    ("0", None)
                )

            run_add = {
                "player"        : player.name if player != "Anonymous" else player,
                "nickname"      : player.nickname if player != "Anonymous" else None,
                "place"         : run.place,
                "defaulttime"   : defaulttime,
                "time"          : run_time,
                "points"        : run.points,
                "date"          : run.date,
                "subcategory"   : run.subcategory,
                "url"           : run.url,
                "video"         : run.video,
                "other_video"   : run.arch_video,
            }

            if player != "Anonymous":
                run_add.update({
                    "countrycode": player.countrycode.id if player.countrycode is not None else None,
                    "countryname": player.countrycode.name if player.countrycode is not None else None
                })

            if run.subcategory == "Classic Mode - Co-Op (Normal)":
                run_add.update({
                    "player2": player2.name if player2 != "Anonymous" else "Anonymous",
                    "player2nickname": player2.nickname if player2 != "Anonymous" else None,
                    "countrycode2": player2.countrycode.id if player2 != "Anonymous" and player2.countrycode else None,
                    "countryname2": player2.countrycode.name if player2 != "Anonymous" and player2.countrycode else None
                })

            runs_list.append(run_add)
        
        leaderboard = sorted(runs_list, key=lambda x: x["place"], reverse=False)

    context = {
        "players"               : players,
        "runs"                  : leaderboard,
        "subcategories"         : categories,
        "game_abbr"             : abbr,
        "selected_category"     : category
    }

    return render(request, "srl/il_leaderboard.html", context)

### MainPage is, well, for the main page. This sets up the "Current World Records", "Latest Runs", and "Latest World Records" tables.
### subcategories and exempt_games are hard-coded for now until a better solution comes up for how to store them. For your project, modify them.
def MainPage(request):
    ### These subcategories are what is queried to have them appear as World Records on the main page. It is kinda clunky, I will eventually have a better solution.
    ### To get these values, look up the ID of the WR in a category and copy + paste the "Subcategory Name" field here.
    subcategories    = ["Any%", "Any% (6th Gen)", "100%", "Any% (No Major Glitches)", "All Goals & Golds (No Major Glitches)", "All Goals & Golds (All Careers)", "All Goals & Golds (6th Gen)", "Any% (Beginner)", "100% (NSR)",\
                     "Story (Easy, NG+)", "100% (NG)", "Classic (Normal, NG+)", "Story Mode (Easy, NG+)", "Classic Mode (Normal)", "Any% (360/PS3)", "100% (360/PS3)", "Any% Tour Mode (All Tours, New Game)", "All Goals & Golds (All Tours, New Game)"]
    exempt_games     = ["GBA","PSP","GBC","Category Extensions","Remix","Sk8land","HD","2x"]
    
    exclusion_filter = Q()
    run_list         = []
    wrs_data         = []
    runs_data        = []

    for game in exempt_games:
        exclusion_filter |= Q(game__name__icontains=game)

    runs = MainRuns.objects.exclude(obsolete=True).exclude(exclusion_filter).filter(place=1,subcategory__in=subcategories).order_by("-subcategory").annotate(o_date=TruncDate("date"))

    ### Next blocks of code are checks to group runs together within the same game and subcategory. In some circumstances, world records are ties.
    ### This makes it so it display properly on the main page (as opposed to two rows, they are on a combined row).
    grouped_runs = []
    seen_records = set()

    for run in runs:
        key = (run.game.abbr, run.subcategory, run.time)
        if key not in seen_records:
            grouped_runs.append({
                "game"          : run.game,
                "subcategory"   : run.subcategory,
                "time"          : run.time,
                "players"       : []
            })
            seen_records.add(key)

        for record in grouped_runs:
            if record["game"].abbr == run.game.abbr and record["subcategory"] == run.subcategory and record["time"] == run.time:
                record["players"].append({
                    "player"    : run.player,
                    "url"       : run.url,
                    "date"      : run.o_date
                })

    ### Sorts runs within the run_list by the game release date, oldest first.
    run_list = sorted(grouped_runs, key=lambda x: x["game"].release, reverse=False)

    ### Sometimes v_date (verify_date) is null; this can happen if the runs on a leaderboard are super old.
    ### And since MainRuns and ILRuns are separate models, this code will exclude v_dates that are null, order by v_date, and get the latest 5 for each model.
    ### wrs does the same, but filters based on place=1 in the model.
    wrs = (MainRuns.objects.filter(place=1,obsolete=False,v_date__isnull=False).order_by("-v_date")[:25]).union(ILRuns.objects.filter(place=1,obsolete=False,v_date__isnull=False).order_by("-v_date")[:25]).order_by("-v_date").values("id")[:5]
    pbs = (MainRuns.objects.filter(obsolete=False,v_date__isnull=False).exclude(place=1).order_by("-v_date")[:25]).union(ILRuns.objects.filter(obsolete=False,v_date__isnull=False).exclude(place=1).order_by("-v_date")[:25]).order_by("-v_date").values("id")[:5]

    for pb in pbs:
        try: run = MainRuns.objects.get(id=pb["id"])
        except: run = ILRuns.objects.get(id=pb["id"])
        
        if run:
            runs_data.append(run)

    for wr in wrs:
        try: run = MainRuns.objects.get(id=wr["id"])
        except: run = ILRuns.objects.get(id=wr["id"])

        if run:
            wrs_data.append(run)

    context = {
        "runs"      : run_list,
        "new_runs"  : runs_data,
        "new_wrs"   : wrs_data,
    }

    return render(request, "srl/main.html", context)

### All of the below is a work-in-progress for the eventual Historical Leaderboards update
###########################################################################################
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