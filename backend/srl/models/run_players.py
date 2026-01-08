from django.db import models


class RunPlayers(models.Model):
    """
    Through model for the many-to-many relationship between Runs and Players.

    This replaces the previous player/player2 fields on the Runs model to allow
    for any number of players per run (including anonymous runs with no players).
    """

    class Meta:
        verbose_name = "Run Player"
        verbose_name_plural = "Run Players"
        constraints = [
            models.UniqueConstraint(
                fields=["run", "player"],
                name="unique_run_player",
            )
        ]
        ordering = ["run", "player__name"]

    run = models.ForeignKey(
        "Runs", on_delete=models.CASCADE, related_name="run_players"
    )
    player = models.ForeignKey(
        "Players", on_delete=models.CASCADE, related_name="player_runs"
    )

    order = models.PositiveSmallIntegerField(
        default=1,
        help_text="Order of this player in the run (1 for primary player, 2 for secondary, etc.)",
    )

    def __str__(self):
        return f"{self.run.id} - {self.player.name} (#{self.order})"
