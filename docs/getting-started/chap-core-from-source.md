# Development setup (source)

This is the **development path** for step 3: build CHAP from a local clone so you can change
chap-core or models. For the quicker alternative and its trade-offs, see
[Choose how to run CHAP](chap-setup.md).

Here you clone the chap-core repository and build it with Docker Compose, layering in the
**chapkit** models overlay. (You still run it in containers - you are building the image from
the cloned code, not running Python by hand.) CHAP then runs as its own Compose project (not
on DHIS2's network), so DHIS2 reaches it on the host - and DHIS2's `chap-route-init` already
points the route there, so the two connect with no extra configuration.

!!! warning "Do not run both CHAP setups at once"
    The bundled CHAP (`compose.chap.yml`) and this locally built CHAP both use port `8000`. Run
    only one. If the bundled stack is up, drop CHAP and keep DHIS2 with
    `docker compose up -d --remove-orphans` (in `docker-dhis2-core`) before bringing up the
    locally built CHAP here.

!!! note "Before you start"
    DHIS2 is running on its own - `docker compose up -d` in `docker-dhis2-core` (the DHIS2-only
    stack, **not** the chap overlay) - and you can log in with `admin` / `district`.

## Step 1 - Get chap-core

In a new terminal, clone chap-core next to your DHIS2 folder:

```bash
git clone https://github.com/dhis2-chap/chap-core
cd chap-core
cp .env.example .env
```

The defaults in `.env` are fine for local use - you do not need to edit anything.

## Step 2 - Start chap-core with the chapkit models

```bash
docker compose -f compose.yml -f compose.chapkit.yml up -d --build
```

What each part means:

- `compose.yml` - chap-core itself: the API, a background **worker** that runs models, a
  Redis broker, and a Postgres database.
- `compose.chapkit.yml` - an umbrella overlay that pulls in the **chapkit-based model
  services**. Today that is just **EWARS**; more chapkit models get added here over time. Each
  one registers itself with chap-core on startup.
- `--build` builds chap-core from the source in this folder. The **first** build takes a
  while; later starts are fast.

!!! tip "Apple Silicon (M1/M2/M3) Macs"
    The CHAP images are built for `amd64`, so on an Apple-Silicon Mac Docker runs them under
    emulation. You will see a `platform does not match` warning - it is harmless, things just
    run a little slower.

Handy commands while developing (from the chap-core folder). The
`-f compose.yml -f compose.chapkit.yml` pair selects the same stack each time:

```bash
# rebuild and restart after editing chap-core source (keeps data)
docker compose -f compose.yml -f compose.chapkit.yml up -d --build

# print the chap_core version running inside the container
docker compose -f compose.yml -f compose.chapkit.yml exec chap \
  python -c 'import chap_core; print(chap_core.__version__)'

# full clean rebuild, WIPES the chap database
docker compose -f compose.yml -f compose.chapkit.yml down -v
docker compose -f compose.yml -f compose.chapkit.yml build --no-cache
docker compose -f compose.yml -f compose.chapkit.yml up -d
```

## Step 3 - Verify chap-core is up

chap-core publishes its API on `http://localhost:8000`:

```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/v2/services | jq -r '.services[].info.display_name'
```

The health check should return `healthy`, and the services list should include
`CHAP-EWARS Model (chapkit)`. The interactive API docs are at
[http://localhost:8000/docs](http://localhost:8000/docs).

## Step 4 - The DHIS2 route is already wired

Your locally built CHAP runs on your host, not on DHIS2's network, so DHIS2 reaches it at
`http://host.docker.internal:8000` - the special hostname a container uses to reach a service
on the host. **DHIS2 already pointed the `chap` route there for you** - its `chap-route-init`
one-shot (which runs with the DHIS2-only stack) repoints the route the demo database ships at
`host.docker.internal:8000`, so there is nothing to configure here. Confirm it:

```bash
curl -s -u admin:district \
  "http://localhost:8080/api/routes.json?filter=code:eq:chap&fields=code,url" | jq -c '.routes[0]'
```

```json
{"code":"chap","url":"http://host.docker.internal:8000/**"}
```

!!! tip "Running CHAP on a different port?"
    The default target is port `8000`. If your locally built CHAP uses another port, set it
    before starting DHIS2:
    `CHAP_ROUTE_URL=http://host.docker.internal:8001/** docker compose up -d` (in
    `docker-dhis2-core`). Or repoint the existing route by hand with a `PUT` to
    `…/api/routes/<id>` carrying `{"name":"chap","code":"chap","url":"<your-url>/**"}` (see the
    DHIS2 [Route API](https://docs.dhis2.org/en/develop/using-the-api/dhis-core-version-242/route.html)).

## Step 5 - Test the connection end to end

```bash
curl -s -u admin:district "http://localhost:8080/api/routes/chap/run/health" | jq
```

A `healthy` response means the full path works: **your browser -> DHIS2 -> route -> the
chap-core you built**.

!!! note "Assignment: your built chap-core connected"
    - [ ] `curl http://localhost:8000/health` returns `healthy`.
    - [ ] `/v2/services` lists `CHAP-EWARS Model (chapkit)`.
    - [ ] The proxy check `…/api/routes/chap/run/health` returns `healthy`.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Proxy returns a connection error | chap-core is not running, or is on a different port. Check `docker compose -f compose.yml -f compose.chapkit.yml ps` and `curl http://localhost:8000/health`. |
| Proxy points at `http://chap:8000` | The route was left targeting the bundled service by a previous bundled run (`compose.chap.yml`). Re-run `docker compose up -d` (DHIS2 only, in `docker-dhis2-core`) to repoint it back at `host.docker.internal:8000`. |
| Port `8000` already in use | The bundled CHAP (`compose.chap.yml`) is still running. Stop it first - see the warning at the top. |
| `platform does not match` warning | Harmless emulation notice on Apple-Silicon Macs (see Step 2). |

## Next step

Continue to [step 4: install the DHIS2 apps](install-apps.md).
