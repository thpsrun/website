import time,math,requests,os
from django.db import transaction
from django.db.models import Q
from django.db import transaction
from asgiref.sync import sync_to_async
from langcodes import standardize_tag
from .models import GameOverview,Categories,Levels,Variables,VariableValues,MainRuns,ILRuns,Players,CountryCodes,Platforms,MainRunTimeframe
from .m_tasks import src_api,convert_time

def update_game(src_game):
    src_game = src_api(f"https://www.speedrun.com/api/v1/games/{src_game['id']}?embed=platforms")

    if isinstance(src_game,dict):
        with transaction.atomic():
            game, created = GameOverview.objects.update_or_create(
                id = src_game["id"],
                defaults = {
                    "name"          : src_game["names"]["international"],
                    "abbr"          : src_game["abbreviation"],
                    "release"       : src_game["release-date"],
                    "defaulttime"   : src_game["ruleset"]["default-time"],
                    "boxart"        : src_game["assets"]["cover-large"]["uri"],
                }
            )

            plat_names = [plat["id"] for plat in src_game["platforms"]["data"]]

            for plat in plat_names:
                game.platforms.add(plat)

def update_game_runs(game_id,reset):
    if reset == 1:
        Categories.objects.filter(game=game_id).delete()
        Levels.objects.filter(game=game_id).delete()
        Variables.objects.filter(game=game_id).delete()
        MainRuns.objects.filter(game=game_id).delete()
        ILRuns.objects.filter(game=game_id).delete()

    game_check = src_api(f"https://www.speedrun.com/api/v1/games/{game_id}?embed=platforms,levels,categories,variables")

    if isinstance(game_check,dict):
        cat_check = game_check["categories"]["data"]
        for check in cat_check:
            update_category(check,game_id)

        il_check = game_check["levels"]["data"]
        if len(il_check) > 0:
            for level in il_check:
                update_level(level,game_id)
        
        var_check = game_check["variables"]["data"]
        if len(var_check) > 0:
            for variable in var_check:
                update_variable(game_id,variable)

        for category in cat_check:
            update_category_runs(game_id,category,il_check)

def update_category(category,game_id):
    with transaction.atomic():
        Categories.objects.update_or_create(
            id       = category["id"],
            defaults = {
                "name"  : category["name"],
                "game"  : GameOverview.objects.get(id=game_id),
                "type"  : category["type"],
                "url"   : category["weblink"],
            }
        )

def update_platform(platform):
    with transaction.atomic():
        Platforms.objects.update_or_create(
            id      = platform["id"],
            defaults = {
                "name"  : platform["name"]
            }
        )

def update_level(level,game_id):
    with transaction.atomic():
        Levels.objects.update_or_create(
            id      = level["id"],
            defaults = {
                "name"  : level["name"],
                "game"  : GameOverview.objects.get(id=game_id),
                "url"   : level["weblink"],
            }
        )

def update_variable(gameid,variable):
    with transaction.atomic():
        Variables.objects.update_or_create(
            id      = variable["id"],
            defaults = {
                "name"      : variable["name"],
                "game"      : GameOverview.objects.get(id=gameid),
                "cat"       : None if variable["category"] == None else Categories.objects.get(id=variable["category"]),
                "all_cats"  : True if variable["category"] == None else False,
                "scope"     : variable["scope"]["type"],
            }
        )

    if variable["is-subcategory"]:
        for value in variable["values"]["values"]:
            update_variable_value(variable,value)

def update_variable_value(variable,value):
    with transaction.atomic():
        VariableValues.objects.update_or_create(
            var     = Variables.objects.get(id=variable["id"]),
            value   = value,
            name    = variable["values"]["values"][value]["label"],
        )

