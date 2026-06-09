# Backup and restore

This is a reference page. Use it before an upgrade or any other change that could affect
stored runs.

The chap database holds everything you have produced - datasets, evaluations, predictions - so
a `pg_dump` snapshot is worth taking before anything risky. The single most important moment is
**before a chap-core upgrade**, which migrates the database in a way you cannot simply undo.

All commands run from the `docker-dhis2-core` folder (the bundled stack); the
[from-source](#from-source-chap) variant is at the bottom.

## Back up

Dump the **chap** database to a file on your machine, in Postgres' custom (compressed) format:

```bash
docker compose -f compose.chap.yml exec -T chap-postgres \
  pg_dump -U chap -Fc chap_core > chap_core.dump
```

The **DHIS2** database is the same idea on its own service:

```bash
docker compose -f compose.chap.yml exec -T dhis2-db \
  pg_dump -U dhis -Fc dhis > dhis.dump
```

`-Fc` writes the custom format, which you restore with `pg_restore` (below). For a plain-SQL
dump you can read or `grep`, drop the `-Fc` and use a `.sql` name.

## Restore

Restoring **replaces** the current contents, so do it with the **app stopped** - a live `chap`
or `chap-worker` holds connections that can block the drop and can write stale state back
mid-restore. Stop the app (leave the database service running), recreate an empty database,
then load the dump into it:

```bash
# 1. stop the app so nothing holds the database open
docker compose -f compose.chap.yml stop chap chap-worker

# 2. drop and recreate an empty database (--force terminates any leftover connections)
docker compose -f compose.chap.yml exec -T chap-postgres dropdb   -U chap --force chap_core
docker compose -f compose.chap.yml exec -T chap-postgres createdb -U chap chap_core

# 3. restore into the empty database
cat chap_core.dump | docker compose -f compose.chap.yml exec -T chap-postgres \
  pg_restore -U chap -d chap_core

# 4. start the app and confirm it is healthy
docker compose -f compose.chap.yml up -d chap chap-worker
curl -s -u admin:district "http://localhost:8080/api/routes/chap/run/health" | jq
```

Recreating the database (rather than `pg_restore --clean` into the live one) guarantees a clean
result: no objects that were added *after* the dump survive. The DHIS2 database is the same idea
with `dhis2-db`, `-U dhis`, and `dhis` - stop the `dhis2-web` service first.

!!! tip "Test a dump before you trust it"
    To check a dump is good without touching live data, restore it into a throwaway database
    and look around, then drop it:

    ```bash
    docker compose -f compose.chap.yml exec -T chap-postgres createdb -U chap restore_test
    cat chap_core.dump | docker compose -f compose.chap.yml exec -T chap-postgres \
      pg_restore -U chap -d restore_test
    docker compose -f compose.chap.yml exec -T chap-postgres \
      psql -U chap -d restore_test -c "select count(*) from backtest;"
    docker compose -f compose.chap.yml exec -T chap-postgres dropdb -U chap restore_test
    ```

## With pgAdmin

If you use [pgAdmin](database.md#c-pgadmin-a-web-gui), the same lives under **Tools -> Backup…**
and **Tools -> Restore…** - a GUI over `pg_dump` / `pg_restore`.

## From-source chap

If you run CHAP [from source](../getting-started/chap-core-from-source.md), the database service
is `postgres` and the compose flags differ:

```bash
# back up
docker compose -f compose.yml -f compose.chapkit.yml exec -T postgres \
  pg_dump -U chap -Fc chap_core > chap_core.dump

# restore (stop the app, recreate the database, then load the dump)
docker compose -f compose.yml -f compose.chapkit.yml stop chap chap-worker
docker compose -f compose.yml -f compose.chapkit.yml exec -T postgres dropdb   -U chap --force chap_core
docker compose -f compose.yml -f compose.chapkit.yml exec -T postgres createdb -U chap chap_core
cat chap_core.dump | docker compose -f compose.yml -f compose.chapkit.yml exec -T postgres \
  pg_restore -U chap -d chap_core
docker compose -f compose.yml -f compose.chapkit.yml up -d chap chap-worker
```

!!! note "Assignment: a dump you can trust"
    - [ ] Dump the chap database to a file.
    - [ ] Restore it into a throwaway database and confirm your `backtest`s are there.

## What's next

With a dump in hand you can upgrade safely - next, [Upgrading and restoring
chap](upgrading.md).
