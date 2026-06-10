# Docker basics: your first container

This is step 2 of the workshop. The workshop runs **everything** in Docker - DHIS2, CHAP, the
databases, and (on the modeller track) your own model - so before you orchestrate those big
stacks, it helps to build and run **one tiny container yourself** so the moving parts are
familiar.

What you build here - a minimal Python web service in a container - is, in miniature, exactly
what a
chapkit model service is ([step 8: build a model](../modelling/chapkit-scaffold.md)): a small web
app that runs in a container and answers HTTP requests. The next page,
[Docker Compose basics](docker-compose-intro.md), grows it into several containers working
together.

!!! note "Before you start"
    You need **Docker** and [**uv**](https://docs.astral.sh/uv/) (the Python project tool), both
    installed in [step 1: prepare your machine](prerequisites.md). Check them:

    ```bash
    docker --version
    uv --version
    ```

## Step 1 - Create a project with uv

`uv init` scaffolds a new Python project in one command:

```bash
uv init hello-docker
cd hello-docker
```

It writes a small, complete project:

```text
hello-docker/
├── main.py              # a placeholder script (you replace it below)
├── pyproject.toml       # project metadata and dependencies
├── README.md
├── .python-version      # the Python version uv will use (3.13)
└── .gitignore
```

## Step 2 - Add FastAPI

[FastAPI](https://fastapi.tiangolo.com/) is a small framework for building web APIs.
Add it with the **`standard`** extras, which pull in the `uvicorn` web server and the `fastapi`
command-line tool you will use to run the app:

```bash
uv add "fastapi[standard]"
```

This records the dependency in `pyproject.toml` and pins the exact versions in a new
**`uv.lock`** file - the lock file is what makes the Docker build reproducible.

## Step 3 - Write the hello-world app

Replace the contents of **`main.py`** with a single endpoint:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello from Docker!"}
```

`app` is the application; `@app.get("/")` says "when someone requests `/`, run this function and
return its result as JSON." Try it on your own machine first:

```bash
uv run fastapi dev
```

Open [http://localhost:8000](http://localhost:8000) - you should see the JSON message. Press
`Ctrl+C` to stop. (If port `8000` is busy - for example CHAP is running - add `--port 8001`.)

## Step 4 - A minimal Dockerfile

A **Dockerfile** is the recipe for building an image: the base system, your code, its
dependencies, and the command to start. Create a file named **`Dockerfile`** (no extension):

```dockerfile
# Start from a small official Python image.
FROM python:3.13-slim

# Copy the uv binary in from its official image - no pip install needed.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Everything below happens inside /app in the image.
WORKDIR /app

# Copy your project in, then install exactly what uv.lock pins (skip dev extras).
COPY . .
RUN uv sync --frozen --no-dev

# The app listens on 8000; document that for whoever runs the image.
EXPOSE 8000

# Start the API, bound to 0.0.0.0 so it is reachable from outside the container.
CMD ["uv", "run", "fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
```

Because `COPY . .` copies the **whole folder**, add a **`.dockerignore`** next to the
`Dockerfile` so the local `.venv` (created by `uv add`, and full of your machine's binaries) is
not copied into the build - the image rebuilds it from `uv.lock` anyway:

```text
.venv
__pycache__
.git
```

That keeps the build context small and avoids carrying host-platform artifacts into a Linux image.

!!! tip "Why `--host 0.0.0.0`"
    Inside a container, `localhost` means *the container itself*. Binding to `0.0.0.0` makes the
    app listen on all interfaces, so the port you publish with `-p` (next step) actually reaches
    it. A service bound to `127.0.0.1` inside a container is unreachable from your machine.

## Step 5 - Build and run

**Build** the image from the Dockerfile (the `.` is "use this folder"; `-t` names the image):

```bash
docker build -t hello-docker .
```

**Run** a container from it:

```bash
docker run --rm -p 8001:8000 hello-docker
```

- `-p 8001:8000` maps **host port 8001 -> container port 8000**. The app listens on `8000`
  *inside* the container; you reach it at `8001` on your machine. Using `8001` here keeps it clear
  of CHAP (which uses `8000`).
- `--rm` deletes the container when you stop it, so nothing is left behind.

In another terminal, call it:

```bash
curl http://localhost:8001/
# {"message":"Hello from Docker!"}
```

Press `Ctrl+C` in the first terminal to stop the container.

!!! note "Assignment: a container you built"
    - [ ] `uv init` a project, `uv add "fastapi[standard]"`, and write the hello-world `main.py`.
    - [ ] Write the `Dockerfile` and `docker build -t hello-docker .` succeeds.
    - [ ] `docker run --rm -p 8001:8000 hello-docker`, then `curl http://localhost:8001/` returns
      the JSON message.

## What you just learned

- An **image** is a built, shippable bundle of code + dependencies; a **container** is a running
  instance of one. The DHIS2 and CHAP services are images someone else built and published.
- A **Dockerfile** builds an image from your code - which is exactly how you package a model in
  [step 8](../modelling/chapkit-scaffold.md) (its `Dockerfile` starts `FROM` a chapkit base image
  instead of plain Python).
- **Port publishing** (`-p host:container`) is how the guides expose DHIS2 on `8080` and CHAP on
  `8000`.

So far that is a single container, started with a single `docker run`. Real systems - including
this workshop - run **several** containers that must start together and talk to each other. That
is what Docker Compose is for.

## Next step

Continue to [Docker Compose basics](docker-compose-intro.md) to run several containers together
with one command - then on to [step 3: start DHIS2](start-dhis2.md).
