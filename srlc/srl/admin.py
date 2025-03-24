from django.contrib import admin
from django.urls import reverse
from django.shortcuts import redirect
from django.urls import path
from .models import Series,GameOverview,Categories,Levels,Variables,VariableValues,MainRuns,ILRuns,Players,CountryCodes,Awards,Platforms
from .views import UpdateSeriesView,UpdateGameView,UpdateGameRunsView,UpdatePlayerView,RefreshGameRunsView,ImportObsoleteView,ImportSRLTimes

class SeriesAdmin(admin.ModelAdmin):
    list_display    = ["name"]
    actions         = ["update_series"]

    def update_series(self, request, queryset):
        series_ids = [obj.id for obj in queryset]
        return redirect(reverse("admin:update_series") + f"?series_ids={','.join(series_ids)}")
    
    update_series.short_description = "Initialize Series Data"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("update-series/", self.admin_site.admin_view(UpdateSeriesView.as_view()), name="update_series"),
        ]
        return custom_urls + urls

class GameOverviewAdmin(admin.ModelAdmin):
    list_display    = ["name"]
    actions         = ["update_game", "update_game_runs", "refresh_game_runs"]
    search_fields   = ["name"]

    def update_game(self, request, queryset):
        game_ids = [obj.id for obj in queryset]
        return redirect(reverse("admin:update_game") + f"?game_ids={','.join(game_ids)}")
    
    update_game.short_description = "Update Game Metadata"
    
    def update_game_runs(self, request, queryset):
        game_ids = [obj.id for obj in queryset]
        return redirect(reverse("admin:update_game_runs") + f"?game_ids={','.join(game_ids)}")
    
    update_game_runs.short_description = "Update Game Runs"

    def refresh_game_runs(self, request, queryset):
        game_ids = [obj.id for obj in queryset]
        return redirect(reverse("admin:refresh_game_runs") + f"?game_ids={','.join(game_ids)}")
    
    refresh_game_runs.short_description = "Reset Game Runs"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("update-game/", self.admin_site.admin_view(UpdateGameView.as_view()), name="update_game"),
            path("update-game-runs/", self.admin_site.admin_view(UpdateGameRunsView.as_view()), name="update_game_runs"),
            path("refresh-game-runs/", self.admin_site.admin_view(RefreshGameRunsView.as_view()), name="refresh_game_runs"),
        ]
        return custom_urls + urls
    
class DefaultAdmin(admin.ModelAdmin):
    list_display        = ["name"]
    search_fields       = ["name"]

class CategoriesAdmin(admin.ModelAdmin):
    list_display        = ["name"]
    search_fields       = ["id"]
    list_filter         = ["game"]

class SpeedrunAdmin(admin.ModelAdmin):
    list_display        = ["id"]
    search_fields       = ["id"]
    list_filter         = ["obsolete","game","platform"]
    """ actions             = ["update_runs"]

    def update_runs(self, request, queryset):
        run_ids = [obj.id for obj in queryset]
        return redirect(reverse("admin:update_runs") + f"?run_ids={','.join(run_ids)}")

    update_runs.short_description = "Update Run Metadata"


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("update-runs/", self.admin_site.admin_view(ImportSRLTimes.as_view()), name="update_runs"),
        ]
        return custom_urls + urls """

class PlayersAdmin(admin.ModelAdmin):
    list_display        = ["name"]
    actions             = ["update_player","import_obsolete"]
    search_fields       = ["name"]

    def update_player(self, request, queryset):
        player_ids = [obj.id for obj in queryset]
        return redirect(reverse("admin:update_player") + f"?player_ids={','.join(player_ids)}")
    
    def import_obsolete(self, request, queryset):
        player_ids = [obj.id for obj in queryset]
        return redirect(reverse("admin:import_obsolete") + f"?player_ids={','.join(player_ids)}")
    
    update_player.short_description = "Update Player Metadata"
    import_obsolete.short_description = "Force Add Obsolete Runs"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("update-player/", self.admin_site.admin_view(UpdatePlayerView.as_view()), name="update_player"),
            path("import-obsolete/", self.admin_site.admin_view(ImportObsoleteView.as_view()), name="import_obsolete")
        ]
        return custom_urls + urls

admin.site.register(Series, SeriesAdmin)
admin.site.register(GameOverview, GameOverviewAdmin)
admin.site.register(Awards, DefaultAdmin) 
admin.site.register(CountryCodes, DefaultAdmin)
admin.site.register(Categories, CategoriesAdmin)
admin.site.register(Levels, CategoriesAdmin)
admin.site.register(Variables, DefaultAdmin)
admin.site.register(VariableValues, DefaultAdmin)
admin.site.register(MainRuns, SpeedrunAdmin)
admin.site.register(ILRuns, SpeedrunAdmin)
admin.site.register(Players, PlayersAdmin)
admin.site.register(Platforms, DefaultAdmin)