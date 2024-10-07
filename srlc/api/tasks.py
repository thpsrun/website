import math
from django.db import transaction
from django.db.models import Count
from asgiref.sync import sync_to_async
from srl.models import Variables,Categories,VariableValues,MainRuns,ILRuns,GameOverview,Players,Levels,Platforms
from srl.tasks import convert_time,update_player

def add_run(game,run,category,level,run_variables,obsolete=False,point_reset=True):
    var_ids     = Variables.objects.filter(cat=category["id"])
    global_cats = Variables.objects.filter(all_cats=True,game=game["id"])

    variable_list = []
    for key, value in run_variables.items():
        variable_list.append(value)

    if category["type"] == "per-level":
        per_level_check = Categories.objects.filter(game=game["id"],type="per-level")

        if len(per_level_check) > 1:
            var_name = level["name"] + " (" + category["name"] + ")"
            invoke_single_run(game["id"],category,run,var_name,None,obsolete,point_reset)
        else:
            invoke_single_run(game["id"],category,run,level["name"],None,obsolete,point_reset)

    elif len(var_ids) == 1:
        var_value = VariableValues.objects.filter(var=var_ids[0].id)

        for var in var_value:
            if var.value in variable_list:
                var_string    = f"{var.value}"
                var_name      = f"{var.name}"
                var_name2     = ""

                if len(global_cats) > 1:
                    for global_cat in global_cats:
                        global_values = VariableValues.objects.filter(var=global_cat.id)

                        for global_value in global_values:
                            if global_value.value in variable_list:
                                var_name2  = f"{global_value.name}"

                                var_name = category["name"] + " " + var_name + "(" + var_name2 + ")"
                                var_str = var_string + "&" + f"{global_value.value}"

                elif len(global_cats) == 1:
                    global_values = VariableValues.objects.filter(var=global_cats[0].id)

                    for global_value in global_values:
                        if global_value.value in variable_list:
                            var_name2  = f", {global_value.name}"

                            var_name = category["name"] + " (" + var_name + var_name2 + ")"
                            var_str = var_string + "&" + f"{global_value.value}"

                else:
                    var_name = category["name"] + " (" + var_name + ")"
                    var_str = var_string
                
                invoke_single_run(game["id"],category,run,var_name,var_str,obsolete,point_reset)


    elif len(var_ids) > 1:
        var_string  = ""
        var_name    = ""
        
        for variable in var_ids:
            var_value = VariableValues.objects.filter(var=variable.id)

            for var in var_value:
                if var.value in variable_list:
                    temp_string    = f"{var.value}"
                    temp_name      = f"{var.name}"

                    var_string += temp_string + "&"
                    var_name   += temp_name + ", "

        if len(global_cats) > 1:
            for global_cat in global_cats:
                    global_values = VariableValues.objects.filter(var=global_cat.id)

                    for global_value in global_values:
                        if global_value.value in variable_list:
                            var_name2  = f"{global_value.name}"

                            var_name = category["name"] + " " + var_name + "(" + var_name2 + ")"
                            var_str = var_string + "&" + f"{global_value.value}"

        elif len(global_cats) == 1:
            global_values = VariableValues.objects.filter(var=global_cats[0].id)

            for global_value in global_values:
                if global_value.value in variable_list:
                    var_name2  = f", {global_value.name}"

                    var_name = category["name"] + " (" + var_name + var_name2 + ")"
                    var_str = var_string + "&" + f"{global_value.value}"

        else:
            var_name = category["name"] + " (" + var_name.rstrip(", ") + ")"
            var_str = var_string.rstrip("&")

        invoke_single_run(game["id"],category,run,var_name,var_str,obsolete,point_reset)

    elif category["type"] == "per-game" and len(var_ids) == 0:
        if len(global_cats) > 0:
            for global_cat in global_cats:
                var_name  = ""

                global_values = VariableValues.objects.filter(var=global_cat.id)

                for global_value in global_values:
                    if global_value.value in variable_list:    
                        temp_name  = f"{global_value.name}"

                        var_name += temp_name + ", "

            var_name = category["name"] + " (" + var_name.rstrip(", ") + ")"

            invoke_single_run(game["id"],category,run,var_name,None,obsolete,point_reset)

        else:
            invoke_single_run(game["id"],category,run,category["name"],None,obsolete,point_reset)

