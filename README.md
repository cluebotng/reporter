ClueBot NG — Report Interface
=============================

The report interface handles false positive submission reports & interacts with the local database.

# Runtime dependencies

## MySQL

The bot database is a hard runtime dependency.

* `vandalism` & `beaten` are written by the bot, these are read only & not managed here.
* `reports`, `comments`, `users` & `edits_sent_for_review` are managed here.

Configuration via environment variables:

* `TOOL_TOOLSDB_HOST` - database host.
* `TOOL_TOOLSDB_USER` - database user.
* `TOOL_TOOLSDB_PASSWORD` - database password.
* `TOOL_TOOLSDB_SCHEMA` - database schema.

## Redis

Required for sessions.

* `REDIS_HOST` - redis host.
* `REDIS_PASSWORD` - redis password.

## Secrets

Required for Django:

* `DJANGO_SECRET_KEY`

Required for (OAuth) authentication:

* `CBNG_REPORT_OAUTH_KEY`
* `CBNG_REPORT_OAUTH_SECRET`

# Deployment

The production deployment is handled via a build pack,
see https://wikitech.wikimedia.org/wiki/Help:Toolforge/Building_container_images for more details.

## Development

For development purposes a local configuration file will be required along the lines of

```
django:
  debug: true

oauth:
  key: xxxx
  secret: xxxx

mysql:
  default:
    host: 127.0.0.1
    user: cbng_reporter
    schema: cbng_reporter

redis:
  host: null
```
