# Run chap-core

With DHIS2 running, you now add **chap-core** - the modelling engine - and connect the two so
DHIS2 can send data to CHAP and read predictions back.

You stay in the same `docker-dhis2-core` repository. One command starts chap-core alongside
DHIS2 using **released CHAP images** and wires up the DHIS2 -> CHAP connection for you. (If you
want to build chap-core from source instead - for model development - see
[Run chap-core from source](chap-core-from-source.md).)

!!! note "Before you start"
    You have completed [Start DHIS2 with Docker](start-dhis2.md). `make start-chap` runs the
    *same* DHIS2 stack plus chap-core, so if `make start` is still running, stop it with
    `Ctrl+C` first - the next command replaces it.

## Step 1 - Start DHIS2 + chap-core

From the `docker-dhis2-core` folder:

```bash
make start-chap
```

Like `make start`, this runs in the **foreground** (`Ctrl+C` to stop). On top of DHIS2 it adds:

- **chap** - the chap-core REST API.
- **chap-worker** - a background worker that runs the models.
- **chap-redis** / **chap-postgres** - the broker and database CHAP needs.
- **chap-ewars** - a chapkit model (EWARS) that registers itself with chap-core.
- **chap-route-init** - a one-shot that creates the DHIS2 Route to CHAP, then exits.

The first run pulls the CHAP images, so give it a few minutes.

!!! info "How DHIS2 reaches CHAP"
    chap-core has **no login of its own**, so it is never exposed publicly. DHIS2 reaches it
    over the internal Docker network through a DHIS2 **Route** with code `chap` that points at
    `http://chap:8000`. The `chap-route-init` one-shot sets this up for you - it repoints the
    route that the demo database ships (which points at a remote server) at your local CHAP.

## Step 2 - Watch it come up

```bash
make ps
```

Wait for `chap` to report **healthy** and `chap-route-init` to have **Exited (0)** (it
finished its job):

```text
docker-dhis2-core-chap-1             Up (healthy)
docker-dhis2-core-chap-worker-1      Up (healthy)
docker-dhis2-core-chap-route-init-1  Exited (0)
docker-dhis2-core-chap-ewars-1       Up (healthy)
```

## Step 3 - Verify the connection

The repository has a shortcut that shows the route and probes it end to end:

```bash
make route
```

You should see the route pointing at `http://chap:8000/**` and a healthy probe. You can also
check it directly - this is DHIS2 proxying a health check through to CHAP:

```bash
curl -s -u admin:district "http://localhost:8080/api/routes/chap/run/health" | jq
```

```json
{
  "status": "success",
  "message": "healthy"
}
```

That response means the full path works: **your browser -> DHIS2 -> route -> chap-core**.

## Step 4 - Confirm the model registered

The EWARS chapkit model registers itself with chap-core on startup:

```bash
curl -s http://localhost:8000/v2/services | jq -r '.services[].info.display_name'
```

You should see `CHAP-EWARS Model (chapkit)`. You can also open the CHAP API docs at
[http://localhost:8000/docs](http://localhost:8000/docs).

!!! note "Assignment: chap-core connected to DHIS2"
    - [ ] `make ps` shows `chap` **healthy** and `chap-route-init` **Exited (0)**.
    - [ ] `make route` (or the proxy `curl`) returns `healthy`.
    - [ ] `/v2/services` lists `CHAP-EWARS Model (chapkit)`.

    When all three pass, DHIS2 and CHAP are wired together and you are ready to use the
    Modelling App.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| First start is slow | The CHAP images are downloading. Watch progress with `make logs`. |
| Proxy is not healthy | Check `make ps` - `chap` must be **healthy**. If `chap-route-init` errored, re-run `make start-chap`; it is safe to repeat. |
| Port `8000` already in use | Another process holds it (a previous from-source CHAP, or your own server). Stop it, or change the port: `CHAP_PORT=8001 make start-chap`. |
| Want a completely fresh start | `make start-chap-force` wipes all volumes (DHIS2 **and** chap) and rebuilds from scratch. |

## What's next

DHIS2 and CHAP are connected. Next you will install the DHIS2 apps - the **Climate App** and
the **Modelling App** (which uses this CHAP connection) - and run your first backtest.
