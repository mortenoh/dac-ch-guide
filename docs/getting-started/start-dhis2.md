# Run DHIS2 with Docker

This is step 2 of the workshop. It starts DHIS2 with the Laos climate demo database; CHAP is
added in the next step.

In this guide you bring up a complete DHIS2 instance on your own machine using Docker. It
comes pre-loaded with a **climate demo database** (Laos), so you have realistic data to model
against in the later guides - no manual import needed.

You will not install DHIS2, Java, or PostgreSQL by hand. A single `docker compose` command
starts everything: the DHIS2 web application, its database, a one-time data load, and the
analytics tables that the Data Visualizer and the Modelling App rely on.

!!! note "Before you start"
    Complete [step 1: prepare your machine](prerequisites.md). Docker and Docker Compose must
    be installed and running.

## Step 1 - Get the setup repository

Clone the DHIS2 Docker setup and move into it:

```bash
git clone https://github.com/dhis2-chap/docker-dhis2-core
cd docker-dhis2-core
```

This repository contains the Docker Compose files used below. You do not need to edit anything
to get started - every setting has a working default. All the commands here are run from inside
this folder.

## Step 2 - Start the stack

```bash
docker compose up -d
```

The `-d` runs it in the background. Follow the logs while it comes up (press `Ctrl+C` to stop
following - that does not stop the stack):

```bash
docker compose logs -f
```

The **first** start does the most work:

1. Downloads and prepares the Laos climate demo database (a few hundred MB - one time).
2. Loads it into PostgreSQL and runs DHIS2's database migrations.
3. Boots the DHIS2 web application.
4. Generates the `analytics_*` tables so charts, maps, and CHAP have data to read.

First boot takes a few minutes. Later starts are much faster because the database is already
loaded.

## Step 3 - Watch it come up

Check container status:

```bash
docker compose ps -a
```

You are waiting for the web container to report **healthy** and the one-shot helpers
(`db-dump`, `db-prep`, `analytics`, `chap-route-init`) to have **Exited (0)** - that exit code
means they finished their job, not that they failed:

```text
docker-dhis2-core-dhis2-web-1         Up (healthy)
docker-dhis2-core-dhis2-db-1          Up (healthy)
docker-dhis2-core-dhis2-analytics-1   Exited (0)
docker-dhis2-core-dhis2-db-dump-1     Exited (0)
docker-dhis2-core-dhis2-db-prep-1     Exited (0)
docker-dhis2-core-chap-route-init-1   Exited (0)
```

!!! note "What is `chap-route-init` doing here?"
    Even the DHIS2-only stack pre-configures the DHIS2 -> CHAP route so it is ready when you
    add CHAP later. You do not need CHAP running yet - this just points the route at where a
    local CHAP would be. The [Run chap-core](add-chap-core.md) guide covers it.

## Step 4 - Log in

Open DHIS2 in your browser:

```text
http://localhost:8080
```

Log in with the demo credentials:

- **Username:** `admin`
- **Password:** `district`

!!! note "Assignment: confirm DHIS2 is running"
    - [ ] `docker compose ps -a` shows `dhis2-web` as **Up (healthy)**.
    - [ ] You can log in at `http://localhost:8080` with `admin` / `district`.
    - [ ] Open **Apps -> Data Visualizer** and confirm you can see organisation units and
      data - this means the demo database and analytics tables loaded correctly.

    If the page does not load yet, give it another minute (first boot is the slow one) and
    check `docker compose logs -f`.

## What you should see

This is the Laos climate demo database. A quick way to confirm it from the command line:

```bash
curl -s -u admin:district http://localhost:8080/api/system/info.json | jq -r .version
```

You should get DHIS2 version `2.42.x` back. The instance ships with a full organisation-unit
hierarchy and climate-relevant data elements - everything CHAP needs to train and predict in
the next guides.

## Managing the stack

```bash
docker compose ps -a       # container status
docker compose logs -f     # follow logs
docker compose stop        # stop (keeps data; resume with `up -d`)
docker compose down        # remove containers (keeps the database volume)
docker compose down -v     # full reset: also wipe volumes (fresh dump + analytics next start)
```

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Browser cannot reach `localhost:8080` | Web container still booting - wait and re-check `docker compose ps -a`. |
| `analytics` container shows `Exited (1)` | DHIS2 likely ran out of memory during the analytics build. Raise Docker's memory to 6-8 GB and re-run `docker compose up -d`. |
| Port `8080` already in use | Another service holds it. Stop that service, or start with a different port: `DHIS2_PORT=8081 docker compose up -d`. |
| Want a completely fresh start | `docker compose down -v` wipes the volumes; the next `docker compose up -d` reloads the dump + analytics from scratch. |

## Next step

Continue to [step 3: choose how to connect CHAP](chap-setup.md).
