from django.core.exceptions import ValidationError
from django.db import models
from django_resized import ResizedImageField


### VALIDATORS
def validate_image(image):
    file_size   = image.file.size
    file_width  = image.file.image._size[0]
    file_height = image.file.image._size[1] 

    limit_mb = 3
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max size of file is {limit_mb} MB")
    elif file_width != file_height:
        raise ValidationError(f"File width and height must match. Current: {file_width}x{file_height}")

### MODEL CLASSES
class Series(models.Model):
    class Meta:
        verbose_name_plural = "Series"

    id      = models.CharField(max_length=10, primary_key=True, verbose_name="Series ID")
    name    = models.CharField(max_length=20, verbose_name="Name")
    url     = models.URLField(verbose_name="URL")

    def __str__(self):
        return self.name

class Platforms(models.Model):
    class Meta:
        verbose_name_plural = "Platforms"
        ordering = ["name"]

    id      = models.CharField(max_length=10, primary_key=True, verbose_name="Platform ID")
    name    = models.CharField(max_length=30, verbose_name="Name")

    def __str__(self):
        return self.name

class Games(models.Model):
    class Meta:
        verbose_name_plural = "Games"
        ordering = ["release"]

    LeaderboardChoices = [
        ("realtime", "RTA"),
        ("realtime_noloads", "LRT"),
        ("ingame", "IGT"),
    ]

    id              = models.CharField(max_length=10, primary_key=True, verbose_name="SRL Game ID")
    name            = models.CharField(max_length=55, verbose_name="Name")
    slug            = models.CharField(max_length=20, verbose_name="Abbreviation/Slug")
    twitch          = models.CharField(max_length=55, verbose_name="Twitch Name", null=True, blank=True)
    release         = models.DateField(verbose_name="Release Date")
    boxart          = models.URLField(verbose_name="Box Art URL")
    defaulttime     = models.CharField(verbose_name="Default Time", choices=LeaderboardChoices, default="realtime")
    idefaulttime    = models.CharField(
                    verbose_name="ILs Default Time",
                    choices=LeaderboardChoices,
                    default="realtime",
                    help_text="Sometimes leaderboards have one timing standard for full game speedruns and another standard for ILs. This setting lets you change the game-specific IL timing method.<br />NOTE: This defaults to RTA upon a game being created and must be set manually."
    )
    platforms       = models.ManyToManyField(Platforms, verbose_name="Platforms")
    pointsmax       = models.IntegerField(
                    verbose_name="Full Game WR Point Maximum",
                    default=1000,
                    help_text="Default is 1000; 25 if this game contains the name \"Category Extension\". This is the maximum total of points a full-game speedrun receives if it is the world record. All lower-ranked speedruns recieve less based upon an algorithmic formula.<br />\
                    NOTE: Changing this value will ONLY affect new runs. If you change this value, you will need to reset runs for this game from the admin panel."
    )
    ipointsmax      = models.IntegerField(
                    verbose_name="IL WR Point Maximum",
                    default=100,
                    help_text="Default is 100; 25 if this game contains the name \"Category Extension\". This is the maximum total of points an IL speedrun receives if it is the world record. All lower-ranked speedruns recieve less based upon an algorithmic formula.<br />\
                    NOTE: Changing this value will ONLY affect new runs. If you change this value, you will need to reset runs for this game from the admin panel."
    )

    def __str__(self):
        return self.name

class Categories(models.Model):
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    id      = models.CharField(max_length=10, primary_key=True, verbose_name="Category ID")
    game    = models.ForeignKey(Games, verbose_name="Linked Game", null=True, on_delete=models.SET_NULL)
    name    = models.CharField(max_length=50, verbose_name="Name")
    type    = models.CharField(max_length=15, verbose_name="Type (IL/FG)")
    url     = models.URLField(verbose_name="URL")
    hidden  = models.BooleanField(verbose_name="Hide Category", default=False)

    def __str__(self):
        return self.name

class Levels(models.Model):
    class Meta:
        verbose_name_plural = "Levels"
        ordering = ["name"]

    id      = models.CharField(max_length=10, primary_key=True, verbose_name="Level ID")
    game    = models.ForeignKey(Games, verbose_name="Linked Game", null=True, on_delete=models.SET_NULL)
    name    = models.CharField(max_length=75, verbose_name="Name")
    url     = models.URLField(verbose_name="URL")

    def __str__(self):
        return self.name

