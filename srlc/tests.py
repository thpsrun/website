import datetime

from django.test import Client, TestCase
from django.utils import timezone
from srl.models import (
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


class HomepageTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class ModelTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    @classmethod
    def setUpTestData(cls):
        cls.series = Series.objects.create(
            id="123abc",
            name="Tony Hank",
            url="https://speedrun.com",
        )

        cls.platform = Platforms.objects.create(
            id="xbox",
            name="Xbox 720",
        )

        cls.games = Games.objects.create(
            id="asdef",
            name="Tony Hank's Pro Skateboarding 1",
            slug="thps1",
            twitch="Tony Hank's Pro Skateboarding 2",
            release="1999-12-31",
            boxart="https://speedrun.com/",
            defaulttime="realtime_noloads",
            idefaulttime="ingame",
            pointsmax=9999,
            ipointsmax=1000,
        )
        cls.games.platforms.add("xbox")

        cls.categories = Categories.objects.create(
            id="category",
            game=Games.objects.get(id="asdef"),
            name="Test Category 1",
            type="per-game",
            url="https://speedrun.com/sm64",
            hidden=True,
        )

        cls.levels = Levels.objects.create(
            id="level",
            game=Games.objects.get(id="asdef"),
            name="Test Level 1",
            url="https://speedrun.com/sm64",
        )

        cls.variables = Variables.objects.create(
            id="var1",
            name="Variable Lariable",
            game=Games.objects.get(id="asdef"),
            cat=Categories.objects.get(id="category"),
            all_cats=False,
            scope="all",
            hidden=False,
        )

        cls.values = VariableValues.objects.create(
            var=Variables.objects.get(id="var1"),
            name="Valueeeeeeeeeee",
            value="val1",
            hidden=False,
        )

        cls.awards = Awards.objects.create(
            id=1,
            name="Best in the World",
            description="Simply the best",
            unique=True,
        )

        cls.countrycodes = CountryCodes.objects.create(
            id="usa",
            name="United States"
        )

        cls.player1 = Players.objects.create(
            id="player1",
            name="Bob",
            nickname="Bobby B",
            url="https://speedrun.com/",
            countrycode=CountryCodes.objects.get(id="usa"),
            pfp="https://google.com/",
            pronouns="He/Him/Them/They",
            twitch="Twitch",
            youtube="Youtube",
            twitter="Twitter",
            bluesky="Bluesky",
            ex_stream=True,
        )
        cls.player1.awards.add(1)

        cls.player2 = Players.objects.create(
            id="player2",
            name="Sam",
            nickname="Sammy",
            url="https://speedrun.com/",
            countrycode=CountryCodes.objects.get(id="usa"),
            pfp="https://google.com/",
            pronouns="He/Him/Them/They",
            twitch="Twitch",
            youtube="Youtube",
            twitter="Twitter",
            bluesky="Bluesky",
            ex_stream=True,
        )
        cls.player2.awards.add(1)

        cls.runs = Runs.objects.create(
            id="run123",
            runtype="il",
            game=Games.objects.get(id="asdef"),
            category=Categories.objects.get(id="category"),
            level=Levels.objects.get(id="level"),
            subcategory="aeiou aeiou",
            player=Players.objects.get(id="player2"),
            place=666,
            url="https://speedrun.com/",
            video="https://speedrun.com/",
            date=timezone.make_aware(datetime.datetime.now()),
            v_date=timezone.make_aware(datetime.datetime.now()),
            time="0m 00s",
            time_secs=0.0,
            timenl="0m 00s",
            timenl_secs=0.0,
            timeigt="5m 33s",
            timeigt_secs=999.92,
            points=1000,
            platform=Platforms.objects.get(id="xbox"),
            emulated=True,
            vid_status="verified",
            approver=Players.objects.get(id="player1"),
            obsolete=True,
            arch_video="https://speedrun.com/",
            description="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        )
        cls.runvariablevalues = RunVariableValues.objects.create(
            id=1,
            run=Runs.objects.get(id="run123"),
            variable=Variables.objects.get(id="var1"),
            value=VariableValues.objects.get(value="val1"),
        )

        cls.nowstreaming = NowStreaming.objects.create(
            streamer=Players.objects.get(id="player2"),
            game=Games.objects.get(id="asdef"),
            title="Heckin good",
            offline_ct=9,
            stream_time=timezone.make_aware(datetime.datetime.now()),
        )

    def test_series(self):
        self.assertEqual(Series.objects.filter(id="123abc").exists(), True)

    def test_platforms(self):
        self.assertEqual(Platforms.objects.filter(id="xbox").exists(), True)

    def test_games(self):
        self.assertEqual(Games.objects.filter(id="asdef").exists(), True)

    def test_categories(self):
        self.assertEqual(Categories.objects.filter(id="category").exists(), True)

    def test_levels(self):
        self.assertEqual(Levels.objects.filter(id="level").exists(), True)

    def test_variables(self):
        self.assertEqual(Variables.objects.filter(id="var1").exists(), True)

    def test_variablevalues(self):
        self.assertEqual(VariableValues.objects.filter(value="val1").exists(), True)

    def test_players(self):
        self.assertEqual(Players.objects.filter(id="player1").exists(), True)
        self.assertEqual(Players.objects.filter(id="player2").exists(), True)

    def test_runs(self):
        self.assertEqual(Runs.objects.filter(id="run123").exists(), True)
        self.assertEqual(RunVariableValues.objects.filter(id=1).exists(), True)

    def test_streaming(self):
        self.assertEqual(NowStreaming.objects.all().exists(), True)