def invoke_single_run(game_id,category,run,var_name=None,var_string=None,obsolete=False,point_reset=True):
    if obsolete == False:
        players = run["run"]["players"]
        place = run["place"]
    else:
        run = {"run":run}
        #try: players = run["run"]["players"]["data"]
        #except: players = run["run"]["players"]
        if "data" in run.get("run", {}).get("players", {}): players = run["run"]["players"]["data"]
        else: players = run["run"]["players"]

        place = 0

    if run["run"]["game"] in ["o6glkk8d","o1yjk541","9d38jey1"]:
        run_type = 25
    elif run["run"]["level"] != None:
        run_type = 100
    else:
        run_type = 1000

    points = 25 if run_type == 25 else 100 if run_type == 100 else 1000

    if players != None:
        run_id       = run["run"]["id"]
        secs         = run["run"]["times"]["primary_t"]

        try: run_video = run.get("run").get("videos").get("links")[0].get("uri") if run.get("run").get("videos") is not None or run.get("run").get("videos").get("text") != "N/A" else None
        except: run_video = None

        default = {
            "game"          : GameOverview.objects.get(id=game_id),
            "category"      : Categories.objects.get(id=category["id"]),
            "subcategory"   : var_name,
            "values"        : var_string,
            "place"         : place,
            "url"           : run["run"]["weblink"],
            "video"         : run_video,
            "date"          : run["run"]["date"],
            "time"          : convert_time(run["run"]["times"]["realtime_t"]) if run["run"]["times"]["realtime_t"] > 0 else 0,
            "time_secs"     : run["run"]["times"]["realtime_t"],
            "timenl"        : convert_time(run["run"]["times"]["realtime_noloads_t"]) if run["run"]["times"]["realtime_noloads_t"] > 0 else 0,
            "timenl_secs"   : run["run"]["times"]["realtime_noloads_t"],
            "timeigt"       : convert_time(run["run"]["times"]["ingame_t"]) if run["run"]["times"]["ingame_t"] > 0 else 0,
            "timeigt_secs"  : run["run"]["times"]["ingame_t"],
            "platform"      : Platforms.objects.get(id=run["run"]["system"]["platform"]) if Platforms.objects.filter(id=run["run"]["system"]["platform"]).exists() else None,
            "emulated"      : run["run"]["system"]["emulated"],
            "obsolete"      : obsolete
        }

        if category["type"] == "per-game":
            reset_points = "Game"

            if obsolete == False:
                if run["place"] > 1:
                    wrecord = MainRuns.objects.filter(game=game_id,subcategory=var_name,obsolete=False,place=1).values("time_secs")[0]["time_secs"]
                    points = math.floor((0.008 * math.pow(math.e, (4.8284 * (wrecord/secs)))) * run_type)
            else:
                points = 0

            player1 = players[0].get("id")
            player2 = players[1].get("id") if len(players) > 1 and players[1]["rel"] == "user" else None

            default["player"]   = Players.objects.get(id=player1)
            default["player2"]  = Players.objects.get(id=player2) if Players.objects.filter(id=player2).exists() else None

            with transaction.atomic():
                MainRuns.objects.update_or_create(
                    id = run_id,
                    defaults = default
                )

            if point_reset == True:
                with transaction.atomic():
                    MainRuns.objects.update_or_create(
                        id = run_id,
                        defaults = {
                            "points"    : points
                        }
                    )
                
        else:
            reset_points = "IL"
            
            if obsolete == False:
                if run["place"] > 1:
                    wrecord = ILRuns.objects.filter(game=game_id,subcategory=var_name,obsolete=False,place=1).values("time_secs")[0]["time_secs"]
                    points = math.floor((0.008 * math.pow(math.e, (4.8284 * (wrecord/secs)))) * run_type)
            else:
                points = 0

            player1 = players[0].get("id")

            default["player"]   = Players.objects.get(id=player1)
            default["level"]    = Levels.objects.get(id=run["run"]["level"])

            with transaction.atomic():
                ILRuns.objects.update_or_create(
                    id = run_id,
                    defaults = default
                )

            if point_reset == True:
                with transaction.atomic():
                    ILRuns.objects.update_or_create(
                        id = run_id,
                        defaults = {
                            "points"    : points
                        }
                    )

        for player in players:
            if player["rel"] != "guest":
                update_player(player["id"])

        if point_reset == True:
            remove_obsolete(game_id,var_name,players,reset_points)
            update_points(game_id,var_name,run_type,reset_points)

