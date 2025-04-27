# thps.run Admin Panel

## What is the Admin Panel?
Within Django, it has an incredibly powerful and built-in administration interface. This isn't meant for everyday users to access, but it helps manage your Models a lot easier, allows you to modify objects, and even search for objects based on parameters.

This section will discuss each individual part of the Admin Panel. If you want to know more about how it works, check out the [Django documentation](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/).

-   [API Keys](#api-keys)
-   [Categories](#categories)
-   [Country Codes](#country-codes)
-   [Games](#games)


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
| id (PK)     | int |
| name        | 50 char limit, unique |
| image       | 64x64, 3MB limit |
| description | 500 char limit |

### Endpoint
There is no endpoint for Awards.


## Categories
`Categories` are, as the name says, the regular categories for games in the `Games` model.

### View
-   "By Linked Game" - When a game is chosen, all Categories that belongs to that game via the `game` field will be filtered.
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected categories" - Deletes all Categories selected permanently.
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
<<INPUT TO CATEGORIES API>>


## Country Codes
`Country Codes` is a small model that lists the unique abbreviation or slug for a country and associates it with their full name (e.g., `us` and `United States`).

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected Country Codes" - Deletes all checked Country Codes permanently.
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


## Games
`Games` holds all of the metadata information for games within your `Series`. Without a game in place, you cannot add `Categories`, `Variables`, or `Runs` to it.

### View
-   Search Bar - Searching is based on what is in the `name` field.

### Actions
-   "Delete selected Games" - Deletes all checked Games permanently.
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
<<INPUT TO GAMES API>>


## Levels
