from django.db import models
from django_resized import ResizedImageField
from django.core.exceptions import ValidationError

###################
# VALIDATORS
###################
def validate_image(image):
    file_size   = image.file.size
    file_width  = image.file.image._size[0]
    file_height = image.file.image._size[1] 

    limit_mb = 3
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max size of file is {limit_mb} MB")
    elif file_width != file_height:
        raise ValidationError(f"File width and height must match. Current: {file_width}x{file_height}")

###################
# MODEL CLASSES
###################
class Series(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Series"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Series ID")
    name        = models.CharField(max_length=20,verbose_name="Name")
    url         = models.URLField(verbose_name="URL")

class Platforms(models.Model):
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Platforms"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Platform ID")
    name        = models.CharField(max_length=30,verbose_name="Name")

class GameOverview(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Game Overview"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="SRL Game ID")
    name        = models.CharField(max_length=35,verbose_name="Name")
    abbr        = models.CharField(max_length=20,verbose_name="Abbreviation")
    release     = models.DateField(verbose_name="Release Date")
    boxart      = models.URLField(verbose_name="Box Art URL")
    defaulttime = models.CharField(max_length=20,verbose_name="Default Time")
    platforms   = models.ManyToManyField(Platforms,verbose_name="Platforms")

class Categories(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Categories"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Category ID")
    game        = models.ForeignKey(GameOverview,verbose_name="Linked Game",null=True,on_delete=models.SET_NULL)
    name        = models.CharField(max_length=50,verbose_name="Name")
    type        = models.CharField(max_length=15,verbose_name="Type (IL/FG)")
    url         = models.URLField(verbose_name="URL")
    hidden      = models.BooleanField(verbose_name="Hide Category",default=False)

class Levels(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Levels"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Level ID")
    game        = models.ForeignKey(GameOverview,verbose_name="Linked Game",null=True,on_delete=models.SET_NULL)
    name        = models.CharField(max_length=75,verbose_name="Name")
    url         = models.URLField(verbose_name="URL")

class Variables(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Variables"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Variable ID")
    name        = models.CharField(max_length=50,verbose_name="Name")
    game        = models.ForeignKey(GameOverview,verbose_name="Linked Game",null=True,on_delete=models.SET_NULL)
    cat         = models.ForeignKey(Categories,verbose_name="Category",null=True,on_delete=models.SET_NULL)
    all_cats    = models.BooleanField(
                verbose_name="All Categories",
                default=False,
                help_text="When checked, this means that the variable will work across all categories of the game in the \"Game\" field. Note: The \"Linked Category\" must be blank."
    )
    scope       = models.CharField(max_length=12,verbose_name="Scope (FG/IL)")
    hidden      = models.BooleanField(verbose_name="Hide Variables",default=False)

    def clean(self):
        if (self.cat == None) and (self.all_cats == False):
            raise ValidationError("\"Linked Category\" must have a value OR \"All Categories\" must be checked.")
        elif self.cat == "all":
            raise ValidationError("\"all\" is not a valid category value; if this variable is for all categories, please check \"All Categories\".")
        elif self.cat and self.all_cats:
            raise ValidationError("If \"All Categories\" is checked, \"Linked Category\" field should be empty.")

class VariableValues(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Variable Values"

    var         = models.ForeignKey(Variables,verbose_name="Linked Variable",null=True,on_delete=models.SET_NULL)
    name        = models.CharField(max_length=50,verbose_name="Name")
    value       = models.CharField(max_length=10,primary_key=True,verbose_name="Value ID")
    hidden      = models.BooleanField(verbose_name="Hide Value",default=False)

class Awards(models.Model):
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Awards"
    
    name        = models.CharField(max_length=50,verbose_name="Award Name",unique=True)
    image       = ResizedImageField(
                size=[64,64],
                upload_to="srl/static/srl/imgs/awards",
                verbose_name="Image",
                validators=[validate_image],
                null=True,
                help_text="Note: Images must be at least 64px in size, must be a square (height and width must match), and the max filesize is 3MB.")
    description = models.CharField(max_length=500,verbose_name="Award Description",blank=True,null=True)
    unique      = models.BooleanField(
                verbose_name="Unique Award",
                default=False,
                help_text="When checked, this award will be given the 'unique' tag - enabling special effects for the award on the profile page."
    )
class CountryCodes(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Country Codes"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Country Code ID")
    name        = models.CharField(max_length=50,verbose_name="Country Name")

class Players(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Players"
    
    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Player ID")
    name        = models.CharField(max_length=30,verbose_name="Name",default="Anonymous")
    nickname    = models.CharField(
                max_length=30,
                verbose_name="Nickname",
                blank=True,
                null=True,
                help_text="This is a special field where, if a nickname is given, it will be shown versus their SRC name."
    )
    url         = models.URLField(verbose_name="URL")
    countrycode = models.ForeignKey(CountryCodes,verbose_name="Country Code",blank=True,null=True,on_delete=models.SET_NULL)
    pfp         = models.CharField(max_length=50,verbose_name="Profile Picture URL",blank=True,null=True)
    pronouns    = models.CharField(max_length=20,verbose_name="Pronouns",blank=True,null=True)
    location    = models.CharField(max_length=30,verbose_name="Location",blank=True,null=True)
    twitch      = models.CharField(max_length=75,verbose_name="Twitch",blank=True,null=True)
    youtube     = models.CharField(max_length=100,verbose_name="YouTube",blank=True,null=True)
    twitter     = models.CharField(max_length=40,verbose_name="Twitter",blank=True,null=True)
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

class MainRunTimeframe(models.Model):
    def __str__(self):
        return "Run ID: " + self.run_id + " - " + self.timeframe
    
    class Meta:
        verbose_name_plural = "Main Run Timeframes"

    id          = models.AutoField(primary_key=True)
    run_id      = models.ForeignKey("MainRuns",max_length=10,verbose_name="Run ID",null=True,on_delete=models.SET_NULL)
    start_date  = models.DateTimeField(verbose_name="Approved Date")
    end_date    = models.DateTimeField(verbose_name="Beaten Date")
    points      = models.IntegerField(verbose_name="Packle Points",default=0)

class MainRuns(models.Model):
    def __str__(self):
        return "Run ID: " + self.id
    class Meta:
        verbose_name_plural = "Main Runs"
    
    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Run ID")
    game        = models.ForeignKey(GameOverview,verbose_name="Game ID",null=True,on_delete=models.SET_NULL)
    category    = models.ForeignKey(Categories,verbose_name="Category ID",null=True,on_delete=models.SET_NULL)
    subcategory = models.CharField(max_length=100,verbose_name="Subcategory Name",blank=True,null=True)
    values      = models.CharField(max_length=100,verbose_name="Subcategory Values",blank=True,null=True)
    player      = models.ForeignKey(Players,verbose_name="Player ID",blank=True,null=True,on_delete=models.SET_NULL,related_name="main_runs")
    player2     = models.ForeignKey(Players,verbose_name="Player 2 ID",blank=True,null=True,on_delete=models.SET_NULL,related_name="main_runs_p2")
    place       = models.IntegerField(verbose_name="Placing")
    url         = models.URLField(verbose_name="URL")
    video       = models.URLField(verbose_name="Video",blank=True,null=True)
    date        = models.DateField (verbose_name="Submitted Date",blank=True,null=True)
    time        = models.CharField(max_length=25,verbose_name="RTA Time",blank=True,null=True)
    time_secs   = models.FloatField(verbose_name="RTA Time (Seconds)",blank=True,null=True)
    timenl      = models.CharField(max_length=25,verbose_name="LRT Time",blank=True,null=True)
    timenl_secs = models.FloatField(verbose_name="LRT Time (Seconds)",blank=True,null=True)
    timeigt     = models.CharField(max_length=25,verbose_name="IGT Time",blank=True,null=True)
    timeigt_secs= models.FloatField(verbose_name="IGT Time (Seconds)",blank=True,null=True)
    points      = models.IntegerField(verbose_name="Packle Points",default=0)
    platform    = models.ForeignKey(Platforms,verbose_name="Platform",blank=True,null=True,on_delete=models.SET_NULL)
    emulated    = models.BooleanField(verbose_name="Emulated?",default=False)
    timeframes  = models.ManyToManyField(
                MainRunTimeframe,
                verbose_name="Run Timeframes",
                default=False,
                blank=True,
                help_text="This is a list of all the timeframes this run held certain point values; upon being beaten by that player or another, this is updated."
    )
    obsolete    = models.BooleanField(
                verbose_name="Obsolete?",
                default=False,
                help_text="When True, the run will be considered obsolete. Points will not count towards the player's total."
    )

class ILRuns(models.Model):
    def __str__(self):
        return "Run ID: " + self.id
    class Meta:
        verbose_name_plural = "IL Runs"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Run ID")
    game        = models.ForeignKey(GameOverview,verbose_name="Game ID",null=True,on_delete=models.SET_NULL)
    category    = models.ForeignKey(Categories,verbose_name="Category ID",null=True,on_delete=models.SET_NULL)
    subcategory = models.CharField(max_length=100,verbose_name="Subcategory Name",blank=True,null=True)
    values      = models.CharField(max_length=100,verbose_name="Subcategory Values",blank=True,null=True)
    level       = models.ForeignKey(Levels,verbose_name="Level ID",null=True,on_delete=models.SET_NULL)
    player      = models.ForeignKey(Players,verbose_name="Player ID",null=True,on_delete=models.SET_NULL)
    place       = models.IntegerField(verbose_name="Placing")
    url         = models.URLField(verbose_name="URL")
    video       = models.URLField(verbose_name="Video",blank=True,null=True)
    date        = models.DateField(verbose_name="Submitted Date",blank=True,null=True)
    time        = models.CharField(max_length=25,verbose_name="RTA Time",blank=True,null=True)
    time_secs   = models.FloatField(verbose_name="RTA Time (Seconds)",blank=True,null=True)
    timenl      = models.CharField(max_length=25,verbose_name="LRT Time",blank=True,null=True)
    timenl_secs = models.FloatField(verbose_name="LRT Time (Seconds)",blank=True,null=True)
    timeigt     = models.CharField(max_length=25,verbose_name="IGT Time",blank=True,null=True)
    timeigt_secs= models.FloatField(verbose_name="IGT Time (Seconds)",blank=True,null=True)
    points      = models.IntegerField(verbose_name="Packle Points",default=0)
    platform    = models.ForeignKey(Platforms,verbose_name="Platform",blank=True,null=True,on_delete=models.SET_NULL)
    timeframes  = models.ManyToManyField(
                MainRunTimeframe,
                verbose_name="Run Timeframes",
                default=False,
                blank=True,
                help_text="This is a list of all the timeframes this run held certain point values; upon being beaten by that player or another, this is updated."
    )
    emulated    = models.BooleanField(verbose_name="Emulated?",default=False)
    obsolete    = models.BooleanField(
                verbose_name="Obsolete?",
                default=False,
                help_text="When True, the run will be considered obsolete. Points will not count towards the player's total."
    )

class NewRuns(models.Model):
    def __str__(self):
        return "Run ID: " + self.id
    class Meta:
        verbose_name_plural = "Latest Runs"

    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Run ID")
    timeadded   = models.DateTimeField(verbose_name="Time Added")

class NewWRs(models.Model):
    def __str__(self):
        return "Run ID: " + self.id
    class Meta:
        verbose_name_plural = "Latest WRs"
    
    id          = models.CharField(max_length=10,primary_key=True,verbose_name="Run ID")
    timeadded   = models.DateTimeField(verbose_name="Time Added")