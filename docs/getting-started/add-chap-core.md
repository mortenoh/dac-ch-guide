# Quick setup (bundled)

This is the **quick path** for step 4: use released images bundled with the DHIS2 stack. For
the alternative and its trade-offs, see [Choose how to run CHAP](chap-setup.md).

With DHIS2 running, you now add **chap-core** - the modelling engine - and connect the two so
DHIS2 can send data to CHAP and read predictions back.

You stay in the same `docker-dhis2-core` repository. It is built as a set of **Compose
overlays** that stack on top of each other, so you bring up exactly the layer you need:

| Compose file | Brings up | Use it for |
|---|---|---|
| `compose.yml` | DHIS2 only | [step 3](start-dhis2.md) |
| `compose.chap.yml` | DHIS2 **+ chap-core** (its built-in models) | chap-core without any chapkit model |
| `compose.chapkit.yml` | DHIS2 + chap-core **+ chapkit models (EWARS)** | this workshop |

Each file `include`s the one above it, so a single `-f` flag pulls in the whole tower
underneath. This mirrors chap-core's own layout, where model services are **opt-in overlays**
rather than part of the base engine. The workshop uses the *CHAP-EWARS Model (chapkit)*, which
is one of those model services - so you want the **`compose.chapkit.yml`** umbrella, which adds
it on top of chap-core.

!!! note "Before you start"
    You have completed [Start DHIS2](start-dhis2.md). `compose.chapkit.yml` includes the same
    DHIS2 stack and layers chap on top, so running it just adds CHAP to what is already up - you
    do not need to stop DHIS2 first.

## Step 1 - Start DHIS2 + chap-core + the EWARS model

From the `docker-dhis2-core` folder, bring up the umbrella overlay:

```bash
docker compose -f compose.chapkit.yml up -d
```

On top of DHIS2 this adds:

- **chap** - the chap-core REST API.
- **chap-worker** - a background worker that runs the models.
- **chap-redis** / **chap-postgres** - the broker and database CHAP needs.
- **chap-route-init** - a one-shot that creates the DHIS2 Route to CHAP, then exits.
- **chap-ewars** - the EWARS chapkit model, added by the `compose.ewars.yml` overlay that the
  umbrella pulls in. It registers itself with chap-core on startup.

The first run pulls the CHAP images, so give it a few minutes. Follow progress with
`docker compose -f compose.chapkit.yml logs -f`.

!!! tip "chap-core without the model"
    Want just chap-core and its built-in models, without the EWARS chapkit service? Use
    `docker compose -f compose.chap.yml up -d` - the layer below the umbrella. The workshop
    needs the EWARS model, so stick with `compose.chapkit.yml` here.

!!! info "How DHIS2 reaches CHAP"
    chap-core has **no login of its own**, so it is never exposed publicly. DHIS2 reaches it
    over the internal Docker network through a DHIS2 **Route** with code `chap` that points at
    `http://chap:8000`. The `chap-route-init` one-shot sets this up for you - it repoints the
    route that the demo database ships (which points at a remote server) at your local CHAP.

## Step 2 - Watch it come up

```bash
docker compose -f compose.chapkit.yml ps -a
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
    - [ ] `docker compose -f compose.chapkit.yml ps -a` shows `chap` **healthy** and
      `chap-route-init` **Exited (0)**.
    - [ ] The proxy `curl` (`…/api/routes/chap/run/health`) returns `healthy`.
    - [ ] `/v2/services` lists `CHAP-EWARS Model (chapkit)`.

    When all three pass, DHIS2 and CHAP are wired together and you are ready to use the
    Modelling App.

!!! tip "`make` shortcuts"
    The repository wraps these overlays in Makefile targets: **`make start-chap`** is the
    `docker compose -f compose.chapkit.yml up` used here (DHIS2 + chap-core + the EWARS model),
    while `make start` brings up DHIS2 on its own, and `make ps` / `make logs` / `make clean`
    manage the running stack. The guides spell out the `docker compose` commands so you can see
    what each target runs.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| First start is slow | The CHAP images are downloading. Watch progress with `docker compose -f compose.chapkit.yml logs -f`. |
| Proxy is not healthy | Check `docker compose -f compose.chapkit.yml ps -a` - `chap` must be **healthy**. If `chap-route-init` errored, re-run `docker compose -f compose.chapkit.yml up -d`; it is safe to repeat. |
| `/v2/services` is empty (no EWARS model) | You likely started `compose.chap.yml` (chap-core only) instead of the `compose.chapkit.yml` umbrella that adds the EWARS model. Bring up the umbrella: `docker compose -f compose.chapkit.yml up -d`. |
| Port `8000` already in use | Another process holds it (a previous from-source CHAP, or your own server). Stop it, or change the port: `CHAP_PORT=8001 docker compose -f compose.chapkit.yml up -d`. |
| Want a completely fresh start | `docker compose -f compose.chapkit.yml down -v` wipes all volumes (DHIS2 **and** chap); start again with `docker compose -f compose.chapkit.yml up -d`. |

## Next step

Continue to [step 5: install the DHIS2 apps](install-apps.md).
