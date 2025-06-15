# All of the below is a work-in-progress for the eventual Historical Leaderboards update
# Feel free to ignore everything below for now!
# ##################################################################################################


""" def MonthlyLeaderboard(request,year,month=None):
    def add_run(main_runs,il_runs,type,month=None):
        export = {}
        for run in main_runs:
            if run["player__name"] in export:
                export[run["player__name"]]["points"] += run["points"]
            else:
                try:
                    export[run["player__name"]] = {"nickname": run["player__nickname"],
                    "countrycode": run["player__countrycode__id"],"points": run["points"],"runs": 1}
                except:
                    export[run["player__name"]] = {"nickname": run["player__nickname"],
                    "countrycode": None, "points": run["points"], "runs": 1}

        for run in il_runs:
            if run["player__name"] in export:
                export[run["player__name"]]["points"] += run["points"]
            else:
                try:
                    export[run["player__name"]] = {"nickname": run["player__nickname"],
                    "countrycode": run["player__countrycode__id"], "points": run["points"],
                    "runs": 1}
                except:
                    export[run["player__name"]] = {"nickname": run["player__nickname"],
                    "countrycode": None, "points": run["points"], "runs": 1}

        if type == 1:
            for player in export:
                export[player]["runs"] = len(MainRuns.objects
                                        .filter(date__year=year,player__name=player))
                export[player]["runs"] += len(ILRuns.objects
                                        .filter(date__year=year,player__name=player))
        else:
            for player in export:
                export[player]["runs"] = len(MainRuns.objects
                                    .filter(date__year=year,date__month=month,player__name=player))
                export[player]["runs"] += len(ILRuns.objects
                                    .filter(date__year=year,date__month=month,player__name=player))

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
            main_runs   = MainRuns.objects.filter(date__year=year)
                        .values("player__name","player__id","player__countrycode__id",
                                "player__nickname","points").annotate(max_time_date=Max("date"))
                        .filter(date=F("max_time_date"))
            il_runs     = ILRuns.objects.filter(date__year=year)
                        .values("player__name","player__id","player__countrycode__id",
                                "player__nickname","points").annotate(max_time_date=Max("date"))
                        .filter(date=F("max_time_date"))

            export = add_run(main_runs,il_runs,1)
            export = sorted(export.items(), key=lambda x: x[1]["points"], reverse=True)
            export = calculate_ranks(export)

            return export
        else:
            player_totals = {}
            for month in months_query:
                main_runs   = (MainRuns.objects.filter(date__year=year,date__month=month)
                            .values("player__name","player__id","player__countrycode__id",
                                    "player__nickname","points").annotate(max_time_date=Max("date"))
                            .filter(date=F("max_time_date")))
                il_runs     = (ILRuns.objects.filter(date__year=year,date__month=month)
                            .values("player__name","player__id","player__countrycode__id",
                                    "player__nickname","points").annotate(max_time_date=Max("date"))
                            .filter(date=F("max_time_date")))

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
        "player_totals" : (init_leaderboard(year,months_output) if month != None
                            else init_leaderboard(year,None)),
        "months"        : sorted(months_output.items(), key=lambda x: x[1], reverse=True),
        "year_query"    : year,
        "month_query"   : month if month != None else None,
    }

    return render(request, "srl/monthly_leaderboard.html", context)
    #except:
        #return redirect("/overall/2024/1") """
