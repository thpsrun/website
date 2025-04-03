######################################################################################################################################################
### File Name: API/views.py
### Author: ThePackle
### Description: All of the necessary defs and commands to add a new, approved run to the API.
### Dependencies: srl/models, srl/tasks
######################################################################################################################################################
import math
from django.db import transaction
from django.db.models import Count
from celery import shared_task
from srl.models import Variables,Categories,VariableValues,MainRuns,ILRuns,GameOverview,Players,Levels,Platforms
from srl.tasks import convert_time,update_player
from srl.m_tasks import points_formula

### add_run starts to gathers information about the approved run from the SRC API.
### The biggest thing here is that it will normalize the data so it can be properly stored in your API.
### Part of the normalization is taking the categories and sub-categories and sub-sub-categories and properly formatting them before handing them to invoke_run.
@shared_task
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
            invoke_single_run.delay(game["id"],category,run,var_name,None,obsolete,point_reset)
        else:
            invoke_single_run.delay(game["id"],category,run,level["name"],None,obsolete,point_reset)

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
                
                invoke_single_run.delay(game["id"],category,run,var_name,var_str,obsolete,point_reset)


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

        invoke_single_run.delay(game["id"],category,run,var_name,var_str,obsolete,point_reset)

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

            invoke_single_run.delay(game["id"],category,run,var_name,None,obsolete,point_reset)

        else:
            invoke_single_run.delay(game["id"],category,run,category["name"],None,obsolete,point_reset)