def update_points(game_id,subcategory,run_type,reset_points):
    #TODO
    #Logic needs to be updated so it will check for obsolete runs by the player within the same category; only the most recent time has points.
    #If Player1 gets two PBs, one for 534 points then one for 857 points, then the 534 would be set to 0 in the same category.
    #If Player1 gets WR, then both of the old runs are set to 0?
    #Alternatively, could just search for specifically the first result with the highest points in each category; this will fix it for months to quarters to years.
    place    = 1
    o_time   = 0
    o_points = 0
    rank_ct  = 0

    if reset_points == "Game":
        runs     = MainRuns.objects.filter(game=game_id,subcategory=subcategory,obsolete=False).order_by("time_secs")
        wr_time  = runs.values("time_secs")[0]["time_secs"]
        
        for fg in runs: 
            if fg.points > 0:
                if fg.time_secs == wr_time:
                    fg.place    = place
                    fg.points   = run_type

                    o_points    = run_type
                    rank_ct     += 1

                elif fg.time_secs == o_time:
                    fg.place    = place
                    fg.points   = o_points

                    rank_ct     += 1

                else:
                    secs        = fg.time_secs
                    points      = math.floor((0.008 * math.pow(math.e, (4.8284 * (wr_time/secs)))) * run_type)
                    fg.points   = points

                    if rank_ct > 0:
                        fg.place = place + rank_ct
                        place    += rank_ct

                        rank_ct  = 1

                    else:
                        place    += 1
                        fg.place = place

                    o_time       = secs
                    o_points     = points

                fg.save()

    else:
        runs = ILRuns.objects.filter(game=game_id,subcategory=subcategory,obsolete=False).order_by("time_secs")
        wr_time = runs.values("time_secs")[0]["time_secs"]

        for il in runs:
            if il.points > 0:
                if il.time_secs == wr_time:
                    il.place    = place
                    il.points   = run_type

                    o_points    = run_type
                    rank_ct     += 1

                elif il.time_secs == o_time:
                    il.place    = place
                    il.points   = o_points
                    
                    rank_ct     += 1

                else:
                    secs        = il.time_secs
                    points      = math.floor((0.008 * math.pow(math.e, (4.8284 * (wr_time/secs)))) * run_type)
                    il.points   = points

                    if rank_ct > 0:
                        il.place = place + rank_ct
                        place    += rank_ct

                        rank_ct  = 1

                    else:
                        place    += 1
                        il.place = place
                        
                    o_time      = secs
                    o_points    = points

                il.save()

def remove_obsolete(game_id,subcategory,players,run_type):
    for player in players:
        if player != None and player["rel"] != "guest":
            if run_type == "IL":
                duplicated_subcategories = (
                    ILRuns.objects.filter(game=game_id,player=player["id"],subcategory=subcategory)
                    .values("subcategory")
                    .annotate(count=Count("subcategory"))
                    .filter(count__gt=1)
                    .values("subcategory")
                )

                slowest_runs = ILRuns.objects.filter(game=game_id,obsolete=False,player=player["id"],subcategory__in=duplicated_subcategories).order_by("-time_secs")
                if len(slowest_runs) > 0:
                    last         = slowest_runs.last()
                    slowest_runs = slowest_runs.exclude(id=last.id)
                    slowest_runs.update(obsolete=True)
            
            else:
                duplicated_subcategories = (
                    MainRuns.objects.filter(game=game_id,player=player["id"],subcategory=subcategory)
                    .values("subcategory")
                    .annotate(count=Count("subcategory"))
                    .filter(count__gt=1)
                    .values("subcategory")
                )

                slowest_runs = MainRuns.objects.filter(game=game_id,obsolete=False,player=player["id"],subcategory__in=duplicated_subcategories).order_by("-time_secs")

                if len(slowest_runs) > 0:
                    last         = slowest_runs.last()
                    slowest_runs = slowest_runs.exclude(id=last.id)
                    slowest_runs.update(obsolete=True)