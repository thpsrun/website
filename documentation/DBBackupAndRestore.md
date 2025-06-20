# Database Backup and Restore

## Requirements
-   rclone
-   Backblaze B2 Bucket (others are supported, but this code is specifically for B2)
-   Linux machine (distro shouldn't matter)

## rclone Setup
1.  Type `rclone config` into a terminal.
2.  Type `n` into the terminal to create a new remote. Name it `B2`. Type `5` to set the type as Backblaze B2.
3.  Go to [https://secure.backblaze.com/app_keys.htm](https://secure.backblaze.com/app_keys.htm), then click "Add a New Application Key".
4.  Use the following settings:
    *   Name the key something you will recognize.
    *   Allow access to a specific bucket or all buckets.
    *   Set the type of access to `Read and Write`.
    *   (Optional) Give uploaded files a prefix.
    *   (Optional) Set the duration (in seconds).
5.  Take the new `keyID` and `applicationKey` and store them in a secure place (password manager, for example).
6.  Give rclone your `keyID` first, then your `applicationKey`. Follow the rest of the on-screen prompts, then press `y` to confirm your settings.

## Backing Up Database
-   `chmod +x ./db_backup.sh`
-   `./db_backup.sh`

This script will automatically backup the ENTIRE database to a gunzip'd SQL file to store locally, then use rclone to upload to the B2 bucket. Additionally, backups greater than 7 days will be automatically removed locally (rclone backup will not be affected).

#### Note: If you don't want to use rclone, remove or comment out the rclone line in `db_backup.sh`.

## Restoring Database
### NOTE: This operation will remove everything from the database, then add everything back from the file you specify. If you are going to do this, backup first!

-   `chmod +x ./db_restore.sh`
-   `./db_restore.sh`

You will be prompted with all *.sql.gz files in the backups directory. Pick the one you want and it'll overwrite the database.

## Crontab Syntax
### NOTE: This obviously only works on *nix-based operating systems.

-   `0 0 * * * cd ~/website; ./db_backup.sh`
    -   Every day at midnight (for the server), the backup is executed.
-   `*/10 * * * * docker exec django python3 manage.py collectstatic --noinput`
    -   Every 10 minutes, static image collection is ran.