class Variables(models.Model):
    class Meta:
        verbose_name_plural = "Variables"

    id          = models.CharField(max_length=10, primary_key=True, verbose_name="Variable ID")
    name        = models.CharField(max_length=50, verbose_name="Name")
    game        = models.ForeignKey(Games, verbose_name="Linked Game", null=True, on_delete=models.SET_NULL)
    cat         = models.ForeignKey(Categories, verbose_name="Category", null=True, blank=True, on_delete=models.SET_NULL)
    all_cats    = models.BooleanField(
                verbose_name="All Categories",
                default=False,
                help_text="When checked,  this means that the variable will work across all categories of the game in the \"Game\" field. Note: The \"Linked Category\" must be blank."
    )
    scope       = models.CharField(max_length=12, verbose_name="Scope (FG/IL)")
    hidden      = models.BooleanField(verbose_name="Hide Variables", default=False)

    def clean(self):
        if (self.cat is None) and (not self.all_cats):
            raise ValidationError("\"Linked Category\" must have a value OR \"All Categories\" must be checked.")
        elif self.cat == "all":
            raise ValidationError("\"all\" is not a valid category value; if this variable is for all categories,  please check \"All Categories\".")
        elif self.cat and self.all_cats:
            raise ValidationError("If \"All Categories\" is checked,  \"Linked Category\" field should be empty.")

    def __str__(self):
        return self.name

class VariableValues(models.Model):
    class Meta:
        verbose_name_plural = "Variable Values"

    var     = models.ForeignKey(Variables, verbose_name="Linked Variable", null=True, on_delete=models.SET_NULL)
    name    = models.CharField(max_length=50, verbose_name="Name")
    value   = models.CharField(max_length=10, primary_key=True, verbose_name="Value ID")
    hidden  = models.BooleanField(verbose_name="Hide Value", default=False)

    def __str__(self):
        return self.name

class Awards(models.Model):
    class Meta:
        verbose_name_plural = "Awards"
    
    name        = models.CharField(max_length=50, verbose_name="Award Name", unique=True)
    image       = ResizedImageField(
                size=[64, 64], 
                upload_to="srl/static/srl/imgs/awards", 
                verbose_name="Image", 
                validators=[validate_image], 
                null=True, 
                blank=True, 
                help_text="Note: Images must be at least 64px in size, must be a square (height and width must match), and the max filesize is 3MB."
    )
    description = models.CharField(max_length=500, verbose_name="Award Description", blank=True, null=True)
    unique      = models.BooleanField(
                verbose_name="Unique Award",
                default=False,
                help_text="When checked, this award will be given the 'unique' tag - enabling special effects for the award on the profile page."
    )

    def __str__(self):
        return self.name

class CountryCodes(models.Model):
    class Meta:
        verbose_name_plural = "Country Codes"
        ordering = ["name"]

    id      = models.CharField(max_length=10, primary_key=True, verbose_name="Country Code ID")
    name    = models.CharField(max_length=50, verbose_name="Country Name")

    def __str__(self):
        return self.name

class Players(models.Model):
    class Meta:
        verbose_name_plural = "Players"
        ordering = ["name"]
    
    id          = models.CharField(max_length=10, primary_key=True, verbose_name="Player ID")
    name        = models.CharField(max_length=30, verbose_name="Name", default="Anonymous")
    nickname    = models.CharField(
                max_length=30,
                verbose_name="Nickname",
                blank=True,
                null=True,
                help_text="This is a special field where,  if a nickname is given,  it will be shown versus their SRC name."
    )
    url         = models.URLField(verbose_name="URL")
    countrycode = models.ForeignKey(CountryCodes, verbose_name="Country Code", blank=True, null=True, on_delete=models.SET_NULL)
    pfp         = models.CharField(max_length=50, verbose_name="Profile Picture URL", blank=True, null=True)
    pronouns    = models.CharField(max_length=20, verbose_name="Pronouns", blank=True, null=True)
    twitch      = models.CharField(max_length=75, verbose_name="Twitch", blank=True, null=True)
    youtube     = models.CharField(max_length=100, verbose_name="YouTube", blank=True, null=True)
    twitter     = models.CharField(max_length=40, verbose_name="Twitter", blank=True, null=True)
    bluesky     = models.CharField(max_length=75, verbose_name="Bluesky", blank=True, null=True)
    ex_stream   = models.BooleanField(
                verbose_name="Stream Exception",
                default=False,
                help_text="When checked, this player can be filtered out from appearing on stream bots or pages."
    )
    awards      = models.ManyToManyField(
                Awards,
                verbose_name="Awards",
                default=False,
                blank=True,
                help_text="Earned awards can be selected here. All selected awards will appear on the Player's profile."
    )

    def __str__(self):
        return self.name

class RunQuerySet(models.QuerySet):
    def main(self):
        return self.filter(runtype="main")

    def il(self):
        return self.filter(runtype="il")

class RunManager(models.Manager):
    def get_queryset(self):
        return RunQuerySet(self.model, using=self._db)

    def main(self):
        return self.get_queryset().main()

    def il(self):
        return self.get_queryset().il()

