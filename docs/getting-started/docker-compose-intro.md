# Docker Compose basics: services that work together

In [Docker basics](docker-intro.md) you ran **one** container with `docker run`. Real systems are
rarely one container: this workshop runs DHIS2, CHAP, a worker, and two databases - five-plus
containers that must **start together** and **talk to each other**. Doing that by hand means
creating a network, starting each container in the right order, and passing the right flags every
time.

**Docker Compose** replaces all of that with one file. You describe the services once in a
**`compose.yml`**, and `docker compose up` starts the whole set on a shared network where each
service can reach the others **by name**.

!!! note "Before you start"
    You have the `hello-docker` project from [Docker basics](docker-intro.md) (the `Dockerfile`
    and the FastAPI app from step 2) - this page continues it by adding a second service.

## Step 1 - Give the app a second service to talk to

A single web app is a dull Compose demo, so let's make it actually *use* a second service. Add
[Redis](https://redis.io/) - a tiny in-memory data store - and have the app count how many times
it has been visited:

```bash
uv add redis
```

Replace **`main.py`** with a version that talks to Redis:

```python
import redis
from fastapi import FastAPI

app = FastAPI()

# "redis" is the service name from compose.yml below - Compose resolves it to
# the redis container on the shared network. No host or port to hard-code.
cache = redis.Redis(host="redis", port=6379, decode_responses=True)


@app.get("/")
def read_root():
    hits = cache.incr("hits")          # increment a counter stored in Redis
    return {"message": "Hello from Docker!", "hits": hits}
```

The key line is `host="redis"`. That is **not** a hostname you configured anywhere - it is the
**service name** you are about to define in `compose.yml`, and Compose makes it resolve to the
right container.

## Step 2 - Describe both services in `compose.yml`

Create a **`compose.yml`** next to your `Dockerfile`:

```yaml
services:
  web:
    build: .              # build the image from the Dockerfile in this folder
    ports:
      - "8001:8000"       # publish to the host, same as the -p flag
    depends_on:
      - redis             # start redis before web

  redis:
    image: redis:8        # pulled ready-made; no build needed
    # No ports: - redis is only used internally by web, so it needs no host port.
```

Two services. `web` is built from your Dockerfile; `redis` is a published image pulled as-is.
Note that `redis` has **no `ports:`** - it does not need to be reachable from your laptop, only
from `web`, and services on the same Compose network reach each other directly.

## Step 3 - Run the whole thing

```bash
docker compose up -d --build   # build web, pull redis, start both in the background
docker compose ps              # both services, Up
```

```text
NAME                    SERVICE   STATUS
hello-docker-redis-1    redis     Up
hello-docker-web-1      web       Up
```

Call the app a few times and watch the counter climb - proof that `web` is reaching `redis` on
every request:

```bash
curl http://localhost:8001/    # {"message":"Hello from Docker!","hits":1}
curl http://localhost:8001/    # {"message":"Hello from Docker!","hits":2}
curl http://localhost:8001/    # {"message":"Hello from Docker!","hits":3}
```

Useful while it runs, then tidy up:

```bash
docker compose logs -f         # follow logs from both services (Ctrl+C stops following)
docker compose down            # stop and remove both containers and the network
```

(Add `-v` to `down` to also delete data volumes - here there are none, but the workshop uses it
for a full reset.)

## Why this is the point of Compose

Look at what you did **not** have to do: create a network, start Redis, figure out its address,
then start the web app pointing at it - in order, with the right flags. You wrote a few lines of
`compose.yml` and ran one command, and the two containers came up together and found each other
**by service name**.

That is exactly how the workshop stacks work:

- DHIS2 reaches CHAP at **`http://chap:8000`** because `chap` is a service name on the shared
  Compose network - the same mechanism as `host="redis"` here.
- Internal-only services (the databases, the worker, Redis) publish **no host ports**, just like
  `redis` above.
- One `compose.yml` can **`include`** another to layer services on - that is the overlay idea
  behind `compose.chap.yml` and `compose.chapkit.yml` in [step 4](add-chap-core.md).
- Containers are named `<project>-<service>-<number>`, so the workshop's show up as
  `docker-dhis2-core-chap-1`, `docker-dhis2-core-dhis2-web-1`, and so on - the same pattern as
  your `hello-docker-web-1`.

Every `docker compose` command in the rest of the guides is the same handful you just used here,
only with more services in the file.

!!! note "Assignment: two services with Compose"
    - [ ] Add `redis` to the project and the Redis-backed `main.py`.
    - [ ] Write `compose.yml` with the `web` and `redis` services.
    - [ ] `docker compose up -d --build`, then `curl http://localhost:8001/` a few times and watch
      `hits` increment.
    - [ ] `docker compose down` to clean up.

## Next step

You have built a container and run a multi-service stack with Compose - the two ideas the whole
workshop is built on. Continue to [step 3: start DHIS2](start-dhis2.md), where a single
`docker compose` command brings up a real stack of containers at once.
