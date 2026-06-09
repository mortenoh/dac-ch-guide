# Run DHIS2 with Docker

In this guide you bring up a complete DHIS2 instance on your own machine using Docker. It
comes pre-loaded with a **climate demo database** (Laos), so you have realistic data to model
against in the later guides - no manual import needed.

You will not install DHIS2, Java, or PostgreSQL by hand. A single `make` command starts
everything: the DHIS2 web application, its database, a one-time data load, and the analytics
tables that the Data Visualizer and the Modelling App rely on.

!!! note "Before you start"
    Complete [Overview & Setup](../index.md) first - you need Docker, Docker Compose v2.20+,
    `make`, and `git`, and Docker should have at least 6 GB of memory.

## Step 1 - Get the setup repository

Clone the DHIS2 Docker setup and move into it:

```bash
git clone https://github.com/dhis2-chap/docker-dhis2-core
cd docker-dhis2-core
```

This repository contains the Docker Compose files and a `Makefile` with the shortcuts used
below. You do not need to edit anything to get started - every setting has a working default.

## Step 2 - Start the stack

```bash
make start
```

This runs in the **foreground** - leave the terminal open and watch the logs. Press
`Ctrl+C` to stop (the containers stay and resume on the next `make start`).

The **first** start does the most work:

1. Downloads and prepares the Laos climate demo database (a few hundred MB - one time).
2. Loads it into PostgreSQL and runs DHIS2's database migrations.
3. Boots the DHIS2 web application.
4. Generates the `analytics_*` tables so charts, maps, and CHAP have data to read.

First boot takes a few minutes. Later starts are much faster because the database is already
loaded.

!!! tip "Prefer a detached terminal?"
    `make start` is `docker compose up` under the hood. To run it in the background instead,
    use `docker compose up -d` and follow the logs with `make logs`.

## Step 3 - Watch it come up

In another terminal (from the same folder), check container status:

```bash
make ps
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
    - [ ] `make ps` shows `dhis2-web` as **Up (healthy)**.
    - [ ] You can log in at `http://localhost:8080` with `admin` / `district`.
    - [ ] Open **Apps -> Data Visualizer** and confirm you can see organisation units and
      data - this means the demo database and analytics tables loaded correctly.

    If the page does not load yet, give it another minute (first boot is the slow one) and
    check `make logs`.

## What you should see

This is the Laos climate demo database. A quick way to confirm it from the command line:

```bash
curl -s -u admin:district http://localhost:8080/api/system/info.json | jq -r .version
```

You should get DHIS2 version `2.42.x` back. The instance ships with a full organisation-unit
hierarchy and climate-relevant data elements - everything CHAP needs to train and predict in
the next guides.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Browser cannot reach `localhost:8080` | Web container still booting - wait and re-check `make ps`. |
| `analytics` container shows `Exited (1)` | DHIS2 likely ran out of memory during the analytics build. Raise Docker's memory to 6-8 GB and re-run `make start`. |
| Port `8080` already in use | Another service holds it. Stop that service, or start with a different port: `DHIS2_PORT=8081 make start`. |
| Want a completely fresh start | `make start-force` wipes the volumes and reloads the dump + analytics from scratch. |

## What's next

DHIS2 is running, but it cannot talk to CHAP yet. Next you will run **chap-core** and connect
the two through a DHIS2 Route.
