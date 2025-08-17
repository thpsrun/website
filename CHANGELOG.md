### v4 - The <Something> Update
###### ???

### Major Changes
*   Entire frontend of the website is redesigned. New UI, not basic HTML/JS, and much more!!? (Noami)
*   Versioned the API endpoints for better future-proofing and upgrading and testing and stuff (Packle)

### Added
*   Added `appear_on_main` field to `Categories` field that will allow for querying only categories that, well, we only want to appear on the main page.
*   Added a new `website` endpoint that is more catered to interacting with React.

### Fixed
*   Fixed the type checking for API responses to be `JsonResponse` and not `HttpResponse`.

### Changes
*   Changed the API so it is separated into "general"/"standard" and "website" API requests.
    *   React will be using a lot of the thps.run API, so separating this will help keep features separate and also allow us to do fancier things.

### Removed
*   (Planned) Removed the `subcategory` field from the `Runs` model.
    *   This was a remnant from v2 code, before it was more understood how to link variable-value pairs to an individual run.
*   (Planned) Removed the `place` field from the `Runs` model.

### Misc.

* * *

## Older Versions (v3 and back)

### v3.4.5
###### August 6, 2025
*   Fixed an issue where ILs were given `defaulttime` instead of `idefaulttime` in the API.

* * *

### v3.4.4
###### July 29, 2025
*   Added direct link to bracket to the nav-bar.
*   Fixed an issue where runs could not be imported if there are more than one IL category.
*   Removed the THPS3+4 Qualifying Leaderboard.
    *   Kept the code for later, but disabled functionality.

* * *

### v3.4.3
###### July 26, 2025
*   Fixed an issue where the SRC API could return a `place` of 0 for newly approved, non-obsolete speedruns when offsetting platforms was set to `True`.
    *   For reference, this *should* only happen if your leaderboard is setup to have region and/or platforms obsolete each other. THPS3+4 was configured to NOT have them offset, so you could have runs from multiple platforms. The thps.run API is configured to always assume platforms and region (which is never used by the THPS series, in either case) are set to offset. But, apparently, the `/leaderboard/` SRC endpoint does not the offsetting settings.
        *   In other words, I found another bug lol.

* * *

### v3.4.2
###### July 22, 2025
*   Fixed a visual bug where the leading zero of a speedrun's milliseconds was removed. [#75](https://github.com/thpsrun/website/issues/75)
    *   Over 250 runs were affected, as of 22 July. All runs have been fixed to properly reflect their times.

* * *

### v3.4.1
###### July 18, 2025
*   Added a new API field that displays the number of players within a game's subcategory.

* * *

### v3.4
###### July 17, 2025

### Added
*   Added a devoted THPS3+4 Tournament Seeding page.
    *   This is temporary until ~August 1st, 2025.
*   Added the combined IL leaderboard for THPS3+4 to the navbar.

### Changes
*   Changed a large amount of Django ORM requests to make a lot of player pages faster.
    *   Players with a large amount of speedruns will see a HUGE increase in speed (from ~5.5s to ~.5s!!!!).
    *   Histories for players with a lot of speedruns also saw a huge increase in speed!

### Fixed
*   Fixed some weird curly brackets being in weird places in some weird files.
*   Fixed an issue where overall community rankings were not accurate in most cases.
    *   The overall leaderboard was always correct, now they are both accurate!

### Removed
*   Removed overall rankings for full game and all individual level attempts from a player's main profile.
    *   If people want this re-added, let me know! Most of the code is still there, just commented out.

* * *

### v3.3.1
###### July 15, 2025
*   Added external links to other THPS sub-communities in the navigation bar.

* * *

### v3.3
###### July 13, 2025

### Added
*   Added a new page that appears when a game is in the database, but there are no available/approved speedruns.
*   Added some missing types to functions.
*   Added THPS3+4 to the full game and IL navigation bar menus.
    *   If no runs are approved, you'll get the "error" page listed above.

### Changes
*   Changed the navigation bar and added a few sub-menus to help with separating games.
*   Changed how slugs for games are given to contexts to render on web pages.
*   Changed the title tags for  `*leaderboard.html` templates to be more consistent.
*   Changed location of the "Currently Streaming" table to display on the bottom-right of a full main page, not top-right.
    *   This was changed since, if there are a lot of streams at once, it will push down the "Latest World Records" and "Latest Runs" tables.
