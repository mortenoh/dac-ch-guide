# Upgrading and restoring chap

This is a reference page for maintaining an existing setup, not part of the core workshop.

chap-core is pinned to a specific version, so upgrading is a deliberate step. On start, a new
version **migrates the chap database automatically** - which is convenient, but means you
cannot simply downgrade afterwards. So the rule is: **back up first, then upgrade**, and keep
the dump in case you need to roll back.

The steps differ slightly depending on how you run CHAP - the bundled images or a from-source
build. Pick your path below. (This mirrors the official
[Upgrading CHAP](https://chap.dhis2.org/chap-modeling-platform/modeling-app/upgrading-installation/)
guide, adapted to the stacks in these guides.)

!!! warning "Back up before you upgrade"
    The upgrade migrates the database and migrations are one-way. Take a dump first - see
    [Backup and restore](backup-restore.md) - so a failed or unwanted upgrade is recoverable.

## Bundled CHAP (docker-dhis2-core)

You run CHAP with `docker compose -f compose.chap.yml …`, and the version lives in the image
tags in `compose.chap.yml`.

### Step 1 - Note the version and back up

```bash
docker compose -f compose.chap.yml exec chap \
  python -c 'import chap_core; print(chap_core.__version__)'

docker compose -f compose.chap.yml exec -T chap-postgres \
  pg_dump -U chap -Fc chap_core > chap_core_pre-upgrade.dump
```

### Step 2 - Set the new version

In `compose.chap.yml`, change the **two** chap image tags to the target version (keep `chap`
and `chap-worker` on the **same** version) - for example `:v2.0.0` -> `:v2.1.0`:

```yaml
  chap:
    image: ghcr.io/dhis2-chap/chap-core:v2.1.0      # was :v2.0.0
  chap-worker:
    image: ghcr.io/dhis2-chap/chap-worker:v2.1.0    # was :v2.0.0
```

Available versions are the tags on the
[chap-core releases](https://github.com/dhis2-chap/chap-core/releases).

### Step 3 - Pull and recreate

```bash
docker compose -f compose.chap.yml pull chap chap-worker
docker compose -f compose.chap.yml up -d
```

chap runs its database migrations on startup - no manual migration step is needed.

### Step 4 - Verify

```bash
docker compose -f compose.chap.yml exec chap \
  python -c 'import chap_core; print(chap_core.__version__)'   # the new version
curl -s -u admin:district "http://localhost:8080/api/routes/chap/run/health" | jq
```

### Step 5 - Roll back if needed

Put the old tags back in `compose.chap.yml`, then:

```bash
docker compose -f compose.chap.yml pull chap chap-worker
docker compose -f compose.chap.yml up -d
```

If the newer version had already migrated the database, the old version may not read it - then
also **restore your dump**:

```bash
cat chap_core_pre-upgrade.dump | docker compose -f compose.chap.yml exec -T chap-postgres \
  pg_restore -U chap -d chap_core --clean --if-exists
```

## From-source CHAP (chap-core)

You run CHAP from the cloned **chap-core** repo, so the version is whatever git revision you
have checked out.

### Step 1 - Note the version and back up

```bash
docker compose -f compose.yml -f compose.chapkit.yml exec chap \
  python -c 'import chap_core; print(chap_core.__version__)'

docker compose -f compose.yml -f compose.chapkit.yml exec -T postgres \
  pg_dump -U chap -Fc chap_core > chap_core_pre-upgrade.dump
```

### Step 2 - Update the repository

```bash
git fetch --tags
git tag -l                  # list available versions
git checkout v2.1.0         # the version you want (or 'master' for the latest)
```

### Step 3 - Rebuild and restart

```bash
docker compose -f compose.yml -f compose.chapkit.yml up -d --build
```

If a stale layer causes trouble, force a clean build:

```bash
docker compose -f compose.yml -f compose.chapkit.yml build --no-cache
docker compose -f compose.yml -f compose.chapkit.yml up -d
```

Migrations run automatically on startup.

### Step 4 - Verify

```bash
docker compose -f compose.yml -f compose.chapkit.yml exec chap \
  python -c 'import chap_core; print(chap_core.__version__)'
curl -s http://localhost:8000/health | jq
```

### Step 5 - Roll back if needed

```bash
git checkout <previous-version>
docker compose -f compose.yml -f compose.chapkit.yml up -d --build
```

Restore the dump as well if the database was already migrated (same `pg_restore` command as the
bundled path, with `postgres` as the service name).

!!! note "Version-specific notes (from the official guide)"
    - **v1.1.5+** needs a `.env` file - copy `.env.example`, but keep your existing PostgreSQL
      credentials if you are migrating an existing database.
    - **v1.2.0+** moved the runs volume from `/app/runs` to `/data/runs` (handled automatically).

    Always check the [release notes](https://github.com/dhis2-chap/chap-core/releases) for the
    version you are moving to.

!!! note "Assignment: a safe upgrade"
    - [ ] Record the running `chap_core` version and take a pre-upgrade dump.
    - [ ] Change to the target version (image tag, or `git checkout`) and bring the stack back
      up.
    - [ ] Verify the new version and a healthy route - and know how to restore the dump if not.

## What's next

You can now run, inspect, and upgrade the platform safely. The remaining advanced topics -
such as batch-evaluating several models and comparing their metrics - build on the model
workflow you already know.
