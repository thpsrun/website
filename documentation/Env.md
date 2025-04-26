# Environmental Variables
## What are they?
This project uses environmental variables to ensure that secrets and customizable information are not hard-coded. If you have absolutely no clue what they are, check out this [Wikpedia article](https://en.wikipedia.org/wiki/Environment_variable).

This section has broken up the environmental variables into loose sections:
- [Setup](#setup)
- [Section 1: Secrets](#secrets)
- [Section 2: Backblaze](#backblaze-b2-bucket-optional) (optional)
- [Section 3: Sentry.io](#sentryio-support-optional) (optional)
- [Section 4: Metadata](#metadata)
- [Section 5: Social Media](#social-media)
- [.env.example](#copy-of-envexample)

## Setup
When you initially pull this project, you should see a `.env.example` file. Open this file in your text editor or IDE of choice, and modify the variables you see within it. Afterwards, save it as a `.env` (get rid of `.example`). If you do not do this, your project will fail to start since it needs that `.env` to load the variables.

If you need a new template, it is at the bottom of this page!

## Secrets
```
COMMUNITY_NAME="<COMMUNITY_NAME>"
POSTGRES_NAME="<POSTGRES_TABLE>"
POSTGRES_USER="<POSTGRES_USER>"
POSTGRES_PASSWORD="<POSTGRES_PASSWORD>"
SECRET_KEY="<SECRETKEY>" # https://djecrety.ir
SSL_HOST="<WEBSITE_URL>"
DEBUG_MODE="True" # MAKE SURE THIS IS SET TO FALSE IN PRODUCTION!!
ALLOWED_HOSTS=<IP>,localhost
```

### COMMUNITY_NAME
-   Name of your community.
-   Must equal a string in quotes. Remove `<COMMUNITY_NAME>` and put the name of your community here.
    -   Example: `COMMUNITY_NAME="THPS.RUN"`

### POSTGRES_NAME
-   Name of the table Django will use in the Postgres database and what is created in Postgres.
-   Must equal a string in quotes. Remove `<POSTGRES_TABLE>` and put the name of your table here.
    -   Do NOT input special characters. Alphanumeric (A-Z,0-9) and underscores only!
    -   Example: `POSTGRES_NAME="pokemon_community"`

### POSTGRES_USER
-   Name of the user that accesses the Postgres database from the `POSTGRES_NAME` variable.
-   Must equal a string in quotes. Remove `<POSTGRES_USER>` and put the name of your user here.
    -   Do NOT input special characters. Alphanumeric (A-Z,0-9) only!
    -   Example: `POSTGRES_USER="bobbyb"`

### POSTGRES_PASSWORD
-   The password for the `POSTGRES_USER` to access the database stated in `POSTGRES_NAME`.
-   Must equal a string in quotes. Remove `<POSTGRES_PASSWORD>` and put your password here.
    -   Keep it secret, keep it safe!!
    -   Make sure this is a UNIQUE password.
        -   Note: This database is only accessible to other Django applications within the created network and is not readily exposed to the Internet. However, you still want to utilize good passwords here!
    -   Example: `POSTGRES_PASSWORD="supers3cretp@$$w0rd"`

### SECRET_KEY
-   This is the Django secret key that is used for pretty much everything. This is in charge of a lot of cryptographic functions like signing, ensuring integrity of sensitive information, session cookies, passwords, and so on. If this is ever leaked, that is pretty bad and you will need to rotate it immediately.
-   Use [Djecrety](https://djecrety.ir/) to generate your `SECRET_KEY`!!
-   Must equal a string in quotes. Remove `<SECRETKEY>` and put the new key in here.
    -   Keep it secret, keep ti safe!!!!
    -   Example: `SECRET_KEY="ql3#swoauvfa^as!=+-i0-pj5c7c&@yxy"`

### SSL_HOST
-   This is the domain name of your website when you have an SSL certificate assigned. Having an SSL certificate setup with Nginx or Nginx Proxy Manager or other tools and NOT setting this will result in errors.
-   Must equal a string in quotes. Remove `<WEBSITE_URL>` and put your domain name in here.
    -   Example: `SSL_HOST="twitch.tv"`

## Backblaze B2 Bucket (Optional)
```
B2_BUCKET=<BUCKET>
B2_KEY=<BUCKET KEY>
B2_APP=<BUCKET APP KEY>
```

### What is Backblaze?
Backblaze (B2) is a cloud storage service that is a lot like Amazon Web Service's S3 Buckets. Instead, these are a lot more affordable. The reason these are here is that there is an optional component that automates the database backups for your Postgres database and imports them into your B2 bucket.

For more information, check out Backblaze's article on [Application Keys](https://www.backblaze.com/docs/cloud-storage-application-keys).

## Sentry.io Support (Optional)
```
SENTRY_ENABLED="False"
SENTRY_DSN="<SENTRY_LINK>"
```

### What is Sentry?
[Sentry.io](https://sentry.io) is a service that works to consolidate errors, logs, crashes, and so on for an application into a single place. You can add automations that make it so you are emailed or notified in Discord when a new error occurs. It gives you information on what was raised, where in the code it was raised, your variables, and so on.

As a note, this is NOT strictly a Sentry.io thing. Sentry.io can cost money and its self-hosted options aren't super great. If you want more open-source options, you can try [GlitchTip](https://glitchtip.com/) or [BugSink](https://www.bugsink.com/). Both of these tools use the same Sentry SDK found in the Django code; all you need to do is setup your instance of either, follow the instructions, and input the DSN code they give you into the `SENTRY_DSN` variable.

And, of course, if you want this disabled, make sure `SENTRY_ENABLED` is set to `False`. If you want to use a Sentry-enabled service, make sure this is set to `True`.

## Metadata
```
SITE_NAME="<WEBSITE NAME>"
SITE_KEYWORDS=KEYWORDS,SEPARATED,BY,COMMAS
SITE_AUTHOR=<AUTHOR>
SITE_DESCRIPTION=<DESCRIPTION>
```

### Metadata Overview
Metadata is embedded information on web pages that describe the site, what the page is about, who created that page, and keywords. For more information on what this does, check out [Mozilla's article](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content/Webpage_metadata).

### SITE_NAME
-   The name of your site.
-   Must equal a string in quotes. Remove `<WEBSITE_NAME>` and input your site name here.
    -   Example: `SITE_NAME="Speedrun.com"`

### SITE_KEYWORDS
-   The primary keywords that are used for your site. When people search terms in a search engine, this can cause your web pages to show up higher in the rankings.
    -   Note: This is for ALL web pages. If you want granular control of what keywords are used for what web pages, you will need to modify the specific templates used in this project.
-   Must be equal to a string in quotes (if spaces or special characters) or without quotes if single words. All keywords must be separated by a comma. Remove `KEYWORDS,SEPARATED,BY,COMMAS` and put your keywords there.
    -   Example: `SITE_KEYWORDS=THESE,KEYWORDS,REALLY,SUCK,DONT,THEY`

### SITE_AUTHOR
-   This is the author of the webpage. This can be the name of the community or a specific person.
    -   Note: This is for ALL web pages. If you want granular control of what keywords are used for what web pages, you will need to modify the specific templates used in this project.
-   Must equal a string in quotes. Remove `<AUTHOR>` and input whatever you want there.
    -   Example: `SITE_AUTHOR="Ligma"`

### SITE_DESCRIPTION
-   Generic description for a webpage that will display when you find the web page in a search engine.
    -   Note: This is for ALL web pages. If you want granular control of what keywords are used for what web pages, you will need to modify the specific templates used in this project.
-   Must equal a string in quotes. Remove `<DESCRIPTION>` and input your description here.
    -   Example: `SITE_DESCRIPTION="This is a generic description that describes my webpage."`

## Social Media
```
DISCORD_URL="<DISCORD>"
TWITTER_URL="https://twitter.com/<TWITTER>"
TWITCH_URL="https://twitch.tv/<TWITCH>"
YOUTUBE_URL="https://www.youtube.com/<YOUTUBE>"
SRC_URL="https://speedrun.com/<SERIESNAME>"
BLUESKY_URL="https://bsky.app/profile/<HANDLE>"
```

### Social Media
Each of these links follow the same formatting and behavior on the site.
-   IF THERE IS A LINK, that respective social media icon will appear on the NavBar on the top of every webpage.
-   IF THERE IS NO LINK, then that respective social media icon will NOT appear.

-   Example: `BLUESKY_URL="https://bsky.app/profile/thps.run"`


## Copy of .env.example
```
COMMUNITY_NAME="<COMMUNITY_NAME>"
POSTGRES_NAME="<POSTGRES_TABLE>"
POSTGRES_USER="<POSTGRES_USER>"
POSTGRES_PASSWORD="<POSTGRES_PASSWORD>"
SECRET_KEY="<SECRETKEY>" # https://djecrety.ir
SSL_HOST="<WEBSITE_URL>"
DEBUG_MODE="True" # MAKE SURE THIS IS SET TO FALSE IN PRODUCTION!!
ALLOWED_HOSTS=<IP>,localhost

# Used for the db_backup.sh script. Instructions in README.
B2_BUCKET=<BUCKET>
B2_KEY=<BUCKET KEY>
B2_APP=<BUCKET APP KEY>

# Sentry.io/Bugsink/GlitchTip sentry setup for consolidating logs
SENTRY_ENABLED="False"
SENTRY_DSN="<SENTRY_LINK>"

# Metadata for the website
SITE_NAME="<WEBSITE NAME>"
SITE_KEYWORDS=KEYWORDS,SEPARATED,BY,COMMAS
SITE_AUTHOR=<AUTHOR>
SITE_DESCRIPTION=<DESCRIPTION>

# If you do not want to use one of these on the website;leave it equal to ""
DISCORD_URL="<DISCORD>"
TWITTER_URL="https://twitter.com/<TWITTER>"
TWITCH_URL="https://twitch.tv/<TWITCH>"
YOUTUBE_URL="https://www.youtube.com/<YOUTUBE>"
SRC_URL="https://speedrun.com/<SERIESNAME>"
BLUESKY_URL="https://bsky.app/profile/<HANDLE>"
```

