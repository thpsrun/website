"""
### Disabled for now; will return when working on Historical Points.
class MainRunTimeframe(models.Model):
    def __str__(self):
        return "Run ID: " + self.run_id + " - " + self.timeframe

    class Meta:
        verbose_name_plural = "Main Run Timeframes"

    id          = models.AutoField(primary_key=True)
    run_id      = models.ForeignKey("MainRuns", max_length=10, verbose_name="Run ID",
                                    null=True, on_delete=models.SET_NULL)
    start_date  = models.DateTimeField(verbose_name="Approved Date")
    end_date    = models.DateTimeField(verbose_name="Beaten Date")
    points      = models.IntegerField(verbose_name="Packle Points", default=0) """