def update_category_runs(game_id,category,il_check):
    var_ids        = Variables.objects.filter(cat=category["id"])
    global_cats    = Variables.objects.filter(all_cats=True,game=game_id)
    global_fg_cats = Variables.objects.filter(all_cats=True,scope="full-game",game=game_id)

    if category["type"] == "per-level":
        per_level_check = Categories.objects.filter(game=game_id,type="per-level")

        for il in il_check:
            leaderboard = src_api(f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/level/{il['id']}/{category['id']}?embed=players,game,category")

            if len(per_level_check) > 1:
                var_name = il["name"] + " (" + category["name"] + ")"
                invoke_runs(game_id,category,leaderboard,var_name)
            else:
                invoke_runs(game_id,category,leaderboard,il["name"])

    elif len(global_fg_cats) > 1:
        cat_list      = []
        var_name_list = []
        var_str_list  = []

        if len(global_fg_cats) == 2:
            global_cat_one = VariableValues.objects.filter(var_id=global_fg_cats[0].id)
            global_cat_two = VariableValues.objects.filter(var_id=global_fg_cats[1].id)

            for global_value_one in global_cat_one:
                var_name   = ""
                lb_string  = ""
                var_string = ""

                lb_string  = lb_string + f"var-{global_value_one.var.id}={global_value_one.value}&" 
                var_name   = var_name + f"{global_value_one.name}, "
                var_string = var_string + f"{global_value_one.value}&"

                for global_value_two in global_cat_two:
                    lb_string2  = lb_string + f"var-{global_value_two.var.id}={global_value_two.value}&" 
                    var_name2   = var_name + f"{global_value_two.name}, "
                    var_string2 = var_string + f"{global_value_two.value}&"

                    cat_list.append(lb_string2.rstrip("&"))
                    var_name_list.append(category["name"] + " (" + var_name2.rstrip(", ") + ")")
                    var_str_list.append(var_string2.rsplit("&"))
        
        for index, lb_string in enumerate(cat_list):
            leaderboard = src_api(f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category['id']}?{lb_string}&embed=players,game,category")
            if leaderboard != 400:
                invoke_runs(game_id,category,leaderboard,var_name_list[index],var_str_list[index])

    elif len(var_ids) == 1:
        var_value = VariableValues.objects.filter(var=var_ids[0].id)

        for var in var_value:
            lb_string     = f"var-{var.var.id}={var.value}" 
            var_string    = f"{var.value}"
            var_name      = f"{var.name}"
            cat_list      = []
            var_name_list = []
            var_str_list  = []
            lb_string2    = ""
            var_name2     = ""

            if len(global_cats) > 1:
                for global_cat in global_cats:
                    global_values = VariableValues.objects.filter(var=global_cat.id)

                    for global_value in global_values:
                        lb_string2 = f"var-{global_cat.id}={global_value.value}&" 
                        var_name2  = f"{global_value.name}"

                        cat_list.append(lb_string2 + lb_string)
                        var_name_list.append(category["name"] + " " + var_name + "(" + var_name2 + ")")
                        var_str_list.append(var_string + "&" + f"{global_value.value}")

            elif len(global_cats) == 1:
                global_values = VariableValues.objects.filter(var=global_cats[0].id)

                for global_value in global_values:
                    lb_string2 = f"&var-{global_value.var.id}={global_value.value}"  
                    var_name2  = f", {global_value.name}"

                    cat_list.append(lb_string + lb_string2)
                    var_name_list.append(category["name"] + " (" + var_name + var_name2 + ")")
                    var_str_list.append(var_string + "&" + f"{global_value.value}")

            else:
                cat_list.append(lb_string)
                var_name_list.append(category["name"] + " (" + var_name + ")")
                var_str_list.append(var_string)
            
            for index, lb_string in enumerate(cat_list):
                leaderboard = src_api(f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category['id']}?{lb_string}&embed=players,game,category")
                if leaderboard != 400:
                    invoke_runs(game_id,category,leaderboard,var_name_list[index],var_str_list[index])

    elif len(var_ids) > 1:
        var_value_one = VariableValues.objects.filter(var=var_ids[0].id)
        var_value_two = VariableValues.objects.filter(var=var_ids[1].id)

        lb_string     = ""
        var_string    = ""
        var_name      = ""
        cat_list      = []
        var_name_list = []
        var_str_list  = []
        lb_string2    = ""
        var_name2     = ""

        for variable in var_value_one:
            for variable_2 in var_value_two:
                lb_string  = f"var-{variable.var.id}={variable.value}&var-{variable_2.var.id}={variable_2.value}&" 
                var_name   = f"{variable.name}, {variable_2.name}, "
                var_string = f"{variable.value}&{variable_2.value}"

                if len(global_cats) > 1:
                    for global_cat in global_cats:
                        global_values = VariableValues.objects.filter(var=global_cat.id)

                        for global_value in global_values:
                            lb_string2 = f"var-{global_cat.id}={global_value.value}&" 
                            var_name2  = f"{global_value.name}"

                            cat_list.append(lb_string2 + lb_string)
                            var_name_list.append(category["name"] + " " + var_name + "(" + var_name2 + ")")
                            var_str_list.append(var_string + "&" + f"{global_value.value}")

                elif len(global_cats) == 1:
                    global_values = VariableValues.objects.filter(var=global_cats[0].id)

                    for global_value in global_values:
                        lb_string2 = f"&var-{global_value.var.id}={global_value.value}"  
                        var_name2  = f", {global_value.name}"

                        cat_list.append(lb_string + lb_string2)
                        var_name_list.append(category["name"] + " (" + var_name + var_name2 + ")")
                        var_str_list.append(var_string + "&" + f"{global_value.value}")

                else:
                    cat_list.append(lb_string.rstrip("&"))
                    var_name_list.append(category["name"] + " (" + var_name.rstrip(", ") + ")")
                    var_str_list.append(var_string.rstrip("&"))

            for index, lb_string in enumerate(cat_list):
                leaderboard = src_api(f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category['id']}?{lb_string}&embed=players,game,category")
                if leaderboard != 400:
                    invoke_runs(game_id,category,leaderboard,var_name_list[index],var_str_list[index])

    elif category["type"] == "per-game" and len(var_ids) == 0:
        if len(global_cats) > 0:
            for global_cat in global_cats:
                cat_list      = []
                var_name_list = []
                var_str_list  = []
                lb_string = ""
                var_name  = ""

                global_values = VariableValues.objects.filter(var=global_cat.id)

                for global_value in global_values:
                    lb_string = f"var-{global_cat.id}={global_value.value}" 
                    var_name  = f"{global_value.name}"

                    cat_list.append(lb_string)
                    var_name_list.append(category["name"] + " (" + var_name + ")")

                for index, lb_string in enumerate(cat_list):
                    leaderboard = src_api(f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category['id']}?{lb_string}&embed=players,game,category")
                    if leaderboard != 400:
                        invoke_runs(game_id,category,leaderboard,var_name_list[index])

        else:
            leaderboard = src_api(f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category['id']}?embed=players,game,category")
            if leaderboard != 400:
                invoke_runs(game_id,category,leaderboard,category["name"])

def update_player(player):
    player_data = src_api(f"https://www.speedrun.com/api/v1/users/{player}")

    if isinstance(player_data,dict) and player_data is not None:
        if player_data["assets"]["image"]["uri"] != None:
            response = requests.get(player_data["assets"]["image"]["uri"])

            while response.status_code == 420 or response.status_code == 503:
                time.sleep(60)
                response = requests.get(player_data["assets"]["image"]["uri"])

            folder_path = "srl/static/pfp"
            os.makedirs(folder_path, exist_ok=True)
            
            file_name = f"{player}.jpg"
            file_path = os.path.join(folder_path, file_name)

            with open(file_path, "wb") as f:
                f.write(response.content)
        else:
            file_path = None

        cc = standardize_tag(player_data.get("location").get("country").get("code").replace("/","_")) if player_data.get("location") is not None and player_data.get("location").get("country") is not None and player_data.get("location").get("country").get("code") is not None and player_data.get("location").get("country").get("code") is not None else None 

        if isinstance(cc, str) and cc.startswith("ca-"):
            cc = "ca"

        with transaction.atomic():
            Players.objects.update_or_create(
                id          = player,
                defaults    = {
                    "name"          : player_data["names"]["international"],
                    "url"           : player_data["weblink"],
                    "countrycode"   : CountryCodes.objects.get(id=cc) if CountryCodes.objects.filter(id=cc).exists() else None,
                    "pfp"           : file_path,
                    "pronouns"      : player_data.get("pronouns") if player_data.get("pronouns") is not None else None,
                    "location"      : player_data.get("location").get("country").get("names").get("international") if player_data.get("location") is not None and player_data.get("location").get("country") is not None and player_data.get("location").get("country").get("name") is not None and player_data.get("location").get("country").get("name").get("international") is not None else None, 
                    "twitch"        : player_data.get("twitch").get("uri") if player_data.get("twitch") is not None and player_data.get("twitch").get("uri") is not None else None,
                    "youtube"       : player_data.get("youtube").get("uri") if player_data.get("youtube") is not None and player_data.get("youtube").get("uri") is not None else None,
                    "twitter"       : player_data.get("twitter").get("uri") if player_data.get("twitter") is not None and player_data.get("twitter").get("uri") is not None else None,
                }
            )

def invoke_runs(game_id,category,leaderboard,var_name=None,var_string=None):
    if len(leaderboard["runs"]) > 0:
        wr_records = leaderboard["runs"][0]
        pb_records = leaderboard["runs"][1:]
        wr_players = wr_records["run"]["players"]

        if wr_records["run"]["game"] in ["o6glkk8d","o1yjk541","9d38jey1"]:
            run_type = 25
        elif wr_records["run"]["level"] != None:
            run_type = 100
        else:
            run_type = 1000

        if wr_players != None:
            run_id     = wr_records["run"]["id"]
            wr_secs    = wr_records["run"]["times"]["primary_t"]
            points     = 25 if run_type == 25 else 100 if run_type == 100 else 1000

            try: wr_video = wr_records.get("run").get("videos").get("links")[0].get("uri") if wr_records.get("run").get("videos") is not None or wr_records.get("run").get("videos").get("text") != "N/A" else None
            except: wr_video = None

            player1 = wr_players[0].get("id")
            player2 = wr_players[1]["id"] if len(wr_players) > 1 and wr_players[1]["rel"] == "user" else None

            default = {
                "player"        : Players.objects.get(id=player1) if Players.objects.filter(id=player1).exists() else None,
                "game"          : GameOverview.objects.get(id=game_id),
                "category"      : Categories.objects.get(id=category["id"]),
                "subcategory"   : var_name,
                "values"        : var_string,
                "place"         : 1,
                "url"           : wr_records["run"]["weblink"],
                "video"         : wr_video,
                "date"          : wr_records["run"]["date"],
                "time"          : convert_time(wr_records["run"]["times"]["realtime_t"]) if wr_records["run"]["times"]["realtime_t"] > 0 else 0,
                "time_secs"     : wr_records["run"]["times"]["realtime_t"],
                "timenl"        : convert_time(wr_records["run"]["times"]["realtime_noloads_t"]) if wr_records["run"]["times"]["realtime_noloads_t"] > 0 else 0,
                "timenl_secs"   : wr_records["run"]["times"]["realtime_noloads_t"],
                "timeigt"       : convert_time(wr_records["run"]["times"]["ingame_t"]) if wr_records["run"]["times"]["ingame_t"] > 0 else 0,
                "timeigt_secs"  : wr_records["run"]["times"]["ingame_t"],
                "points"        : points,
                "platform"      : Platforms.objects.get(id=wr_records["run"]["system"]["platform"]) if Platforms.objects.filter(id=wr_records["run"]["system"]["platform"]).exists() else None,
                "emulated"      : wr_records["run"]["system"]["emulated"],
                "obsolete"      : False
            }

            if category["type"] == "per-game":
                default["player2"] = Players.objects.get(id=player2) if Players.objects.filter(id=player2).exists() else None

                with transaction.atomic():
                    MainRuns.objects.update_or_create(
                        id=run_id,
                        defaults=default
                    )
            else:
                default["level"] = Levels.objects.get(id=wr_records["run"]["level"])

                with transaction.atomic():
                    ILRuns.objects.update_or_create(
                        id=run_id,
                        defaults=default
                    )

            for player in wr_players:
                if player["rel"] != "guest":
                    invoke_players(leaderboard["players"]["data"],player["id"])

        for pb in pb_records:
            if pb["place"] > 0:
                pb_players = pb["run"]["players"]
                
                if pb_players != None:
                    for player in pb_players:
                        if player["rel"] != "guest":
                            invoke_players(leaderboard["players"]["data"],player["id"])

                    run_id = pb["run"]["id"]
                    player1 = pb_players[0].get("id")
                    player2 = pb_players[1]["id"] if len(pb_players) > 1 and pb_players[1]["rel"] == "user" else None

                    pb_secs   = pb["run"]["times"]["primary_t"]
                    points    = math.floor((0.008 * math.pow(math.e, (4.8284 * (wr_secs/pb_secs)))) * run_type)

                    videos = pb.get("run").get("videos")
                    pb_video = videos["links"][0]["uri"] if videos and videos.get("text") != "N/A" else None

                    #try: pb_video  = pb.get("run").get("videos").get("links")[0].get("uri") if pb.get("run").get("videos") is not None or pb.get("run").get("videos").get("text") != "N/A" else None
                    #except: pb_video = None

                    default = {
                        "player"        : Players.objects.get(id=player1) if Players.objects.filter(id=player1).exists() else None,
                        "game"          : GameOverview.objects.get(id=game_id),
                        "category"      : Categories.objects.get(id=category["id"]),
                        "subcategory"   : var_name,
                        "values"        : var_string,
                        "place"         : pb["place"],
                        "url"           : pb["run"]["weblink"],
                        "video"         : pb_video,
                        "date"          : pb["run"]["date"],
                        "time"          : convert_time(pb["run"]["times"]["realtime_t"]) if pb["run"]["times"]["realtime_t"] > 0 else 0,
                        "time_secs"     : pb["run"]["times"]["realtime_t"],
                        "timenl"        : convert_time(pb["run"]["times"]["realtime_noloads_t"]) if pb["run"]["times"]["realtime_noloads_t"] > 0 else 0,
                        "timenl_secs"   : pb["run"]["times"]["realtime_noloads_t"],
                        "timeigt"       : convert_time(pb["run"]["times"]["ingame_t"]) if pb["run"]["times"]["ingame_t"] > 0 else 0,
                        "timeigt_secs"  : pb["run"]["times"]["ingame_t"],
                        "points"        : points,
                        "platform"      : Platforms.objects.get(id=pb["run"]["system"]["platform"]) if Platforms.objects.filter(id=pb["run"]["system"]["platform"]).exists() else None,
                        "emulated"      : pb["run"]["system"]["emulated"],
                        "obsolete"      : False
                    }

                    if category["type"] == "per-game":
                        default["player2"] = Players.objects.get(id=player2) if Players.objects.filter(id=player2).exists() else None

                        with transaction.atomic():
                            MainRuns.objects.update_or_create(
                                id=run_id,
                                defaults=default
                            )
                    else:
                        default["level"] = Levels.objects.get(id=pb["run"]["level"])

                        with transaction.atomic():
                            ILRuns.objects.update_or_create(
                                id=run_id,
                                defaults=default
                            )

def invoke_players(players_data,player=None):
    for player_data in players_data:
        player_id = player_data.get("id")
        if player_id == player:
            if player_data["assets"]["image"]["uri"] != None:
                file_name = player_data["assets"]["image"]["uri"].split("v=")[1] + ".jpg"

                if not os.path.exists("srl/static/pfp/" + file_name):
                    response = requests.get(player_data["assets"]["image"]["uri"])

                    while response.status_code == 420 or response.status_code == 503:
                        time.sleep(60)
                        response = requests.get(player_data["assets"]["image"]["uri"])

                    folder_path = "srl/static/pfp"
                    os.makedirs(folder_path, exist_ok=True)

                    file_path = os.path.join(folder_path, file_name)

                    with open(file_path, "wb") as f:
                        f.write(response.content)
                else:
                    folder_path = "srl/static/pfp"
                    file_path = os.path.join(folder_path, file_name)
            else:
                file_path = None

            cc = standardize_tag(player_data.get("location").get("country").get("code").replace("/","_")) if player_data.get("location") is not None and player_data.get("location").get("country") is not None and player_data.get("location").get("country").get("code") is not None and player_data.get("location").get("country").get("code") is not None else None

            if cc is not None and cc.startswith("ca-"):
                cc = "ca"

            with transaction.atomic():
                Players.objects.update_or_create(
                    id          = player,
                    defaults = {
                        "name"        : player_data["names"]["international"],
                        "url"         : player_data["weblink"],
                        "countrycode" : CountryCodes.objects.get(id=cc) if CountryCodes.objects.filter(id=cc).exists() else None,
                        "pfp"         : file_path,
                        "pronouns"    : player_data.get("pronouns") if player_data.get("pronouns") is not None else None,
                        "location"    : player_data.get("location").get("country").get("names").get("international") if player_data.get("location") is not None and player_data.get("location").get("country") is not None and player_data.get("location").get("country").get("name") is not None and player_data.get("location").get("country").get("name").get("international") is not None else None,
                        "twitch"      : player_data.get("twitch").get("uri") if player_data.get("twitch") is not None and player_data.get("twitch").get("uri") is not None else None,
                        "youtube"     : player_data.get("youtube").get("uri") if player_data.get("youtube") is not None and player_data.get("youtube").get("uri") is not None else None,
                        "twitter"     : player_data.get("twitter").get("uri") if player_data.get("twitter") is not None and player_data.get("twitter").get("uri") is not None else None,
                    }
                )

@sync_to_async
def import_obsolete(player):
    from api.tasks import add_run

    run_data = src_api(f"https://www.speedrun.com/api/v1/runs?user={player}&max=200",True)

    if isinstance(run_data,dict):
        all_runs = run_data["data"]
        offset   = 0

        while run_data["pagination"]["max"] == run_data["pagination"]["size"]:
            offset += 200
            run_data = src_api(f"https://www.speedrun.com/api/v1/runs?user={player}&max=200&offset={offset}?embed=players",True)
            all_runs.extend(run_data["data"])

        i = 0
        for run in all_runs:
            if GameOverview.objects.filter(id=run["game"]).exists():
                if len(MainRuns.objects.filter(id=run["id"])) == 0 and len(ILRuns.objects.filter(id=run["id"])) == 0:
                    try:
                        if run["level"]:
                            lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run['game']}/level/{run['level']}/{run['category']}?embed=game,category,level,players,variables")
                        elif len(run["values"]) > 0:
                            lb_variables = ""
                            for key, value in run["values"].items():
                                lb_variables += f"var-{key}={value}&"

                            lb_variables = lb_variables.rstrip("&")

                            lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run['game']}/category/{run['category']}?{lb_variables}&embed=game,category,level,players,variables")
                        else:
                            lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run['game']}/category/{run['category']}?embed=game,category,level,players,variables")
                        
                        if isinstance(lb_info,dict):
                            add_run(lb_info["game"]["data"],run,lb_info["category"]["data"],lb_info["level"]["data"],run["values"],True,False)

                            print(f"DEBUG: Added {run['id']} without issue...")
                    except Exception as e:
                        print(e,lb_info["game"]["data"]["name"])

