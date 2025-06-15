# thps.run Admin Panel

## What is the Admin Panel?
Within Django, it has an incredibly powerful and built-in administration interface. This isn't meant for everyday users to access, but it helps manage your Models a lot easier, allows you to modify objects, and even search for objects based on parameters.

This section will discuss each individual part of the Admin Panel. If you want to know more about how it works, check out the [Django documentation](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/).

## Table of Contents:
### Core Models
-   [Series](#series)
-   [Platforms](#platforms)
-   [Games](#games)
-   [Categories](#categories)
-   [Levels](#levels)
-   [Variables](#variables)
-   [VariableValues](#variablevalues)
-   [Awards](#awards)
-   [Country Codes](#country-codes)
-   [Players](#players)
-   [Runs](#runs)

### Other Models
-   [API Keys](#api-keys)
-   [Streaming](#streaming)

## Series
`Series` is a small model who's role is to hold basic information for a Speedrun.com Series. However, it does hold a few powerful tools that should be used.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected series" - Deletes all selected Series permanently.
-   "Initialize Series Data"
    -   **NOTE: PLEASE READ THIS!!**
    -   This action is very time consuming; once the Series ID is given, it will begin a crawl of that series on Speedrun.com and discover ALL associated games, categories, variables, values, levels, runs, and players.
        -   This is conducted in ascending release order.
        -   **YOU WILL BE RATE LIMITED!** Everything is done in the background using celery runners; if you want current information on *where* the process is, check the Django pod's logs for information. If you haven't seen any movement in more than 3 minutes or so, then it completed.


### Adding Series
-   Click "Add Series" on the Series interface.
-   Give your series a unique ID.
    -   **NOTE:** This ID is derived from the unique ID given to the series from Speedrun.com. Website-specific IDs are not currently supported at this time. If you want to find the Series ID, research the [Speedrun.com API Documentation](https://github.com/speedruncomorg/api/tree/master/version1).
-   Give your series a name and input the URL to the Series from Speedrun.com.
-   Click "Save".

### Model Structure
| Field   | Inputs |
| --------| ------ |
| id (PK) | 10 char limit |
| name    | 20 char limit |
| url     | URL field |

### Endpoint
There is no endpoint for Series.


## Platforms
`Platforms` are the specific consoles for levels.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected platforms" - Deletes all selected Platforms permanently.

### Adding Platforms
-   Click on the "Add Platforms" option in the Platforms interface.
-   Give your platform a unique ID.
    -   **NOTE:** This ID is derived from the unique ID given to the platform from Speedrun.com. Website-specific IDs are not currently supported at this time. If you want to find the Platform ID, research the [Speedrun.com API Documentation](https://github.com/speedruncomorg/api/tree/master/version1).
-   Select the linked game from the drop-down.
-   Give your Level a name.
-   Input the URL to the Speedrun.com platform.
-   Click "Save".

### Model Structure
| Field   | Inputs |
| --------| ------ |
| id (PK) | 10 char limit |
| name    | 50 char limit |

### Endpoint
There is no endpoint for Platforms.


## Games
`Games` holds all of the metadata information for games within your `Series`. Without a game in place, you cannot add `Categories`, `Variables`, or `Runs` to it.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected Games" - Deletes all selected Games permanently.
    -   **`Categories`, `Variables`, `Runs`, and `NowStreaming` objects that are linked to these game(s) will have them removed automatically and be orphaned (will lose that Category as a foreign key)!**
-   "Update Game Metadata" - Retrieves current information from the Speedrun.com API to update the game(s) metadata.
-   "Update Game Runs" - Retrieves current information on all runs (including obsolete) from the Speedrun.com API that belongs to that game and updates their respective objects.
-   "Reset Game Runs" - Removes all non-obsolete runs from the database belonging to the game(s) and re-retrieves them from the Speedrun.com API.

### Adding Games
-   Click on the "Add Games" option in the Games interface.
-   Give your game a unique ID.
    -   **NOTE:** This ID is derived from the unique ID given to the game from Speedrun.com. Website-specific IDs are not currently supported at this time. If you want to find the Game ID, research the [Speedrun.com API Documentation](https://github.com/speedruncomorg/api/tree/master/version1).
-   Input the name.
-   Input the abbreviation/slug.
    -   Example: Tony Hawk's Pro Skater 2 would be `thps2`
-   Give the Twitch name based on the name of the game in Twitch's directory.
-   Input the original release date of the game (or platform).
-   Input the box art URL to the game (when inputted from Speedrun.com API, it is to the one in the API).
-   Timing methods:
    -   Default Time - The default timing method used for the game.
    -   ILs Default Time - The default timing method used for individual levels.
        -   NOTE: This is not a real field in the Speedrun.com API; sometimes you will have games that are real-time (for example) for full game runs, but in-game time for individual level. This helps differentiate them properly when queries are conducted.
-   Select the platforms associated with this game.
    -   Hold down "Control" on Windows or "Command" on Mac OS to select more than one.
-   Points:
    -   Full Game WR Points Maximum - This is the maximum amount of points given to a speedrun that is the world record of a full game category. Default is 1000.
    -   IL WR Points Maximum - This is the maximum amount of points given to a speedrun that is the world record of an IL category. Default is 100.

### Model Structure
| Field        | Inputs |
| ------------ | ------ |
| id (PK)      | 10 char limit |
| name         | 55 char limit |
| slug         | 20 char limit |
| twitch       | 55 char limit |
| release      | DateTime field |
| boxart       | URL field |
| defaulttime  | `realtime`, `realtime_noloads`, or `ingame` |
| idefaulttime | `realtime`, `realtime_noloads`, or `ingame` |
| platforms    | ManyToMany |
| pointsmax    | int |
| ipointsmax   | int |

### Endpoint
`/api/games/<ID>`


## Categories
`Categories` are, as the name says, the regular categories for games in the `Games` model.

### View
-   "By Linked Game" - When a game is chosen, all Categories that belongs to that game via the `game` field will be filtered.
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected categories" - Deletes all selected Categories permanently.
    -   To re-add, you will need to initiate the "Reset Game Runs" or "Refresh Game Runs" actions for the specific game.
    -   **All `Runs` and `Variables` asscociated with this category will be orphaned (will lose that Category as a foreign key)!**
        -   Only do this if you know what you are doing!

### Adding Categories
**Note: Categories are primarily added through the "Reset Game Runs" or "Refresh Game Runs" actions in the specific game.**
-   Click on the "Add Categories" option in the Categories interface.
-   Give your category a unique ID.
    -   **NOTE:** This ID is derived from the unique ID given to the category from Speedrun.com. Website-specific IDs are not currently supported at this time. If you want to find the Category ID, research the [Speedrun.com API Documentation](https://github.com/speedruncomorg/api/tree/master/version1).
-   Select the linked game from the drop-down.
-   Give your Category a name.
-   Select "Full Game" or "Individual Level" from the drop-down, dependent on what this Category belongs to.
-   Input the URL to the Speedrun.com category.
-   Optionally, you can click "Hide Category" if you want this category to be hidden later.
-   Click "Save".

### Model Structure
| Field   | Inputs |
| --------| ------ |
| id (PK) | 10 char limit |
| game    | `Games` FK |
| name    | 50 char limit |
| type    | `per-game` or `per-level` |
| url     | URL field |
| hidden  | bool |

### Endpoint
`/api/categories/<ID>`


## Levels
`Levels` signify specific levels or segments in an individual level speedrun. ILs are easily identified in the SRC API if they have a `level` ID associated with them.

### View
-   "By Linked Game" - When a game is chosen, all Levels that belongs to that game via the `game` field will be filtered.
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected levels" - Deletes all selected Levels permanently.
    -   To re-add, you will need to initiate the "Reset Game Runs" or "Refresh Game Runs" actions for the specific game.
    -   **All `Runs` and `Variables` asscociated with this level will be orphaned (will lose that Level as a foreign key)!**
        -   Only do this if you know what you are doing!

### Adding Levels
**Note: Levels are primarily added through the "Reset Game Runs" or "Refresh Game Runs" actions in the specific game.**
-   Click on the "Add Levels" option in the Levels interface.
-   Give your level a unique ID.
    -   **NOTE:** This ID is derived from the unique ID given to the level from Speedrun.com. Website-specific IDs are not currently supported at this time. If you want to find the Level ID, research the [Speedrun.com API Documentation](https://github.com/speedruncomorg/api/tree/master/version1).
-   Select the linked game from the drop-down.
-   Give your Level a name.
-   Input the URL to the Speedrun.com level.
-   Click "Save".

### Model Structure
| Field   | Inputs |
| --------| ------ |
| id (PK) | 10 char limit |
| game    | `Games` FK |
| name    | 50 char limit |
| url     | URL field |

### Endpoint
`/api/levels/<ID>`


## Variables
`Variables` can either be annotations or, a super majority of cases, ways to make sub-categories for a speedrun category.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected Variable Values" - Deletes all selected VariableValues permanently.
    -   **All `VariableValues` and `RunVariableValues` asscociated with this variable will be orphaned (will lose that variable as a foreign key)!**

### Adding Variables
-   Click "Add Variable" on the Variables interface.
-   Give your variable a unique ID.
    -   **NOTE:** This ID is derived from the unique ID given to the variable from Speedrun.com. Website-specific IDs are not currently supported at this time. If you want to find the Value ID, research the [Speedrun.com API Documentation](https://github.com/speedruncomorg/api/tree/master/version1).
-   Name the variable.
-   Select the game this variable is linked to.
-   Optionally, select the category this is linked to.
-   Optionally, check "All Categories" IF a category is not selected.
-   Select the scope for the Variable.
-   Optionally, select the Level this is associated with IF scope is set to "Specific IL".
-   Optionally, you can click "Hide Variable" if you want this category to be hidden later.
-   Click "Save".

#### Understanding Categories and Scope

##### Relationship
-   Categories is optional; if you do not have a category set, then you must select "All Categories"
    -   This makes this what is called a "global" variable within the game. It is not associated with a specific category, instead it will apply based on what the scope is.
-   Scope is required; this defines HOW the Variable is set within the game.
    -   "global" = All full game and IL categories have this variable.
    -   "full-game" = All full game categories have this variable.
    -   "all-levels" = All individual level categories have this variable.
    -   "single-level" = Only ONE specific Level has this Variable applied to it.

##### Examples
1.  If "All Categories" is checked and "global" is set as the scope, then ALL full game and IL categories have this variable applied.
2.  If "All Categories" is checked and "all-levels" is set as the scope, then ALL IL categories have this variable applied.
3.  If a category is checked and "full-game" is set as the scope, the variable is ONLY applied for the category's full game speedruns.
4.  If a category is checked and "single-level" is set as the scope and a level is specificed, then ONLY that level with that category will have the variable applied.

### Model Structure
| Field       | Inputs |
| ----------- | ------ |
| id (PK)     | 10 char limit |
| name        | 50 char limit |
| cat         | `Categories` FK |
| all_cats    | bool |
| scope       | `global`, `full-game`, `all-levels`, or `single-level` |
| level       | `Levels` FK |
| hidden      | bool |

#### Validations
-   Either `cat` must have a value OR `all_cats` is checked.
-   You cannot have BOTH `cat` defined AND `all_cats` checked.
-   If `scope` is set to "single-level", a `level` MUST be defined.
-   If a `level` is defined, `scope` MUST be set to "single-level"

### Endpoint
`/api/variables/<ID>`


## VariableValues
`VariableValues` are the individual and unique values for `Variables`. Another term for these are simply "Values", but the code currently refers to them as the former (mostly to know they are a Variable's values). Variables can have MANY values, but a singular run can only have ONE value per variable it holds.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected Variable Values" - Deletes all selected VariableValues permanently.
    -   **All `RunVariableValues` asscociated with this variable value will be orphaned (will lose that variable value as a foreign key)!**

### Adding VariableValues
-   Click "Add Variable Values" on the VariableValues interface.
-   Select the variable to associate this value to.
-   Name the value.
-   Give your value a unique ID.
    -   **NOTE:** This ID is derived from the unique ID given to the value from Speedrun.com. Website-specific IDs are not currently supported at this time. If you want to find the Value ID, research the [Speedrun.com API Documentation](https://github.com/speedruncomorg/api/tree/master/version1).

### Model Structure
| Field       | Inputs |
| ----------- | ------ |
| var         | `Variables` FK |
| name        | 50 char limit |
| value (PK)  | 10 char limit |
| hidden      | bool |

### Endpoint
`/api/values/<ID>`


## Awards
`Awards` are special titles that you can give to users. It is set to be Many-to-Many field within the `Players` model, meaning that it can be assigned to many players and many players can have multiple awards.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected awards" - Deletes all checked awards permanently.
    -   Players who has those award(s) will have them removed automatically.

### Adding Awards
-   Click on the "Add Awards" option in the Awards interface.
-   Give your Award a unique name and description.
-   Optionally, you can give it an image.
    -   Images are uploaded to the `srlc/srl/static/srl/imgs` directory.
    -   Images must be 64x64, with a maximum file size of 3MB.
-   Click "Save".

### Model Structure
| Field       | Inputs |
| ----------- | ------ |
| id (PK)     | int, hidden |
| name        | 50 char limit, unique |
| image       | 64x64, 3MB limit |
| description | 500 char limit |

### Endpoint
There is no endpoint for Awards.


## Country Codes
`Country Codes` is a small model that lists the unique abbreviation or slug for a country and associates it with their full name (e.g., `us` and `United States`).

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected Country Codes" - Deletes all selected Country Codes permanently.
    -   Players who has those Country Codes will have them removed automatically. That player will no longer be associated with a Country Code until a refresh occurs for their profile.

### Adding Country Codes
-   Click on the "Add Country Codes" option in the County Codes interface.
-   Lookup the [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code for the country you want to add (this list is for two-letter abbreviations).
-   Input the two-letter code and the full name into the respectivie fields.
-   Click "Save".

### Model Structure
| Field   | Inputs |
| --------| ------ |
| id (PK) | 10 char limit |
| name    | 50 char limit |

### Endpoint
There are no endpoints for Country Codes.


## Players
`Players` are the, well, users/players of speedruns. Whenever an object is added to `Runs`, it is associated to the `Players` model via a foreign key. This allows for enhanced lookups and stuff throughout the website.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected players" - Deletes all selected Players permanently.
    -   **All `Runs` asscociated with this player will be orphaned (will lose that Player as a foreign key)!**
        -   Only do this if you know what you are doing!
-   "Update player metadata" - Retrieves current information of the player from the Speedrun.com API and updates their associated object.
-   "Force Add Obsolete Runs" - All checked player(s) will have their entire Speedrun.com profile checked for runs that belong to any game that belongs to this Series.
    -   **NOTE: This is an intensive operation. This will take time to complete.**

### Add Players
-   Click on the "Add Players" option in the Players interface.
-   Give your player a unique ID.
    -   **NOTE:** This ID is derived from the unique ID given to the player from Speedrun.com. Website-specific IDs are not currently supported at this time. If you want to find the Platform ID, research the [Speedrun.com API Documentation](https://github.com/speedruncomorg/api/tree/master/version1).
-   Give your player a name and, optionally, a nickname.
    -   Nicknames take priority visually on the site, but their name is what is used to access their profile.
-   Input the URL to the Speedrun.com player.
-   Select the Country (Country Code) of the player.
-   Input the URL to their profile picture.
    -   By default, if the player had a profile picture on Speedrun.com, it is downloaded and linked here.
-   Input the pronouns of the player.
-   Add the social media links (full links, not aliases or shorthand) for the player.
-   Optionally, you can select "Stream Exception" on this player and they will not appear on the main page when they are streaming and will not appear in the `/live/` endpoint.
-   Select whatever award(s) you want to give them.
    -   Hold down "Control" on Windows or "Command" on Mac OS to select more than one.
-   Click "Save".

### Model Structure
| Field        | Inputs |
| ------------ | ------ |
| id (PK)      | 10 char limit |
| name         | 30 char limit, "Anonymous" default |
| nickname     | 30 char limit |
| url          | URL field |
| countrycode  | `CountryCodes` FK |
| pfp          | 100 char limit |
| pronouns     | 20 char limit |
| twitch       | URL field |
| youtube      | URL field |
| twitter      | URL field |
| bluesky      | URL field |
| ex_stream    | bool |
| awards       | ManyToMany |

### Endpoint
`/api/players/<ID>`


## Runs
`Runs` holds the individual speedruns found on the leaderboards.

### View
-   "By Full-Game or IL" - Filters for the only full game or individual level speedruns or both.
-   "By Obsolete?" - Filters for only runs that are marked obsolete or not or both.
-   "By Game" - When a game is chosen, all Runs that belongs to that game via the `game` field will be filtered.
-   "By Platform" - When a platform is chosen, all Runs that belong to that platform via the `platform` field will be filtered.
-   Search Bar - Searching is based on what is in the `id` field.

### Actions
-   "Delete selected series" - Deletes all selected Series permanently.
    -   **All `RunVariableValues` asscociated with this run will be orphaned (will lose that run as a foreign key)!**

### Adding Runs

### Model Structure
| Field        | Inputs |
| ------------ | ------ |
| id (PK)      | 10 char limit |
| runtype      | `main` or `il` |
| game         | `Games` FK |
| category     | `Categories` FK |
| level        | `Levels` FK |
| subcategory  | 100 char limit |
| variables    | THROUGH model to `RunVariableValues` |
| player       | `Players` FK |
| player2      | `Players` FK |
| place        | int |
| url          | URL field |
| video        | URL field |
| date         | DateTime field |
| time         | 25 char limit |
| time_secs    | Float field |
| timenl       | 25 char limit |
| timenl_secs  | Float field |
| timeigt      | 25 char limit |
| timeigt_secs | Float field |
| points       | int |
| platform     | `Platforms` FK |
| emulted      | bool
| vid_status   | `verified`, `new`, or `rejected` |
| approver     | `Players` FK |
| obsolete     | bool |
| arch_video   | URL field |
| description  | 1000 char limit |

### Endpoint
`/api/runs/<ID>`


## API Keys
###### Third-Party Middleware
By default, in order to access the REST API associated with this project, you must have an API token.

### View
-   "By Created" - Allows you to filter what API Keys have bene created within the time period specified.
-   Search Bar - Searching is based on what is found in `name` or `prefix` field.

### Actions
-   "Delete selected API keys" - Deletes all checked API keys permanently.

### Adding Keys
-   Click on the "Add API Key" option in the API Key interface.
-   Give your API Key a unique name that describes its function, who it belongs to, or whatever else. Being descriptive helps.
-   Give a Date and Time for when the key expires. If you want this to be a key that lasts forever, choose something like 2999 as the year.
-   Click "Save".
-   On the next screen, you will be presented the API key. **THIS IS THE ONLY TIME YOU WILL SEE IT!!**

### Revoking/Expiring Keys
-   Once the date/time set when the key was setup lapses, the key is no longer valid and can never be used again.
-   If you go to a key and check "Revoked", then the key is added to revocation and can never be used again.

### Using Keys
-   In order to use the keys, you must setup your headers a specific way. You must use an `Authorization` header, with associated data being "Api-Key <KEY>".
-   The following is a snippet of Python code that uses the `requests` library:

```
import requests

headers = {'Authorization': f"Api-Key @$#F$#T#%$FEFD@T%#GSFDGEW"}

requests.get(f"https://thps.run/api/runs/{runid}/", headers=request_headers)
```


## Streaming
`Streaming` is a model that helps track which runners are currently streaming.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected streams" - Deletes all selected Streams permanently.

### Adding Stream
-   Click "Add Stream" on the Streams interface.
-   Select the player who is streaming.
-   Select the game they are streaming.
-   Add the title of the Twitch stream.
-   Increment the counter (or start at 0) to mark how many offline attempts have been made.
    -   Sometimes the Twitch API messes up a little bit or a player goes offline temporarily. With this counter, you can decide *when* you want to remove the stream completely through the API.
-   Select the start date and time.
-   Click "Save".

### Model Structure
| Field       | Inputs |
| ----------- | ------ |
| id (PK)     | int, hidden |
| streamer    | `Players` FK |
| game        | `Games` FK |
| title       | 100 char limit |
| offline_ct  | int |
| stream_time | DateTime field |

### Endpoint
`/api/live`