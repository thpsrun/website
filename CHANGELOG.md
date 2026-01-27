### v4 - The <Something> Update
###### ???

### Major Changes
*   Entire frontend of the website is redesigned. New UI, not basic HTML/JS, and much more!!? This is all hosted on the frontend repo, just to keep Django's complexities separate from React's. (Noami)
    *   New main page!
    *   New game screen!
    *   New login system! (Packle)
*   Migrated the entire API to Django Ninja.
    *   Versioned the API endpoints for future-proofing and upgrading and testing and stuff. (Packle)
    *   GET endpoints are now publicly accessible! All other methods will require authentication.
        *   Roles system has also been added to API keys to manage scope and rate-limiting.
    *   Documentation is also publicly accessible via `/api/v1/docs`.
*   Rebuilt the Guides system to be within the API instead of GitHub.
*   Consolidated the SRC -> thps.run pipeline from two different chains into one.
*   Caching has been added to all API endpoints.
    *   Cached responses last ~7 days.
        *   Upon a run, category, or player account being updated, then this will also update the cached

### Added
*   Added new login system that allows you to create an account on thps.run and associate your account with SRC.
    *   Logins can be created through the new login interface or through OAuth with Discord.
    *   Added support for token-based one-time passwords (TOTP) to use with your favorite authenticator app or the use of Passkeys.
        *   Contributors and higher are required to have this enabled.
*   Added new user system and profile editing system.
    *   NOTE: When a login is created and associated to your SRC account, thps.run/THPSBot will NOT update your fields automatically anymore. You can edit them inyour new profile page!
*   Added new revision to accomodate addition of storing user credentials/OAuth tokens to the Privacy Policy.
*   Added `appear_on_main` field to `Categories` field that will allow for querying only categories that, well, we only want to appear on the main page.
*   Added `archived` field to `Variables`, `VariableValues`, `Categories`, and `Levels`.
*   Added a `Categories`-specific override that lets you force change the default timing method of the category.
    *   THPS4 5th Gen, you're welcome.
*   Added `slug` field to `Variables`, `VariableValues`, `Categories`, `Levels` and `Platforms`.
*   Added a new `/website` endpoint that is more catered to interacting with React.
*   Added Pydantic schema and models.
    *   About time tbh.

### Fixed
*   Fixed the type checking for API responses to be `JsonResponse` and not `HttpResponse`.
*   Fixed the logic calculating a run's `points` and `place` fields so they are more consistent.

### Changed
*   Changed the Guides system so it can be accessible via the Django Admin interface (for super admins of the project), the API via GET request, and the new portal.
*   Changed the API key system so that it will be scoped based on role. Each role has different rate limits (with admins having unlimited).
*   Changed the ordering of levels and category names so they reflect better what is seen on Speedrun.com.
    *   This is mostly hard-coded. Ordering on SRC is done on server-side, so there is no way around that besides either having a "ranking" system or just hard-coding what the order should be. (Sue me).
*   Changed the API so it is separated into "general"/"standard" and "website" API requests.
    *   React will be using a lot of the thps.run API, so separating this will help keep features separate and also allow us to do fancier things.
*   Changed the `/player` endpoint to both return no stats on default and to require the `?embed=stats` request to add stats to the query.
    *   When interacting with larger sets of data, especially when stats aren't required, it can cause slow down.
*   Changed `hidden` to `archive` within `Variables`, `VariableValues`, and `Categories`.
    *   `Archive` will mimic what you see from archived variables or categories. They are excluded from searches, as well, but will help ensure runs do not get orphaned.

### Removed
*   

### Misc.
*   

### TODO
*   Caching
*   [LOW] Fix `Categories` `defaulttime` logic to override the main game when they are different.
*   Fix `init_series.py` to accomodate newly refactored SRC logic.
*   Add new login system and upgrade `Users` model to accept OAuth tokens from Discord, allow for new signups, and require an SRC account.
    *   When synced, SRC account should be crawled to see if the user has any runs in the database; if no, then they are restricted.
    *   TOTP-based tokens and Passkeys should also be added.
    *   Revise Privacy Policy on new guidelines.
*   Upgrade the `website` endpoint with custom APIs for:
    *   Main Page
    *   Player Profile
        *   Run History
    *   Overall Points Leaderboard
    *   IL Leaderboard Per Game
        *   Special version for THPS4 and THPS12CE(?)
    *   Single-game IL Leaderboard
    *   Full-game leaderboard
        *   With pagination?
*   Research caching for website endpoint (~5m?)
    *   Other endpoints would be exempted