*   Changed the "Currently Streaming" table to be slimmer.

* * *

### v3.2.3
###### July 9, 2025
*   Added information on the THPS3+4 Speedrun Mode Tournament to the top navbar.
*   Added the THUG1 SDL mod to the list of Mods on the top navbar.

* * *

### v3.2.2
###### July 4, 2025
*   Third round against nefarious N+1 queries. [#61 (continued)](https://github.com/thpsrun/website/issues/61)
*   Changed behavior of `/player/<user>/history` to be ordered by category name THEN by approval date.

* * *

### v3.2.1
###### July 1, 2025
*   Took a second pass at reducing the number of N+1 queries. [#61 (continued)](https://github.com/thpsrun/website/issues/61)
*   Fixed an issue where a server error would be returned if a player hasn't been given a rank (e.g. no approved runs).

* * *

### v3.2.0.1
###### June 30, 2025
*   Fixed an issue where the `/runs/` endpoint would return a server error when no world record exists for a category.

* * *

### v3.2.0
###### June 30, 2025
*   Took first major pass at reducing the number of N+1 queries popping up. [#61](https://github.com/thpsrun/website/issues/61)
*   Removed some redundant code and unused variables.
*   Fixed some grammar mistakes because I are bad.

* * *

### v3.1.0
###### June 20, 2025
### Added
*   Added return types to functions across the project.
*   Added additional PUT `/players` endpoint option to update a player's nickname through the API.
*   Added new crontab commands in the documentation for backing up the database every night and collecting static images regularly.

### Fixed
*   Fixed an issue where some API functions would return an `HTTP 200 OK` response instead of `HTTP 404 NOT FOUND` when something didn't exist.

### Changes
*   Changed the PUT `/players` endpoint so that it will use the player's unique ID to query SRC instead of their name.
    *   If they changed their username, it would return a 404.

### Misc.
*   Updated SentrySDK to give better verbose logging.
*   Updated libraries.

* * *

### v3.0.2
###### June 18, 2025
*   Fixed an issue where a co-op run's second player had improper variable names, resulting in a `Server Error 500` response.

* * *

### v3.0.1
###### June 16, 2025
*   Disabled (commented out) Nginx in the primary install to thps.run.
    *   Everything still works, but just using Nginx Proxy Manager for now. If you wanna use it, un-comment the the Nginx info in `docker-compose.PROD.yml`!

* * *

## v3.0 - The Open Source Update
###### June 15, 2025
*   [!!!!] This project is now open source! For more information on this, please check out the project's GitHub here: [https://github.com/thpsrun/website/](https://github.com/thpsrun/website/)
    *   This project has been updated to include some configurations and settings from [headstart-django](https://github.com/alexdeathway/headstart-django)!
  
### Added
*   Added Guides!
    *   Guides are .MD files (with some enhancements on-site) that serve to make the webiste the central point of information for the community.
    *   Guides will been added to the top navigation bar. If a game has a guide, it will appear after you go to it's view.
    *   If you wana contribute, you can contribute to the [new thps-guide GitHub repo](https://github.com/thpsrun/guides)!
        *   Approved pull requests will have its files automatically appear on this site.
*   Added `bluesky` to the `Players` model.
    *   As a note, this is minor change. If you want your Bluesky account added to your profile, contact Packle. A later update will move to SRC's v2 endpoint, which can return Bluesky links; otherwise this must be done manually.
*   Added `twitch` to the `Games` model.
    *   Added logic so this is imported when a new game is added.
    *   Sometimes, like with handheld leaderboards, an SRC game is appended with "GBC","GBA", "PSP", or others; because of this the default Twitch name will be different than reality (e.g., Tony Hawk's Pro Skater 4 exists, but Tony Hawk's Pro Skater 4 (GBA) does not).
*   Added Bluesky as an environmental variable to the project that can display on the navbar.
*   Added the following to the `Runs` model:
    *   `vid_status`: Mirrors what the current verification status is on SRC.
        *   Runs will be cached from now on when they are awaiting approval. They will be removed if rejected.
        *   Runs marked as "new" or "rejected" will not appear on the site.
    *   `approver`: Shows the player who approved the run (marked as None if the runner deleted their account).
    *   `description`: Shows the comment field of a specific speedrun.
        *   Right now, this is more for archiving purposes. If runs are eventually given the ability to be submited through this site, this will be available.
    *   `arch_video`: Optional field that holds archived/mirrored videos. This field is not automated, so it must be updated dynamically outside of the program or done manually.
*   Added the new `Runs` model to replace `MainRuns` and `ILRuns`.
    *   It was frustrating dealing with duplicate code for two nearly identical models (`MainRuns` has support for 2 players; `ILRuns` has support for Levels). This update forced me to change this to a combined model - had to get rid of dumb tech debt!
    *   Each runtype (`main` and `il`) have been given new QuerySet options to better separate them quickly.
*   Added support to cache rules by `Levels`, `Categories`, or `VariableValues`.
*   Added the `RunVariableValues` model to map out Variable-Value tandems for each run in the `Runs`.
    *   Later updates will deprecate `subcategory` and make it more automated to find categories and sub-categories for each game.
*   Added quick-links to Twitch, YouTube, and/or Archived Video to player profiles, leaderboards, and the main page. [#19](https://github.com/thpsrun/website/issues/19)
*   Added "Run History" for all players. By navigating to `/player/<NAME>/history/`, you will be able to see ALL current and obsolete speedruns (ordered by date).
    *   Quick-links to Twitch, YouTube, and/or Archived Videos are also here!
*   Added additional validations for the `Variable` model and added preliminary support for using the `all-levels` and `single-level` attributes. [#36](https://github.com/thpsrun/website/issues/36)
*   Added more alt and title tags through the site for accessibility.
*   Added the `NowStreaming` model.
    *   Added a new panel on the main page to show who is actively streaming.
    *   Also added the `/live/` endpoint.
        *   Pretty much the only endpoint that has full CRUD support.
  
  
### Changed
*   Changed around a lot of CSS values throughout the site.
    *   Different media queries were created for different screen sizes (definitely should be a lot more responsive on mobile).
    *   Not CSS, but sub-categories in most areas are now have a line break incldued. For example: "College" is on one line; "Collect the S-K-A-T-E letters" on the other.
*   Changed the `GameOverview` model to `Games`.
*   Changed the front page to display tied world records on the same table row. [#12](https://github.com/thpsrun/website/issues/12)
*   Changed the logic of the "Latest World Records" has been updated so that in cases that one runner has multiple world records in a row in the same category, only the most recent is shown. [#13](https://github.com/thpsrun/website/issues/13)
    *   Also changed the logic for "Latest Runs" so world records do not appear there.
*   Changed all of the API endpoints so they properly return information. Embed and query support has been added where applicable.
    *   `/runs/<ID>` returns information on a run based on its ID (e.g. SRC).
    *   `/players/<ID>` returns information on a player based on their name or ID.
    *   `/players/all` returns all information on players, but must be given query options.
        *   Example: `?query=streamexceptions`
    *   `/players/<USER>/pbs` returns all PBs of a player based on their name or ID.
    *   `/games/<ID>` returns information on a game based on their name or abbreviation.
    *   `/games/all` returns information on all games.
    *   `/categories/<ID>` returns information on a category based on its ID.
    *   `/levels/<ID>` returns information on a level based on its ID.
    *   `/variables/<ID>` returns information on a variable based on its ID.
    *   `/values/<ID>` returns information on a value based on its ID.
    *   `/live/` returns information on active streams.
    *   All endpoints have specific query and embed options that are added. Documentation is included with their respective functions in the project's API folder; more specific documentation will be made later.
    *   All endpoints require a valid API token; they will return an HTTP 403 Forbidden reponse.
*   Changed `/runs/` endpoint to now properly return data upon POST'ing a new run, while also serving HTTP_200_OK.
*   Changed `abbr` value in the `Games` model to `slug`.
*   Changed some checks in the API so it better detects if a newly submitted run is from a game belonging to the inputted `Series`. 
    *   Before, it checked the `weblink` key on new runs to see if they contain `speedrun.com/th`, which obviously (mostly) works for Tony Hawk... But it was hard-coded and it doesn't work for other series.
    *   This change effectively pulls all game IDs from the Speedrun.com API, and then checks to see if the newly submitted run belongs to any of those games.
*   Changed the response for the `/runs/` endpoint to give information on the current world record based on what game and category the run is from.
*   Changed the function responsible for gathering the SRC run's video.
    *   Before, it was the first video in the array. However, if multiple videos are in the array (such as videos being linked in the comments of the run), then the LAST video is the submission video. Now, it will always get the last video in the array.
  
  
### Fixed
*   Fixed an issue where the nickname of players would not properly appear in the "Latest Runs" portion of the main page. [#17](https://github.com/thpsrun/website/issues/17)
*   Fixed an issue where world records were also appearing on the "Latest Runs" portion of the main page. [#18](https://github.com/thpsrun/website/issues/18)
    *   Also added additional logic to remove obsolete runs, in cases that a player gets multiple WRs in a row in the same game and category.
*   Fixed an issue where games with multiple global categories (e.g., THPS1+2) would not have their new speedruns updated automatically; only the first global category would be given, not all. [#27](https://github.com/thpsrun/website/issues/27)
*   Fixed an issue where, if a game's timing is set to LRT and no RTA was submitted, it would appear as "0m 00s" on the leaderboard.
    *   Only obsolete runs were really affected, so this is more for the "Runs History" page for players.
*   Fixed an issue where obsolete runs were counting towards a player's overall totals.
*   Fixed an issue where new runs would be improperly have `obsolete` set to True; later functions would not reset this to False.
*   Fixed an issue where profile pictures were not displaying correctly. [#11](https://github.com/thpsrun/website/issues/11)
    *   Static profile pictures weren't being properly utilized by nginx, but also the static URLs were wrong.
*   Fixed an issue where brand new games in a series would fail to be added to the database. [#42](https://github.com/thpsrun/website/issues/42)
    *   Tony Hawk's Shred was the first real run added in a long time, so I added celery chaining to help stop it from going too fast.
*   Fixed an issue where `VariableValues` were returning an error when they were being updated with new metadata.
*   Fixed an issue where not giving an `Award` object to a website-generated user would produce an error.
  

### Removed
*   Removed `MainRuns` and `ILRuns` models. [#28](https://github.com/thpsrun/website/issues/28)
*   Removed Twitter from the navbar.
    *   Changed some logic around to make it an optional environmental variable.
*   Removed `Location` field from the Players model.
    *   `CountryCode` does a similar thing. `Location` was a remnant from the refactor.
*   Removed the website's changelog to appear on this GitHub repo.
*   Removed the `/import/` endpoint.
    *   This was a fragment from the earlier days of the project when I - quite frankly - did not know what I was doing.
        * Clarification: I still don't.
*   Removed `unique` field from `Awards` model.
    *   This was an idea earlier on to give special flair to players with specific awards. Currently not something I am working on, so it was removed. May be added again later!
  
  
### Other
*   Practically every major class, method, and function within this project is documented to a decent degree using python docstrings.
    *   Tried to also add some in-line comments wherever I could to explain rationale aout some lines of code.
*   On this repo, you will find a new section called "documentation" that goes over a lot of components of the project, including model structures, relationships, and API stuff.
*   All migrations have been squashed (it was at like 50 before I squashed them lol).
  

### Future Stuff/Current Issues
*   The project supports only two players (because the THPS community has not had a run with more than two players). A future update will remove `player` and `player2` from the `Runs` model and have a `Players` through model, similar to `RunVariableValues`.
*   The `subcategory` field in `Runs` is a lazy way to solve an issue from earlier on in the project's life (as early as 2.0 two years ago).
    *   The `subcategory` field is used to quickly query for all unique game/category combinations to dynamically load. There are, however, two major issues:
        1.  It only accounts for TWO global categories at a time. There hasn't been a reason to increase this, but other games may use more than two. Administrators from those communities will find issues with this, and it is honestly kind of a lazy way to do things. It needs to be more dynamic.
        2.  If a category or variable changes name, there is no mechanism to automatically update this field.
*   Run submissions is a topic that has been brought up a few times. Right now, this project currently PULLS data from Speedrun.com and acts like a cache. Later updates could introduce the concept of run submissions and, maybe, have it synced back up to Speedrun.com somehow.
    *   This is currently not possible with the v1 endpoint.
*   Updating to the v2 endpoint for Speedrun.com is an eventuality. However, the v2 endpoint is in alpha, is poorly documented (outside of the outstanding job by ManicJamie and YummyBacon5 in the [speedruncompy](https://github.com/ManicJamie/speedruncompy) repo). Because of this, I am not comfortable moving EVERYTHING to v2 yet.
    *   Due to this, there is some functionality I cannot implement yet. So, soon??
*   `Place` will soon be removed for dynamic placements [https://github.com/thpsrun/website/issues/40](https://github.com/thpsrun/website/issues/40).
*   `Subcategory` will be soon removed [https://github.com/thpsrun/website/issues/38](https://github.com/thpsrun/website/issues/38).
  
* * *

### v2.2.1.2
###### April 3, 2024

### Fixed
*   Fixed an issue where runs were not properly set to obsolete when a new run was uploaded. [#21](https://github.com/thpsrun/website/issues/21)
  
* * *
  
### v2.2.1.1
###### March 24, 2025

### Added
*   Added THPS1+2 Any% Tour Mode (All Tours, New Game) and All Goals & Golds (All Tours, New Game) to the main page.
*   Added additional logic to properly handle speedruns that have only LRT submitted but not RTA.
    *   An example speedrun is [neskamikaze's THPS3 Any% - 6th Gen](https://speedrun.com/api/v1/runs/8m78g0z0) run. As of writing, the link will give you the raw JSON of the run from the SRC API with incorrect data. Even though the front-end has their LRT set properly, the API has their LRT time set to "realtime" and "realtime\_t".
    *   This logic is temporary and will be removed if the v1 endpoint is fixed or (more likely) when this site uses the v2 endpoint.

### Fixed
*   Fixed an issue where world records sent through the API could produce errors with point calculations

* * *

### v2.2.1
###### March 23, 2025

### Added
*   Added `idefaulttime` (IL Default Time) attribute to the `GameOverview` model.
    *   One annoying part of SRC is that there is no way to set a specific timing standard (e.g., RTA, IGT, LRT) for full game leaderboards and another standard for ILs.
    *   An example of this is that THPS2 (as of writing) is RTA, but its ILs are set to IGT.
    *   Either I have to do a super hacky job of doing a check for the default timing method for a leaderboard THEN double-check if that is the actual default timing method, just have a billion checks that waste cycles, or I do this. This makes it easier to manage.
*   Added `pointsmax` (Full Game WR Point Maximum) and `ipointsmax` (IL WR Point Maximum) attributes to the `GameOverview` model.
    *   This is more so for future/historical change logging for me. Eventually this project will be open-source.
*   Added `v-date` (Verified Date) attribute to `MainRuns` and `ILRuns` models.
    *   `v-date` is used to show the most recently approved speedruns on the main page.
*   Added an additional check for the obsolete run imports that prevents importing runs awaiting review or are denied.
*   Added external links to the approved PARTYMOD and ClownJob'd mods.
    *   In a later update, resources will be handled better (to include guides).
  
### Changed
*   Changed dropdowns for all categories to be alphabetized.
    *   Need to work on a better system for showing categories (especially showing default categories first).
*   Changed `date` in `MainRuns` and `ILRuns` models from a regular date field to date and time field.
  
### Fixed
*   Fixed an issue where some runs that did not have a "submitted" or "verified" date would return as null.
    *   Because of this, the website would return a date of "January 1, 1970" (beginning of Unix epoch time). The games didn't exist back then.
    *   `v-date` can return as Null in some cases from the SRC API. The `date` field from SRC, however, always returns at least the date it was added to the SRC leaderboards. So, if the submitted date doesn't exist, it will use this date at midnight UTC as the time.
        *   Some ancient runs do not have a date. From now on, those runs will display a date of "---" on the leaderboards.
*   Fixed an issue where runs were not being imported properly if it was from a speedrunner that didn't already exist on this site.
*   Fixed an issue where nicknames for players on the "Latest World Records" section of the front page would show up null.
*   Fixed an issue where runs with a non-default time would appear as "0" on the front page (e.g., THPS2 ILs use IGT; they were still showing RTA instead).
    *   Alongside this, the issue where times in non-default categories/leaderboards displaying all of their runs as having the maximum points has been resolved.
    *   For example, THPS2 ILs use IGT for their timing, even though the THPS2 board uses RTA. Since Speedurn.com does not let you choose for different types of leaderboards in the same game, I added extra checks to balance this out.
*   Fixed an issue where obsolete times were still showing up on the leaderboards.
*   Fixed an issue where the leaderboard could display IGT runs in the wrong order.
*   Fixed an issue where IL leaderboards were displaying "Full Game" in the page title when they were obviously ILs.
*   Fixed an issue where profile pictures were calling an incorrect player ID.
*   Fixed an issue where obsolete runs were still counting towards a player's overall total in the overall IL leaderboards.
  
### Removed
*   Removed `NewRuns` and `NewWRs` models.
*   Removed a lot of libraries and dependencies that were no longer in use/needed.

* * *

### v2.2 - The BIG Update
###### December 25, 2024

### Added
*   Added the `Awards` model.
    *   Awards granted by the community (The Tony's, tournament victors, etc.) will be given special entries, which can the be associated with a player.
    *   When an award is given, they will appear on that player's profile in a new section. In the future, awards can also change the look of the profile (i.e. different colors).
*   Added the "Exceptions" field to the `Players` model.
    *   When a Player is marked with this new field, this will show they do not want their stream to appear in places like THPSBot or an upcoming Livestream page.
    *   This feature will make more of an impact with the next version of THPSBot, sometime before the heat death of the universe.
*   Added the "Nickname" field to the `Players` model.
    *   When a nickname is specified, then it will take precedent over the SRC name given.
*   Added the "obsolete" field to `MainRuns` and `ILRuns` models.
    *   Before, obsolete runs were considered obsolete when their Points were set to zero. However, this could cause potential issues in the future and was just a poor way to mark runs as old.
    *   This also allows for all obsolete runs to be added to the database, without issue.
  
### Changed
*   Changed the URLs for all leaderboards (again) so they make more sense:
    *   /lbs/thps1/ -> [/thps1/](/thps1/) -- Primary RTA leaderboard
    *   /lbs/ils/thps1/ -> [/thps1/ils/](/thps1/ils) -- Primary IL leaderboard
    *   /lbs/all/thps1/ -> [/thps1/all/](/thps1/all) -- Game Points Leaderboard
*   With this change, there will be no redirects; please update your links accordingly.
*   Updated the flag icons throughout the website to display hover-over text in compliance with accessibility standards.
    *   The otherworldly country known as Valhalla has been added to the list, as well. It's flag will also now display properly.
*   Updated the API `/players` endpoint so it can provide a list of users with YouTube and/or Twitch streams.
*   Updated the SQL database's performance with a dedicated solution.
*   Updated a bunch of Models in the database to feature heavier use of Foreign Keys to link data more dynamically together.
    *   This change will reduce on the number of overall requests a bit, while also making it easier to manage for future releases.
  
### Fixed
*   Fixed an issue where obsolete runs would fail to be added.
*   Fixed an issue where country codes were being set as the profile picture for users.
*   Fixed an issue where the profile pictures of users weren't being saved properly in some cases, causing errors.
*   Fixed an issue where, in some cases, new categories or levels would not be properly added to the database.
   
### Removed
*   Removed the "THP8 - Rank 1" category from the main page.

* * *

### v2.1.7
###### January 29, 2024

*   Added support for the THPG "100% (360/PS3)" category on the main page.

* * *

### v2.1.6
###### January 15, 2023

### Fixed
*   Fixed an issue where unknown country names would crash [the regional leaderboard](/regional).
*   Fixed an issue where unknown country names would show up as broken images on the main page, player profile, and individual leaderboards.

* * *

### v2.1.5
###### December 21, 2023

### Fixed
*   Fixed an issue where the THPS1+2 full game categories names were not properly associated with newly approved speedruns.

* * *

### v2.1.4
###### December 2, 2023

### Removed
*   Removed the overall Individual Level rankings on player profiles; load times for player profiles have been cut roughly in half.
    *   Previous behavior showed the game (i.e. Tony Hawk's Pro Skater 2) then a rank compared to other runners.
    *   The code utilized in this routine was inefficient, resulting in severe slowdown for all profiles who have IL times (especially THPS4).
    *   New behavior will have this removed; this may be re-introduced in the future.
        *   Note: This is ONLY for player profiles; not for rankings seen on the actual IL leaderboards (i.e. [/lbs/all/thps4/](/lbs/all/thps4/)).

* * *

### v2.1.3
###### November 26, 2023

### Fixed
*   Fixed an issue where obsolete world records would show up on the website's home page.

* * *

### v2.1.2
###### November 2, 2023

### Added
*   Added dates for when updates were applied from v2 to current day.
  
### Fixed
*   Fixed an issue where the THPS4 IL Oldest Record board was accounting for the previous world record instead of the current one.
*   Fixed an issue where dates on the IL leaderboards were set to one day backwards than their actual ones.

* * *

### v2.1.1
###### October 30, 2023

### Added
*   Added the THPS4CE Overall IL Leaderboard to the navigation bar.
*   Added a disclaimer to the THPS4 IL Leaderboards to show that the WR Count table doesn't account for the "Zoo - Feed the Hippos" goal.
*   Added a basic FAQ portion of the webiste to explain some things on how the website functions; more questions will be added over time.
  
### Changed
*   Changed the following URL patterns to shorten the links by a good bit and make them less confusing. The mappings are as follows:
    *   /lbs/ -> /overall
    *   /lbs/all/ -> /fullgame
    *   /lbs/regional/ -> /regional
    *   /lbs/worldwide/ -> /worldwide
    *   /lbs/ils/all/(ABBR) -> /lbs/all/(ABBR)
    *   /lbs/game/(ABBR) -> /lbs/(ABBR)
    *   /lbs/ils/game/(ABBR) -> /lbs/ils/(ABBR)
  
### Fixed
*   Fixed an issue where the webpage titles had the wrong formatting for some games.
*   Fixed an issue where placement logic would become out of sync when a new run was added to a leaderboard, especially when ties are involved.
    *   Note: Points were always accurate; this is a visual fix to show placements/ranks on a category while also ensuring they are accurate in the API.

* * *

### v2.1.0.1
###### October 27, 2023

### Added
*   Added a filter in the Regional Leaderboard that shows you all runners who have no country association known.
*   Added a default "Internal Server Error" message page when server errors occur.
*   Added a default "Resource Does Not Exist" message when the requested resource could not be found.
  
### Fixed
*   Fixed an issue where ILs would sometimes fail to be registered in the database.

* * *

### v2.1 - The API Update
###### October 26, 2023

### Added
*   Added Sentry.io for troubleshooting purposes.
*   Added a website privacy policy.
*   Added administrator feature to "hide" categories.
*   Added API endpoints for THPSBot to utilize in its v2.1 release.
*   Added country flags next to each player's name (wherever applicable).
    *   Country flags are outsourced via flagpedia.net's content delivery network!
    *   Added a new library that converts Speedrun.com's very... strange country code formatting to ISO-3166 approved codes instead.
*   Added support for a mobile version of the website.
    *   Layout is a LOT more dynamic; should be very easily viewable on all current smart phones and tablets.
*   Added the "Regional Leaderboards"
    *   Overall board features the average points for runners from a country.
    *   Regional leaderboards also have a brief leaderboard of the top players in that country.
*   Added the "Worldwide Leaderboards"
    *   Up-to-date count of WRs (Gold), 2nd places (Silver), and 3rd places (Bronze)
*   Added "Oldest Records" for THPS4 ILs.
    *   This is only for THPS4 now since there are soooo many ILs to keep track of; this can be easily added to other games as requested.
*   Added "World Record Count" for THPS4 ILs.
    *   Again, only for THPS4 ILs but can easily be added to other games as requested.
*   Added a footer to the bottom of the website with a disclaimer about the website.
  
### Changed
*   Changed "THPS12" to display as "THPS1+2" on the home page.
*   Changed the social icons on the navigation bar to be more stylized.
*   Changed the formula so it only accounts for the highest placed speedrun in Co-Op leaderboards (rip Infinite Packle Points).
*   Changed the profile page a bit to make it more pleasing to look at.
    *   Reduced the amount of white space on the top panel.
    *   Changed the social icons to match the navigation bar.
  
### Fixed
*   Fixed an issue where names were case sensitive, leading to issues where "username" didn't equal "UserName" and errors were raised.
*   Fixed an issue where the entire leaderboard would be shown with no pagination if nothing was searched.
*   Fixed an issue where the searchbar on Full Game and IL leaderboards would show all points for all runners instead of their specific sections.
*   Fixed an issue where the second player in THAW Classic Mode - Co-Op would not appear.
*   Fixed an issue where the tables on the site index was off slightly.
*   Fixed an issue where the navigation bar would "move" in some cases on larger screen sizes.
*   Fixed an issue where players with larger speedrun resumes would have drastically slower webpage loading.
    *   This is a partial fix; will attack this again in a later update. TL;DR: there is a lot of data processed on the player profile pages to make sure it is dynamic. Cache will probably be added in the early-to-mid term; more to come.
*   Fixed an issue where ranks on leaderboards would display the incorrect rank whenever ties occurred.

* * *

### v2.0.5.1
###### August 18, 2023

### Fixed
*   Fixed an issue where new sub-categories would not be automatically added to the website, resulting in a desync error.
*   Fixed an issue where new runs would not be properly added to the "New Runs" or "New WRs" tab.

* * *

### v2.0.5
###### August 14, 2023

### Added
*   Added an additional ability for administrators to completely refresh a leaderboard from scratch.
*   Added additional calls as setup for the upcoming API Update.

### Changed
*   Updated Django and all libraries to their latest versions.

### Fixed
*   Fixed an issue where the THAW leaderboards did not properly separate the Difficulty and NG+ sub-categories and instead combined them.
*   Fixed an issue where API calls were not properly updating speedruns that have two non-global sub-categories.
*   Fixed a rare issue where the API will fail, even if an API key is properly given.
  
* * *

### v2.0.4
###### August 10, 2023

### Added
*   Added automation in the background to check for new static images every 5 minutes in Django.
  
### Fixed
*   Fixed an issue where only the very last obsolete speedrun would be set to 0 points.
*   Fixed an issue where the real placing of tied runs would not be displayed properly.
    *   Before: the earliest runs held tiebreakers and all subsequent runs were incremented by 1.
    *   Now: the earliest runs are shown towards the top, first, and placings are properly displayed.
    *   Fixed an associated bug where some placings were incorrect.
*   Fixed an issue where certain categories were combining with others if there were more than one global category.

* * *

### v2.0.3
###### August 5, 2023

### Fixed
*   Fixed an issue where non-World Records would somehow appear on the Latest WRs leaderboard.

* * *

### v2.0.2
###### July 13, 2023

### Fixed
*   Fixed an issue where non-World Record speedruns would not properly be added to the Latest Runs leaderboard.
*   Fixed an issue where adding anonymous-only runs via the API would cause a crash.

* * *

### v2.0.1
###### July 12, 2023

### Fixed
*   Fixed an issue where the wrong category would be assigned to runs imported from the thps.run API.
*   Fixed an issue where World Records would not start the function that would change all point totals for subsequent runs.
    *   Also fixed a related issue where those same runs would not have their placings updated.
    *   Also, also fixed an issue related to the last two that had runs resetting point values in some cases.
*   Fixed an issue where redirects weren't working properly.

* * *

### v2.0 - The "Fucking Finally" Update
###### July 2, 2023

*   Reworked the entire website from the ground up, using Django and a custom-made API for future projects.
*   Runs approved and seen by THPSBot on the Discord server are automatically sent to the new thps.run API; runs are added and auto-updated on the site.
*   Category Extensions have been buffed to give 25 points on WR; same formula applies as before for subsequent runs.
*   Completely remade the player profile, including:
    *   Profile picture taken from SRC (if none given, will auto-use TonyChamp).
    *   An "overall" table on the top that displays the player, their points, and overall rank.
    *   Broke down games better and cleaned up the table to make it more asthetically pleasing (not by much lol)
*   Broke up the Full Game and IL leaderboards into two separate areas on the navigation bar.
    *   To avoid clutter, the games are separated into "THPS", "Not THPS" (i.e. THUG1 - THP8), "Handheld", and "Category Extensions"
*   Leaderboards for a game can now be linked directly via URL (specific category in a future update).
*   Uses custom Django models instead of a stupid JSON file for a "database"
*   Overall and IL leaderboards with over 50 players will be auto-paginated