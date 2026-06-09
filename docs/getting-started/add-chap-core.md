# Run chap-core

!!! abstract "Two ways to run chap-core - pick one"
    This page is the **quick way**: pre-built images, bundled with the DHIS2 stack and wired up
    for you. To build chap-core yourself - the path for **model development** - use
    [Build chap-core](chap-core-from-source.md) instead. You only need one; either way you end
    up with DHIS2 + chap-core connected.

With DHIS2 running, you now add **chap-core** - the modelling engine - and connect the two so
DHIS2 can send data to CHAP and read predictions back.

You stay in the same `docker-dhis2-core` repository. A second compose file, `compose.chap.yml`,
adds chap-core on top of the DHIS2 stack using **released CHAP images** and wires up the
DHIS2 -> CHAP connection for you.

!!! note "Before you start"
    You have completed [Run DHIS2](start-dhis2.md). `compose.chap.yml` includes the same DHIS2
    stack and adds chap to it, so running it just layers CHAP onto what is already up - you do
    not need to stop DHIS2 first.

## Step 1 - Start DHIS2 + chap-core

From the `docker-dhis2-core` folder:

```bash
docker compose -f compose.chap.yml up -d
```

On top of DHIS2 this adds:

- **chap** - the chap-core REST API.
- **chap-worker** - a background worker that runs the models.
- **chap-redis** / **chap-postgres** - the broker and database CHAP needs.
- **chap-ewars** - a chapkit model (EWARS) that registers itself with chap-core.
- **chap-route-init** - a one-shot that creates the DHIS2 Route to CHAP, then exits.

The first run pulls the CHAP images, so give it a few minutes. Follow progress with
`docker compose -f compose.chap.yml logs -f`.

!!! info "How DHIS2 reaches CHAP"
    chap-core has **no login of its own**, so it is never exposed publicly. DHIS2 reaches it
    over the internal Docker network through a DHIS2 **Route** with code `chap` that points at
    `http://chap:8000`. The `chap-route-init` one-shot sets this up for you - it repoints the
    route that the demo database ships (which points at a remote server) at your local CHAP.

## Step 2 - Watch it come up

```bash
docker compose -f compose.chap.yml ps -a
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

First, confirm the route now points at the bundled CHAP service:

```bash
curl -s -u admin:district \
  "http://localhost:8080/api/routes.json?filter=code:eq:chap&fields=code,url" | jq -c '.routes[0]'
```

```json
{"code":"chap","url":"http://chap:8000/**"}
```

Then have DHIS2 proxy a health check through to CHAP:

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
    - [ ] `docker compose -f compose.chap.yml ps -a` shows `chap` **healthy** and
      `chap-route-init` **Exited (0)**.
    - [ ] The proxy `curl` (`…/api/routes/chap/run/health`) returns `healthy`.
    - [ ] `/v2/services` lists `CHAP-EWARS Model (chapkit)`.

    When all three pass, DHIS2 and CHAP are wired together and you are ready to use the
    Modelling App.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| First start is slow | The CHAP images are downloading. Watch progress with `docker compose -f compose.chap.yml logs -f`. |
| Proxy is not healthy | Check `docker compose -f compose.chap.yml ps -a` - `chap` must be **healthy**. If `chap-route-init` errored, re-run `docker compose -f compose.chap.yml up -d`; it is safe to repeat. |
| Port `8000` already in use | Another process holds it (a previous from-source CHAP, or your own server). Stop it, or change the port: `CHAP_PORT=8001 docker compose -f compose.chap.yml up -d`. |
| Want a completely fresh start | `docker compose -f compose.chap.yml down -v` wipes all volumes (DHIS2 **and** chap); start again with `docker compose -f compose.chap.yml up -d`. |

## What's next

DHIS2 and CHAP are connected. Next you will install the DHIS2 apps - the **Climate App** and
the **Modelling App** (which uses this CHAP connection) - and run your first backtest.
