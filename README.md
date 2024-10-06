# thps.run - Speedrun Leaderboard Creator (SRLC)
## Version 2.0

### License
SRLC uses

### What the heck is this??
This has been the pet project of [ThePackle](https://twitch.tv/thepackle) for a few years now. In short, it is a highly-customizable, easy-to-use, and interesting way to create a website that mimics a lot of the leaderboard functionality seen from [HaloRuns](https://haloruns.com). Built entirely in Django 5.1 (Python), this is the open-source files used for websites like [THPS.RUN](https://thps.run).

This version of SRLC assumes that the administrator is a newbie to Python and/or Django; most processes are already automated and ready to be used. That said, if you have experience with either or both, you are free to utilize 

In short, there are a few different services built-in to this project:
1. Django Website
  - This is the "grand jewel" of the project. This is a [full-stack](https://www.w3schools.com/whatis/whatis_fullstack.asp) application that pulls from a Postgres database dynamically to update information on the webiste in real-time. Again, an easy example of this is [THPS.RUN](https://thps.run).
2. Postgres Database
  - Django usually utilizes a SQLite3 database, but larger communities will require a better database. Plus, this allows me to more easily tie in the database into future projects (e.g., THPS Twitch bot, more powerful Discord bot, etc.).
3. Custom REST API
  - With the database is a custom API backend that can be called upon for various functions. It is still a work-in-progress, but there is a decent amount you can do with it already!
4. Discord Python Bot
  - While the Discord posting is optional, the Python bot included has a special function. Since Speedrun.com's REST API does not provide webhooks currently, the bot is tasked with continual checks (~1 minute default) to see if any new speedruns are posted in a series. If a new one is found, it is posted to the Discord channel of the user's choice. If approved, the speedrun is given to the API so it can process the new data dynamically!

### Requirements
- [Docker](https://www.docker.com/products/docker-desktop/) (Desktop or Docker Compose is fine)

### Note on Points
The points system utilized within this project was created by ibeechu and goatrope of the <a href="https://haloruns.com">HaloRuns</a> speedrun community. For the use of thps.run, they are used with permission; if you wish to use this points system, then contact them on their official Discord for permission.