@sync_to_async
def import_srltimes(run):
    print(run)
    run_info = src_api(f"https://speedrun.com/api/v1/runs/{run}")

    #try: run_video = run_info.get("videos").get("links")[0].get("uri") if run_info.get("videos") is not None or run_info.get("videos").get("text") != "N/A" else None
    #except: run_video = None

    if isinstance(run_info,dict):
        videos = run_info.get("run").get("videos")
        run_video = videos["links"][0]["uri"] if videos and videos.get("text") != "N/A" else None

        if MainRuns.objects.filter(id=run).exists():
            with transaction.atomic():
                MainRuns.objects.update_or_create(
                    id          = run,
                    defaults    = {
                        "video"       : run_video,
                        "time"        : convert_time(run_info["times"]["realtime_t"]) if run_info["times"]["realtime_t"] > 0 else 0,
                        "time_secs"   : run_info["times"]["realtime_t"],
                        "timenl"      : convert_time(run_info["times"]["realtime_noloads_t"]) if run_info["times"]["realtime_noloads_t"] > 0 else 0,
                        "timenl_secs" : run_info["times"]["realtime_noloads_t"],
                        "timeigt"     : convert_time(run_info["times"]["ingame_t"]) if run_info["times"]["ingame_t"] > 0 else 0,
                        "timeigt_secs": run_info["times"]["ingame_t"],
                        "emulated"    : run_info["system"]["emulated"],
                    }
                )

