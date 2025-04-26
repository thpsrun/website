# thps.run Documentation

## What is this?
This is the documentation for thps.run website. Since this is open source, you are allowed to pull this repo and make your own version! And, hopefully with this, you will get a better idea of how things work. This section includes the following:

*   Known caveats and issues
*   Admin Panel functionality
*   API Documentation
*   Other stuff

This section *should* help with just about everything, from start to finish. If you have any issues, feel free to make an Issue to request help or reach out to ThePackle on Discord [THPS Speedrun Discord](https://thps.run/discord).

## Components
*   Django
    *   If you wanna learn more about Django, go here: [djangoproject.com](https://www.djangoproject.com/)
*   PostgreSQL
    *   SQL database holding all of the games, categories, sub-categories, variables, and runs for your series. Also holds additonal stuff like hashed user credentials and other goodies.
        *   The cool thing about Django is that you will very rarely interact with raw SQL! But, it is still good to know what is under the hood.
*   redis
    *   Data platform who's job for this project is to handle celery runners to make automations smoother and faster.
        *   Later releases of this project might leverage this for caching and stuff.


## How does this all work?
The best way to think of this project is that it is a "cache" for your community's speedruns. Upon initialization, all speedruns (to include obsolete speedruns) are imported into your local database.


## Basics
### Overall
*   !! This project assumes your community is a collection of games known as a "Series". If you do not have a Series, this project may still work for you, but things like SRC game IDs and such will need to be imported manually.
*   Pretty much all dates and times follow [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601).
*   This project assumes you have a basic understanding of at least Python, but experience in Django will help as well! This was created as an in-house solution for the thps.run website, but with the idea that (eventually) this could be used as a template for other communities.
    *   With that said, there will be a handful of things that is tailored *specically* for the THPS community. Some features are not going to be completely ready out of the box.


### Hosting
*   [thps.run](https://thps.run) is hosted on Hetzner cloud servers using Docker containers. I tried my best to make this as lightweight and open as possible. With this in mind, it *shouldn't* matter if this is on Windows or Linux - but this project has primarily been developed with Linux in mind!


### API
*   All responses from the API responds with either raw JSON and the HTTP status code. While this API mimics a lot of things from the [SRC API](https://github.com/speedruncomorg/api), there are no such things like a `data` key.
*   As of writing (version 3.0), there is no limitations on returned elements. Later versions *may* introduce pagination, but will be projected ahead of time and easily disabled.
*   The API will require that you create an API Key through the Admin Panel. This is explained in the [Admin Panel](AdminPanel.md) section.