class Runs(models.Model):
    class Meta:
        verbose_name_plural = "Runs"

    objects = RunManager()

    statuschoices = [
        ("verified", "Verified"),
        ("new", "Unverified"),
        ("rejected", "Rejected"),
    ]

    runtype = [
        ("main", "Full Game"),
        ("il", "Individual Level"),
    ]

    id              = models.CharField(max_length=10, primary_key=True, verbose_name="Run ID")
    runtype         = models.CharField(max_length=5, choices=runtype, verbose_name="Full-Game or IL")
    game            = models.ForeignKey(Games, verbose_name="Game", on_delete=models.CASCADE)
    category        = models.ForeignKey(Categories, verbose_name="Category", blank=True, null=True, on_delete=models.SET_NULL)
    level           = models.ForeignKey(Levels, verbose_name="Level", blank=True, null=True, on_delete=models.SET_NULL)
    subcategory     = models.CharField(max_length=100, verbose_name="Subcategory Name", blank=True, null=True)
    variables       = models.ManyToManyField(Variables, verbose_name="Variables", through="RunVariableValues", related_name="runs")
    player          = models.ForeignKey(Players, verbose_name="Player", blank=True, null=True, on_delete=models.SET_NULL, related_name="runs_p1")
    player2         = models.ForeignKey(Players, verbose_name="Player 2", blank=True, null=True, on_delete=models.SET_NULL, related_name="runs_p2")
    place           = models.IntegerField(verbose_name="Placing")
    url             = models.URLField(verbose_name="URL")
    video           = models.URLField(verbose_name="Video", blank=True, null=True)
    date            = models.DateTimeField(verbose_name="Submitted Date", blank=True, null=True)
    v_date          = models.DateTimeField(verbose_name="Verified Date", blank=True, null=True)
    time            = models.CharField(max_length=25, verbose_name="RTA Time", blank=True, null=True)
    time_secs       = models.FloatField(verbose_name="RTA Time (Seconds)", blank=True, null=True)
    timenl          = models.CharField(max_length=25, verbose_name="LRT Time", blank=True, null=True)
    timenl_secs     = models.FloatField(verbose_name="LRT Time (Seconds)", blank=True, null=True)
    timeigt         = models.CharField(max_length=25, verbose_name="IGT Time", blank=True, null=True)
    timeigt_secs    = models.FloatField(verbose_name="IGT Time (Seconds)", blank=True, null=True)
    points          = models.IntegerField(verbose_name="Packle Points", default=0)
    platform        = models.ForeignKey(Platforms, verbose_name="Platform", blank=True, null=True, on_delete=models.SET_NULL)
    emulated        = models.BooleanField(verbose_name="Emulated?", default=False)
    vid_status      = models.CharField(
                    verbose_name="SRC Status",
                    choices=statuschoices,
                    default="verified",
                    help_text="This is the current status of the run, according to Speedrun.com. It should be updated whenever the run is approved. Runs set as \"Unverified\" or \"Rejected\" do not appear anywhere on this site."
    )
    obsolete        = models.BooleanField(
                    verbose_name="Obsolete?",
                    default=False,
                    help_text="When True, the run will be considered obsolete. Points will not count towards the player's total."
    )
    arch_video      = models.URLField(
                    verbose_name="Archived Video URL",
                    blank=True,
                    null=True,
                    help_text="Optional field. If you have a mirrored link to a video, you can input it here."
    )

    def __str__ (self):
        return self.id

    def set_variables(self, variable_value_map: dict):
        for variable, value in variable_value_map.items():
            VariableValues.objects.create(run=self, variable=variable, value=value)

class RunVariableValues(models.Model):    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["run", "variable"], name="unique_variable_and_value")
        ]

    run         = models.ForeignKey(Runs, on_delete=models.CASCADE)
    variable    = models.ForeignKey(Variables, on_delete=models.CASCADE)
    value       = models.ForeignKey(VariableValues, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.run} - {self.variable.name}: {self.value.name}"

class NowStreaming(models.Model):
    class Meta:
        verbose_name_plural = "Streaming"

    streamer    = models.OneToOneField(Players, primary_key=True, verbose_name="Streamer", on_delete=models.CASCADE)
    game        = models.ForeignKey(Games, verbose_name="Game", null=True, on_delete=models.SET_NULL)
    title       = models.CharField(max_length=100, verbose_name="Twitch Title")
    offline_ct  = models.IntegerField(
                verbose_name="Offline Count",
                help_text="In some situations, bots or the Twitch API can mess up. To help users, you can use this counter to countup the number of attempts to see if the runner is offline. After a certain number is hit, you can do something like remove embeds and/or remove this record."
    )
    stream_time = models.DateTimeField(verbose_name="Started Stream")

    def __str__(self):
        return f"Streaming: {self.streamer.name}"


""" 
### Disabled for now; will return when working on Historical Points.
class MainRunTimeframe(models.Model):
    def __str__(self):
        return "Run ID: " + self.run_id + " - " + self.timeframe
    
    class Meta:
        verbose_name_plural = "Main Run Timeframes"

    id          = models.AutoField(primary_key=True)
    run_id      = models.ForeignKey("MainRuns", max_length=10, verbose_name="Run ID", null=True, on_delete=models.SET_NULL)
    start_date  = models.DateTimeField(verbose_name="Approved Date")
    end_date    = models.DateTimeField(verbose_name="Beaten Date")
    points      = models.IntegerField(verbose_name="Packle Points", default=0) """