def invoke_timereview():
    for game in GameOverview.objects.all():
        pref_time   = game.defaulttime
        main        = MainRuns.objects.all()
        categories  = main.filter(game_id=game.id).values("subcategory").distinct()

        run_type = 25 if game.id in ["o6glkk8d","o1yjk541","9d38jey1"] else 1000

        for category in categories:
            runs        = main.filter(game_id=game.id,subcategory=category).order_by("-date")
            wr_run      = runs.first()
            latest_run  = MainRunTimeframe.objects.filter(run_id__player__id=run.player.id,end_date__isnull=True).order_by("-start_date").first()

            for run in runs[1:]:
                if pref_time == "realtime":
                    wr_time, run_time, latest_time = wr_run.time_secs, run.time_secs, latest_run.time_secs
                elif pref_time == "realtime_noloads":
                    wr_time, run_time, latest_time = wr_run.timenl_secs, run.timenl_secs, latest_run.timenl_secs
                elif pref_time == "ingame":
                    wr_time, run_time, latest_time = wr_run.timeigt_secs, run.timeigt_secs, latest_run.timeigt_secs
                
                with transaction.atomic():
                    MainRunTimeframe.objects.create(
                        run_id      = wr_run.id,
                        start_date  = wr_run.date,
                        points      = run_type,
                    )
                    
                    if wr_time > run_time:
                        if len(latest_time) > 0:
                            if run_time > latest_time:
                                latest_run.update(end_date=run.date)
                                MainRunTimeframe.objects.create(
                                    run_id      = run.id,
                                    start_date  = run.date,
                                    points      = math.floor((0.008 * math.pow(math.e, (4.8284 * (wr_time / run_time)))) * run_type),
                                )

                    else:
                        MainRunTimeframe.objects.update_or_create(
                            run_id   = wr_run.id,
                            defaults = {
                                "start_date"    : wr_run.date,
                                "end_date"      : run.date,
                                "points"        : run_type,
                            }
                        )
                        wr_run = run

                        for archived_run in MainRunTimeframe.objects.filter(run_id__subcategory=run.subcategory,end_date__isNull=True).order_by("-start_date"):
                            archived_run.update(end_date=wr_run.date)
                            if pref_time == "realtime":
                                wr_time, run_time= wr_run.time_secs, archived_run.time_secs
                            elif pref_time == "realtime_noloads":
                                wr_time, run_time= wr_run.timenl_secs, archived_run.timenl_secs
                            elif pref_time == "ingame":
                                wr_time, run_time= wr_run.timeigt_secs, archived_run.timeigt_secs

                            MainRunTimeframe.objects.create(
                                run_id        = archived_run.id,
                                start_date    = wr_run.date,
                                points        = math.floor((0.008 * math.pow(math.e, (4.8284 * (wr_time / run_time)))) * run_type),
                            )