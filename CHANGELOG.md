### v4 - The <Something> Update
###### ???

### Major Changes
*   Entire frontend of the website is redesigned. New UI, not basic HTML/JS, and much more!!? This is all hosted on the frontend repo, just to keep Django's complexities separate from React's. (Noami)
    *   New main page!
    *   New game screen!
    *   New login system! (Packle)
*   Versioned the API endpoints for future-proofing and upgrading and testing and stuff. (Packle)
    *   Upgraded the API to Django Ninja to better support async operations in the future.
    *   GET endpoints are now publicly accessible! All other methods will require authentication.
        *   Roles system has also been added to API keys to manage scope.
*   Rebuilt the Guides system to be within the API instead of GitHub.
*   (Planned) Consolidated the SRC -> thps.run pipeline from two different chains into one.
*   Migrated the entire API to Django Ninja, to include role-based API keys to better limit access to endpoints and provide some rate-limiting capabilities.

### Added
*   (Planned) Added new login system that allows you to create an account on thps.run and associate your account with SRC.
    *   (Planned) Logins can be created through the new login interface or through OAuth with Discord.
    *   (Planned) Added support for token-based one-time passwords (TOTP) to use with your favorite authenticator app or the use of Passkeys.
        *   (Planned) Contributors and higher are required to have this enabled.
*   (Planned) Added new user system and profile editing system.
    *   NOTE: When a login is created and associated to your SRC account, thps.run/THPSBot will NOT update your fields automatically anymore. You can edit them inyour new profile page!
*   (Planned) Added new revision to accomodate addition of storing user credentials/OAuth tokens to the Privacy Policy.
*   Added `appear_on_main` field to `Categories` field that will allow for querying only categories that, well, we only want to appear on the main page.
*   Added `archived` field to `Variables`, `VariableValues`, `Categories`, and `Levels`.
*   Added a `Categories`-specific override that lets you force change the default timing method of the category.
    *   THPS4 5th Gen, you're welcome.
*   Added `slug` field to `Variables`, `VariableValues`, `Categories`, `Levels` and `Platforms`.
*   Added a new `/website` endpoint that is more catered to interacting with React.

### Fixed
*   Fixed the type checking for API responses to be `JsonResponse` and not `HttpResponse`.
*   (Planned) Fixed the logic calculating a run's `points` and `place` fields.

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
*   (Planned) Removed the `subcategory` field from the `Runs` model.
    *   This was a remnant from v2 code, before it was more understood how to link variable-value pairs to an individual run.

### Misc.