### invoke_single_run normalizes the rest of the run from the SRC API and prepares to add it to the correct model.
@shared_task
def invoke_single_run(game_id,category,run,var_name=None,var_string=None,obsolete=False,point_reset=True):
    if obsolete == False:
        players = run["run"]["players"]
        place = run["place"]
    else:
        run = {"run":run}
        if "data" in run.get("run", {}).get("players", {}): players = run["run"]["players"]["data"]
        else: players = run["run"]["players"]

        place = 0

    lrt_fix = False
    if run["run"]["level"] != None:
        max_points = GameOverview.objects.get(id=game_id).ipointsmax

        if GameOverview.objects.get(id=game_id).idefaulttime == "realtime_noloads": lrt_fix = True
    else:
        max_points = GameOverview.objects.get(id=game_id).pointsmax

        if GameOverview.objects.get(id=game_id).defaulttime == "realtime_noloads": lrt_fix = True

    if players != None:
        run_id       = run["run"]["id"]
        secs         = run["run"]["times"]["primary_t"]

        try: run_video = run.get("run").get("videos").get("links")[0].get("uri") if run.get("run").get("videos") is not None or run.get("run").get("videos").get("text") != "N/A" else None
        except: run_video = None

        ### All of the below fields correlate to the MainRuns and ILRuns models.
        default = {
            "game"          : GameOverview.objects.get(id=game_id),
            "category"      : Categories.objects.get(id=category["id"]),
            "subcategory"   : var_name,
            "values"        : var_string,
            "place"         : place,
            "url"           : run["run"]["weblink"],
            "video"         : run_video,
            "date"          : run["run"]["submitted"] if run["run"]["submitted"] else run["run"]["date"],
            "v_date"        : run["run"]["status"]["verify-date"],
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

        ### LRT_TEMP_FIX
        ### This is a temporary fix for an issue with the SRC API where runs that have LRT but no RTA time will have the
        ### LRT set to RTA instead. Really dumb.
        if lrt_fix and default["time_secs"] > 0 and default["timenl_secs"] == 0:
            default["time"]         = "0"
            default["time_secs"]    = 0.0
            default["timenl"]       = convert_time(run["run"]["times"]["realtime_t"])
            default["timenl_secs"]  = run["run"]["times"]["realtime_t"]

        if category["type"] == "per-game":
            reset_points = "Game"

            if obsolete == False:
                ### Some runs in the SRC API (runs that are on separate platforms, for example, but there is one faster) are seen as Place 0. This skips that.
                if run["place"] == 1:
                    points = max_points
                elif run["place"] > 1:
                    wr_pull     = MainRuns.objects.filter(game=game_id,subcategory=var_name,obsolete=False,place=1)[0]
                    defaulttime = wr_pull.game.defaulttime

                    if defaulttime == "realtime":
                        if wr_pull.time_secs == 0:
                            wrecord = wr_pull.timeigt_secs
                        else:
                            wrecord = wr_pull.time_secs
                    elif defaulttime == "realtime_noloads":
                        wrecord = wr_pull.timenl_secs
                    elif defaulttime == "ingame":
                        if wr_pull.timeigt_secs == 0:
                            wrecord = wr_pull.time_secs
                        else:
                            wrecord = wr_pull.timeigt_secs

                    points = points_formula(wrecord,secs,max_points)

            player1 = players[0].get("id")
            player2 = players[1].get("id") if len(players) > 1 and players[1]["rel"] == "user" else None

            if player1:
                default["player"]   = Players.objects.get(id=player1) if Players.objects.filter(id=player1).exists() else None
            if player2:
                default["player2"]  = Players.objects.get(id=player2)if Players.objects.filter(id=player2).exists() else None

            with transaction.atomic():
                MainRuns.objects.update_or_create(
                    id = run_id,
                    defaults = default
                )

            if point_reset:
                with transaction.atomic():
                    MainRuns.objects.update_or_create(
                        id = run_id,
                        defaults = {
                            "points" : points
                        }
                    )
                
        else:
            reset_points = "IL"
            if obsolete == False:
                if run["place"] == 1:
                    points = max_points
                elif run["place"] > 1:
                    wr_pull = ILRuns.objects.filter(game=game_id,subcategory=var_name,obsolete=False,place=1)[0]
                    defaulttime = wr_pull.game.idefaulttime
                    
                    if defaulttime == "realtime":
                        if wr_pull.time_secs == 0:
                            wrecord = wr_pull.timeigt_secs
                        else:
                            wrecord = wr_pull.time_secs
                    elif defaulttime == "realtime_noloads":
                        wrecord = wr_pull.timenl_secs
                    elif defaulttime == "ingame":
                        if wr_pull.timeigt_secs == 0:
                            wrecord = wr_pull.time_secs
                        else:
                            wrecord = wr_pull.timeigt_secs
                    
                    points = points_formula(wrecord,secs,max_points)

            player1 = players[0].get("id")
            
            update_player.delay(player1)

            if player1:
                default["player"] = Players.objects.get(id=player1) if Players.objects.filter(id=player1).exists() else None

            default["level"] = Levels.objects.get(id=run["run"]["level"])

            with transaction.atomic():
                ILRuns.objects.update_or_create(
                    id = run_id,
                    defaults = default
                )

            if point_reset:
                with transaction.atomic():
                    ILRuns.objects.update_or_create(
                        id = run_id,
                        defaults = {
                            "points" : points
                        }
                    )

        if point_reset:
            remove_obsolete.delay(game_id,var_name,players,reset_points)
            update_points.delay(game_id,var_name,max_points,reset_points)

### update_points is ran after a new run is successfully uploaded to the API.
### It will go through all of the runs within a game's specific subcategory and re-rank their points.
@shared_task
def update_points(game_id,subcategory,max_points,reset_points):
    place        = 1
    old_time     = 0
    old_points   = 0
    rank_count   = 0

    ### Dictionary to maps default timing methods to the type of seconds used.
    time_columns = {
        "realtime"         : "time_secs",
        "realtime_noloads" : "timenl_secs",
        "ingame"           : "timeigt_secs"
    }

    if reset_points == "Game":
        all_runs = MainRuns.objects.filter(game=game_id,subcategory=subcategory,obsolete=False)
        default_time = GameOverview.objects.get(id=game_id).defaulttime
    else:
        all_runs = ILRuns.objects.filter(game=game_id,subcategory=subcategory,obsolete=False)
        default_time = GameOverview.objects.get(id=game_id).idefaulttime

    runs = all_runs.order_by(time_columns[default_time])
    wr_time = runs[0].__getattribute__(time_columns[default_time])

    ### Logic here will iterate through the runs from the same subcategory that are not obsolete in the same game.
    ### If it is WR, then it gets max_points; rank is incremented.
    ### NOTE: Dunno why I have the elif, lol. Need to figure that out.
    ### If it is not WR, then points are calculated based on the formula and the max_points of the run.
    ### The place of the run would be place + rank_count; rank_count is reset to 1. Then saved.
    for run in runs:
        run_time = run.__getattribute__(time_columns[default_time])

        if run_time == 0:
            run_time = run.timeigt_secs

        if run_time == wr_time:
            run.place  = place
            run.points = max_points

            old_points = max_points
            rank_count += 1
        elif run_time == old_time:
            run.place  = place
            run.points = old_points

            rank_count += 1
        else:
            points     = points_formula(wr_time,run_time,max_points)
            run.points = points

            if rank_count > 0:
                run.place  = place + rank_count
                place      += rank_count
                
                rank_count = 1
            else:
                place     += 1
                run.place = place

            old_time   = run_time
            old_points = points
        
        run.save(update_fields=["place","points"])


### remove_obsolete is ran after a new run is successfully uploaded to the API.
### It will run through all runs from the same player in the same game, category, and run type.
### It will mark all non-current runs as Obsolete, so they will not appear on the leaderboards.
### NOTE: Obsolete runs will retain their final point total, and are still counted as completed to the player's profile.
@shared_task
def remove_obsolete(game_id,subcategory,players,run_type):
    time_columns = {
        "realtime"         : "time_secs",
        "realtime_noloads" : "timenl_secs",
        "ingame"           : "timeigt_secs"
    }

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

                ### Checks the defaulttime from the GameOverview model.
                ### Once found, it will set the slowest_runs variable based on the game ID, whether it is already obsolete, from the same player, in the same category.
                default_time = GameOverview.objects.get(id=game_id).idefaulttime
                slowest_runs = ILRuns.objects.filter(game=game_id,obsolete=False,player=player["id"],subcategory__in=duplicated_subcategories).order_by(f"-{time_columns[default_time]}")
            
            else:
                duplicated_subcategories = (
                    MainRuns.objects.filter(game=game_id,player=player["id"],subcategory=subcategory)
                    .values("subcategory")
                    .annotate(count=Count("subcategory"))
                    .filter(count__gt=1)
                    .values("subcategory")
                )

                ### Checks the defaulttime from the GameOverview model.
                ### Once found, it will set the slowest_runs variable based on the game ID, whether it is already obsolete, from the same player, in the same category.
                default_time = GameOverview.objects.get(id=game_id).defaulttime
                slowest_runs = MainRuns.objects.filter(game=game_id,obsolete=False,player=player["id"],subcategory__in=duplicated_subcategories).order_by(f"-{time_columns[default_time]}")
                
            ### Removes the newest time from the query, then sets all other runs (should be one) to obsolete.
            if len(slowest_runs) > 0:
                last = slowest_runs.last()
                slowest_runs = slowest_runs.exclude(id=last.id)
                for new_obsolete in slowest_runs:
                    new_obsolete.obsolete = True
                    new_obsolete.save(force_update=True)