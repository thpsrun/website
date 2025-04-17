from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse

from .models import (
    Awards,
    Categories,
    CountryCodes,
    Games,
    Levels,
    NowStreaming,
    Platforms,
    Players,
    Runs,
    RunVariableValues,
    Series,
    Variables,
    VariableValues,
)
from .views import (
    ImportObsoleteView,
    RefreshGameRunsView,
    UpdateGameRunsView,
    UpdateGameView,
    UpdatePlayerView,
    UpdateSeriesView,
)


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
            path("update-series/",
                self.admin_site.admin_view(UpdateSeriesView.as_view()), name="update_series"),
        ]
        return custom_urls + urls


class GameAdmin(admin.ModelAdmin):
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
            path("update-game/",
                self.admin_site.admin_view(UpdateGameView.as_view()), name="update_game"),
            path("update-game-runs/",
                self.admin_site.admin_view(UpdateGameRunsView.as_view()), name="update_game_runs"),
            path("refresh-game-runs/",
                self.admin_site.admin_view(RefreshGameRunsView.as_view()), name="refresh_game_runs")
        ]
        return custom_urls + urls


class DefaultAdmin(admin.ModelAdmin):
    list_display    = ["name"]
    search_fields   = ["name"]


class CategoriesAdmin(admin.ModelAdmin):
    list_display    = ["name"]
    search_fields   = ["id"]
    list_filter     = ["game"]


class RunVariableValuesInline(admin.TabularInline):
    model = RunVariableValues
    extra = 1
    autocomplete_fields = ["variable", "value"]


class SpeedrunAdmin(admin.ModelAdmin):
    list_display    = ["id"]
    search_fields   = ["id"]
    list_filter     = ["runtype", "obsolete", "game", "platform"]
    inlines         = [RunVariableValuesInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ["category", "level"]:
            if request.resolver_match and "object_id" in request.resolver_match.kwargs:
                run_id = request.resolver_match.kwargs["object_id"]
                try:
                    run = Runs.objects.get(id=run_id)
                    if db_field.name == "category":
                        kwargs["queryset"] = Categories.objects.filter(game=run.game)
                    elif db_field.name == "level":
                        kwargs["queryset"] = Levels.objects.filter(game=run.game)
                except Runs.DoesNotExist:
                    pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PlayersAdmin(admin.ModelAdmin):
    list_display    = ["name"]
    actions         = ["update_player", "import_obsolete"]
    search_fields   = ["name"]

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
            path("update-player/",
                self.admin_site.admin_view(UpdatePlayerView.as_view()), name="update_player"),
            path("import-obsolete/",
                self.admin_site.admin_view(ImportObsoleteView.as_view()), name="import_obsolete")
        ]
        return custom_urls + urls


admin.site.register(Series, SeriesAdmin)
admin.site.register(Games, GameAdmin)
admin.site.register(Awards, DefaultAdmin)
admin.site.register(CountryCodes, DefaultAdmin)
admin.site.register(Categories, CategoriesAdmin)
admin.site.register(Levels, CategoriesAdmin)
admin.site.register(Variables, DefaultAdmin)
admin.site.register(VariableValues, DefaultAdmin)
admin.site.register(RunVariableValues)
admin.site.register(Runs, SpeedrunAdmin)
admin.site.register(Players, PlayersAdmin)
admin.site.register(Platforms, DefaultAdmin)
admin.site.register(NowStreaming)
