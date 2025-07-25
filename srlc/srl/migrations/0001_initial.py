# Generated by Django 5.2.3 on 2025-06-15 16:23

import django.db.models.deletion
import django_resized.forms
from django.db import migrations, models

import srl.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Awards",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=50, unique=True, verbose_name="Award Name"
                    ),
                ),
                (
                    "image",
                    django_resized.forms.ResizedImageField(
                        blank=True,
                        crop=None,
                        force_format=None,
                        help_text="Note: Images must be at least 64px in size, must be a square (height and width must match), and the max filesize is 3MB.",
                        keep_meta=True,
                        null=True,
                        quality=-1,
                        scale=None,
                        size=[64, 64],
                        upload_to="srl/static/srl/imgs/awards",
                        validators=[srl.models.validate_image],
                        verbose_name="Image",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        null=True,
                        verbose_name="Award Description",
                    ),
                ),
                (
                    "unique",
                    models.BooleanField(
                        default=False,
                        help_text="When checked, this award will be given the 'unique' tag - enabling special effects for the award on the profile page.",
                        verbose_name="Unique Award",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Awards",
            },
        ),
        migrations.CreateModel(
            name="CountryCodes",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Country Code ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="Country Name")),
            ],
            options={
                "verbose_name_plural": "Country Codes",
            },
        ),
        migrations.CreateModel(
            name="GameOverview",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="SRL Game ID",
                    ),
                ),
                ("name", models.CharField(max_length=35, verbose_name="Name")),
                ("abbr", models.CharField(max_length=20, verbose_name="Abbreviation")),
                ("release", models.DateField(verbose_name="Release Date")),
                ("boxart", models.URLField(verbose_name="Box Art URL")),
                (
                    "defaulttime",
                    models.CharField(max_length=20, verbose_name="Default Time"),
                ),
            ],
            options={
                "verbose_name_plural": "Game Overview",
            },
        ),
        migrations.CreateModel(
            name="Platforms",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Platform ID",
                    ),
                ),
                ("name", models.CharField(max_length=30, verbose_name="Name")),
            ],
            options={
                "verbose_name_plural": "Platforms",
            },
        ),
        migrations.CreateModel(
            name="Series",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Series ID",
                    ),
                ),
                ("name", models.CharField(max_length=20, verbose_name="Name")),
                ("url", models.URLField(verbose_name="URL")),
            ],
            options={
                "verbose_name_plural": "Series",
            },
        ),
        migrations.CreateModel(
            name="Categories",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Category ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="Name")),
                ("type", models.CharField(max_length=15, verbose_name="Type (IL/FG)")),
                ("url", models.URLField(verbose_name="URL")),
                (
                    "hidden",
                    models.BooleanField(default=False, verbose_name="Hide Category"),
                ),
                (
                    "game",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.gameoverview",
                        verbose_name="Linked Game",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Categories",
            },
        ),
        migrations.CreateModel(
            name="Levels",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Level ID",
                    ),
                ),
                ("name", models.CharField(max_length=75, verbose_name="Name")),
                ("url", models.URLField(verbose_name="URL")),
                (
                    "game",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.gameoverview",
                        verbose_name="Linked Game",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Levels",
            },
        ),
        migrations.AddField(
            model_name="gameoverview",
            name="platforms",
            field=models.ManyToManyField(to="srl.platforms", verbose_name="Platforms"),
        ),
        migrations.CreateModel(
            name="Players",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Player ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        default="Anonymous", max_length=30, verbose_name="Name"
                    ),
                ),
                (
                    "nickname",
                    models.CharField(
                        blank=True,
                        help_text="This is a special field where,  if a nickname is given,  it will be shown versus their SRC name.",
                        max_length=30,
                        null=True,
                        verbose_name="Nickname",
                    ),
                ),
                ("url", models.URLField(verbose_name="URL")),
                (
                    "pfp",
                    models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                        verbose_name="Profile Picture URL",
                    ),
                ),
                (
                    "pronouns",
                    models.CharField(
                        blank=True, max_length=20, null=True, verbose_name="Pronouns"
                    ),
                ),
                (
                    "twitch",
                    models.CharField(
                        blank=True, max_length=75, null=True, verbose_name="Twitch"
                    ),
                ),
                (
                    "youtube",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="YouTube"
                    ),
                ),
                (
                    "twitter",
                    models.CharField(
                        blank=True, max_length=40, null=True, verbose_name="Twitter"
                    ),
                ),
                (
                    "ex_stream",
                    models.BooleanField(
                        default=False,
                        help_text="When checked, this player can be filtered out from appearing on stream bots or pages.",
                        verbose_name="Stream Exception",
                    ),
                ),
                (
                    "awards",
                    models.ManyToManyField(
                        blank=True,
                        default=False,
                        help_text="Earned awards can be selected here. All selected awards will appear on the Player's profile.",
                        to="srl.awards",
                        verbose_name="Awards",
                    ),
                ),
                (
                    "countrycode",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.countrycodes",
                        verbose_name="Country Code",
                    ),
                ),
                (
                    "bluesky",
                    models.CharField(
                        blank=True, max_length=75, null=True, verbose_name="Bluesky"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Players",
            },
        ),
        migrations.CreateModel(
            name="Variables",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Variable ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="Name")),
                (
                    "cat",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.categories",
                        verbose_name="Category",
                    ),
                ),
                (
                    "all_cats",
                    models.BooleanField(
                        default=False,
                        help_text='When checked,  this means that the variable will work across all categories of the game in the "Game" field. Note: The "Linked Category" must be blank.',
                        verbose_name="All Categories",
                    ),
                ),
                (
                    "scope",
                    models.CharField(max_length=12, verbose_name="Scope (FG/IL)"),
                ),
                (
                    "hidden",
                    models.BooleanField(default=False, verbose_name="Hide Variables"),
                ),
                (
                    "game",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.gameoverview",
                        verbose_name="Linked Game",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Variables",
            },
        ),
        migrations.CreateModel(
            name="VariableValues",
            fields=[
                ("name", models.CharField(max_length=50, verbose_name="Name")),
                (
                    "value",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Value ID",
                    ),
                ),
                (
                    "hidden",
                    models.BooleanField(default=False, verbose_name="Hide Value"),
                ),
                (
                    "var",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.variables",
                        verbose_name="Linked Variable",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Variable Values",
            },
        ),
        migrations.AlterField(
            model_name="gameoverview",
            name="defaulttime",
            field=models.CharField(
                choices=[
                    ("realtime", "RTA"),
                    ("realtime_noloads", "LRT"),
                    ("ingame", "IGT"),
                ],
                default="realtime",
                verbose_name="Default Time",
            ),
        ),
        migrations.AddField(
            model_name="gameoverview",
            name="idefaulttime",
            field=models.CharField(
                choices=[
                    ("realtime", "RTA"),
                    ("realtime_noloads", "LRT"),
                    ("ingame", "IGT"),
                ],
                default="realtime",
                help_text="Sometimes leaderboards have one timing standard for full game speedruns and another standard for ILs. This setting lets you change the game-specific IL timing method.<br />NOTE: This defaults to RTA upon a game being created and must be set manually.",
                verbose_name="ILs Default Time",
            ),
        ),
        migrations.AddField(
            model_name="gameoverview",
            name="ipointsmax",
            field=models.IntegerField(
                default=100,
                help_text='Default is 100; 25 if this game contains the name "Category Extension". This is the maximum total of points an IL speedrun receives if it is the world record. All lower-ranked speedruns recieve less based upon an algorithmic formula.<br />                    NOTE: Changing this value will ONLY affect new runs. If you change this value, you will need to reset runs for this game from the admin panel.',
                verbose_name="IL WR Point Maximum",
            ),
        ),
        migrations.AddField(
            model_name="gameoverview",
            name="pointsmax",
            field=models.IntegerField(
                default=1000,
                help_text='Default is 1000; 25 if this game contains the name "Category Extension". This is the maximum total of points a full-game speedrun receives if it is the world record. All lower-ranked speedruns recieve less based upon an algorithmic formula.<br />                    NOTE: Changing this value will ONLY affect new runs. If you change this value, you will need to reset runs for this game from the admin panel.',
                verbose_name="Full Game WR Point Maximum",
            ),
        ),
        migrations.AlterField(
            model_name="gameoverview",
            name="name",
            field=models.CharField(max_length=55, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="gameoverview",
            name="twitch",
            field=models.CharField(
                blank=True, max_length=55, null=True, verbose_name="Twitch Name"
            ),
        ),
        migrations.CreateModel(
            name="NowStreaming",
            fields=[
                (
                    "title",
                    models.CharField(max_length=100, verbose_name="Twitch Title"),
                ),
                (
                    "offline_ct",
                    models.IntegerField(
                        help_text="In some situations, bots or the Twitch API can mess up. To help users, you can use this counter to countup the number of attempts to see if the runner is offline. After a certain number is hit, you can do something like remove embeds and/or remove this record.",
                        verbose_name="Offline Count",
                    ),
                ),
                ("stream_time", models.DateTimeField(verbose_name="Started Stream")),
                (
                    "game",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.gameoverview",
                        verbose_name="Game",
                    ),
                ),
                (
                    "streamer",
                    models.OneToOneField(
                        default="thepackle",
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="srl.players",
                        verbose_name="Streamer",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Streaming",
            },
        ),
        migrations.CreateModel(
            name="Runs",
            fields=[
                (
                    "id",
                    models.CharField(
                        max_length=10,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Run ID",
                    ),
                ),
                (
                    "runtype",
                    models.CharField(
                        choices=[("main", "Full Game"), ("il", "Individual Level")],
                        max_length=5,
                        verbose_name="Full-Game or IL",
                    ),
                ),
                (
                    "subcategory",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Subcategory Name",
                    ),
                ),
                ("place", models.IntegerField(verbose_name="Placing")),
                ("url", models.URLField(verbose_name="URL")),
                ("video", models.URLField(blank=True, null=True, verbose_name="Video")),
                (
                    "date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Submitted Date"
                    ),
                ),
                (
                    "v_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Verified Date"
                    ),
                ),
                (
                    "time",
                    models.CharField(
                        blank=True, max_length=25, null=True, verbose_name="RTA Time"
                    ),
                ),
                (
                    "time_secs",
                    models.FloatField(
                        blank=True, null=True, verbose_name="RTA Time (Seconds)"
                    ),
                ),
                (
                    "timenl",
                    models.CharField(
                        blank=True, max_length=25, null=True, verbose_name="LRT Time"
                    ),
                ),
                (
                    "timenl_secs",
                    models.FloatField(
                        blank=True, null=True, verbose_name="LRT Time (Seconds)"
                    ),
                ),
                (
                    "timeigt",
                    models.CharField(
                        blank=True, max_length=25, null=True, verbose_name="IGT Time"
                    ),
                ),
                (
                    "timeigt_secs",
                    models.FloatField(
                        blank=True, null=True, verbose_name="IGT Time (Seconds)"
                    ),
                ),
                (
                    "points",
                    models.IntegerField(default=0, verbose_name="Packle Points"),
                ),
                (
                    "emulated",
                    models.BooleanField(default=False, verbose_name="Emulated?"),
                ),
                (
                    "vid_status",
                    models.CharField(
                        choices=[
                            ("verified", "Verified"),
                            ("new", "Unverified"),
                            ("rejected", "Rejected"),
                        ],
                        default="verified",
                        help_text='This is the current status of the run,  according to Speedrun.com. It should be updated whenever the run is approved. Runs set as "Unverified" do not appear anywhere on this site.',
                        verbose_name="SRC Status",
                    ),
                ),
                (
                    "obsolete",
                    models.BooleanField(
                        default=False,
                        help_text="When True,  the run will be considered obsolete. Points will not count towards the player's total.",
                        verbose_name="Obsolete?",
                    ),
                ),
                (
                    "arch_video",
                    models.URLField(
                        blank=True,
                        help_text="Optional field. If you have a mirrored link to a video,  you can input it here.",
                        null=True,
                        verbose_name="Archived Video URL",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.categories",
                        verbose_name="Category ID",
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="srl.gameoverview",
                        verbose_name="Game ID",
                    ),
                ),
                (
                    "level",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.levels",
                        verbose_name="Level ID",
                    ),
                ),
                (
                    "platform",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="srl.platforms",
                        verbose_name="Platform",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="runs_p1",
                        to="srl.players",
                        verbose_name="Player ID",
                    ),
                ),
                (
                    "player2",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="runs_p2",
                        to="srl.players",
                        verbose_name="Player 2 ID",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Runs",
            },
        ),
        migrations.RemoveField(
            model_name="gameoverview",
            name="abbr",
        ),
        migrations.AddField(
            model_name="gameoverview",
            name="slug",
            field=models.CharField(
                default="", max_length=20, verbose_name="Abbreviation/Slug"
            ),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="RunVariableValues",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="srl.runs"
                    ),
                ),
                (
                    "value",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="srl.variablevalues",
                    ),
                ),
                (
                    "variable",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="srl.variables"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="runs",
            name="variables",
            field=models.ManyToManyField(
                related_name="runs",
                through="srl.RunVariableValues",
                to="srl.variables",
                verbose_name="Variables",
            ),
        ),
        migrations.AddConstraint(
            model_name="runvariablevalues",
            constraint=models.UniqueConstraint(
                fields=("run", "variable"), name="unique_variable_and_value"
            ),
        ),
        migrations.AlterField(
            model_name="runs",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="srl.categories",
                verbose_name="Category",
            ),
        ),
        migrations.AlterField(
            model_name="runs",
            name="game",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="srl.gameoverview",
                verbose_name="Game",
            ),
        ),
        migrations.AlterField(
            model_name="runs",
            name="level",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="srl.levels",
                verbose_name="Level",
            ),
        ),
        migrations.AlterField(
            model_name="runs",
            name="player",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="runs_p1",
                to="srl.players",
                verbose_name="Player",
            ),
        ),
        migrations.AlterField(
            model_name="runs",
            name="player2",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="runs_p2",
                to="srl.players",
                verbose_name="Player 2",
            ),
        ),
        migrations.AlterModelOptions(
            name="categories",
            options={"ordering": ["name"], "verbose_name_plural": "Categories"},
        ),
        migrations.AlterModelOptions(
            name="countrycodes",
            options={"ordering": ["name"], "verbose_name_plural": "Country Codes"},
        ),
        migrations.AlterModelOptions(
            name="gameoverview",
            options={"ordering": ["release"], "verbose_name_plural": "Game Overview"},
        ),
        migrations.AlterModelOptions(
            name="levels",
            options={"ordering": ["name"], "verbose_name_plural": "Levels"},
        ),
        migrations.AlterModelOptions(
            name="platforms",
            options={"ordering": ["name"], "verbose_name_plural": "Platforms"},
        ),
        migrations.AlterModelOptions(
            name="players",
            options={"ordering": ["name"], "verbose_name_plural": "Players"},
        ),
        migrations.RenameModel(
            old_name="GameOverview",
            new_name="Games",
        ),
        migrations.AlterField(
            model_name="runs",
            name="arch_video",
            field=models.URLField(
                blank=True,
                help_text="Optional field. If you have a mirrored link to a video, you can input it here.",
                null=True,
                verbose_name="Archived Video URL",
            ),
        ),
        migrations.AlterField(
            model_name="runs",
            name="obsolete",
            field=models.BooleanField(
                default=False,
                help_text="When True, the run will be considered obsolete. Points will not count towards the player's total.",
                verbose_name="Obsolete?",
            ),
        ),
        migrations.AlterField(
            model_name="runs",
            name="vid_status",
            field=models.CharField(
                choices=[
                    ("verified", "Verified"),
                    ("new", "Unverified"),
                    ("rejected", "Rejected"),
                ],
                default="verified",
                help_text='This is the current status of the run, according to Speedrun.com. It should be updated whenever the run is approved. Runs set as "Unverified" or "Rejected" do not appear anywhere on this site.',
                verbose_name="SRC Status",
            ),
        ),
        migrations.AlterModelOptions(
            name="games",
            options={"ordering": ["release"], "verbose_name_plural": "Games"},
        ),
        migrations.AddField(
            model_name="runs",
            name="approver",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="approver",
                to="srl.players",
                verbose_name="Approver",
            ),
        ),
        migrations.AddField(
            model_name="runs",
            name="description",
            field=models.TextField(
                blank=True, max_length=1000, null=True, verbose_name="Description"
            ),
        ),
        migrations.AlterField(
            model_name="games",
            name="ipointsmax",
            field=models.IntegerField(
                default=100,
                help_text='Default is 100; 25 if this game contains the name "Category Extension". This is the maximum total of points an IL speedrun receives if it is the world record. All lower-ranked speedruns recieve less based upon an algorithmic formula.<br />NOTE: Changing this value will ONLY affect new runs. If you change this value, you will need to reset runs for this game from the admin panel.',
                verbose_name="IL WR Point Maximum",
            ),
        ),
        migrations.AlterField(
            model_name="games",
            name="pointsmax",
            field=models.IntegerField(
                default=1000,
                help_text='Default is 1000; 25 if this game contains the name "Category Extension". This is the maximum total of points a full-game speedrun receives if it is the world record. All lower-ranked speedruns recieve less based upon an algorithmic formula.<br />NOTE: Changing this value will ONLY affect new runs. If you change this value, you will need to reset runs for this game from the admin panel.',
                verbose_name="Full Game WR Point Maximum",
            ),
        ),
        migrations.AlterField(
            model_name="players",
            name="nickname",
            field=models.CharField(
                blank=True,
                help_text="This is a special field where,  if a nickname is given, it will be shown versus their SRC name.",
                max_length=30,
                null=True,
                verbose_name="Nickname",
            ),
        ),
        migrations.RemoveField(
            model_name="awards",
            name="unique",
        ),
        migrations.AlterField(
            model_name="categories",
            name="type",
            field=models.CharField(
                choices=[("per-level", "Individual Level"), ("per-game", "Full Game")],
                verbose_name="Type (IL/FG)",
            ),
        ),
        migrations.AlterModelOptions(
            name="nowstreaming",
            options={"verbose_name": "Stream", "verbose_name_plural": "Streams"},
        ),
        migrations.AlterModelOptions(
            name="runvariablevalues",
            options={"verbose_name_plural": "Run Variable Values"},
        ),
        migrations.AddField(
            model_name="variables",
            name="level",
            field=models.ForeignKey(
                blank=True,
                help_text='If "scope" is set to "single-level", then a level must be associated. Otherwise, keep null.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="srl.levels",
                verbose_name="Associated Level",
            ),
        ),
        migrations.AlterField(
            model_name="players",
            name="bluesky",
            field=models.URLField(blank=True, null=True, verbose_name="Bluesky"),
        ),
        migrations.AlterField(
            model_name="players",
            name="pfp",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="Profile Picture URL",
            ),
        ),
        migrations.AlterField(
            model_name="players",
            name="twitch",
            field=models.URLField(blank=True, null=True, verbose_name="Twitch"),
        ),
        migrations.AlterField(
            model_name="players",
            name="twitter",
            field=models.URLField(blank=True, null=True, verbose_name="Twitter"),
        ),
        migrations.AlterField(
            model_name="players",
            name="youtube",
            field=models.URLField(blank=True, null=True, verbose_name="YouTube"),
        ),
        migrations.AlterField(
            model_name="variables",
            name="hidden",
            field=models.BooleanField(default=False, verbose_name="Hide Variable"),
        ),
        migrations.AlterField(
            model_name="variables",
            name="scope",
            field=models.CharField(
                choices=[
                    ("global", "All Categories"),
                    ("full-game", "Only Full Game Runs"),
                    ("all-levels", "Only IL Runs"),
                    ("single-level", "Specific IL"),
                ],
                verbose_name="Scope (FG/IL)",
            ),
        ),
        migrations.AddField(
            model_name="categories",
            name="rules",
            field=models.TextField(
                blank=True, max_length=1000, null=True, verbose_name="Rules"
            ),
        ),
        migrations.AddField(
            model_name="levels",
            name="rules",
            field=models.TextField(
                blank=True, max_length=1000, null=True, verbose_name="Rules"
            ),
        ),
        migrations.AddField(
            model_name="variablevalues",
            name="rules",
            field=models.TextField(
                blank=True, max_length=1000, null=True, verbose_name="Rules"
            ),
        ),
        migrations.AlterField(
            model_name="players",
            name="awards",
            field=models.ManyToManyField(
                blank=True,
                help_text="Earned awards can be selected here. All selected awards will appear on the Player's profile.",
                to="srl.awards",
                verbose_name="Awards",
            ),
        ),
    ]
