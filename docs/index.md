# Overview & Setup

Welcome to the hands-on guides for the **DHIS2 Annual Conference (DAC) climate track**.

These guides take you from an empty machine to a working **DHIS2 + CHAP** setup that you
can model with. They are built to be followed at your own pace during the session - read a
step, do it, confirm it worked, move on.

## What we are building

By the end of the getting-started guides you will have three pieces running locally and
talking to each other:

| Piece | What it is | How you reach it |
|-------|------------|------------------|
| **DHIS2** | The health information platform you already know, pre-loaded with a climate demo database. | Browser at `http://localhost:8080` |
| **CHAP (chap-core)** | The modelling engine that trains models and produces predictions. | Through DHIS2 (it has no login of its own) |
| **Modelling App** | The DHIS2 app where you run backtests and predictions against CHAP. | Inside DHIS2 |

DHIS2 never calls CHAP directly from your browser. Instead it proxies through a DHIS2
**Route** - a small piece of config inside DHIS2 that forwards requests to CHAP. Setting up
that route is one of the steps you will do yourself.

```mermaid
flowchart LR
    Browser["Your browser"] --> DHIS2["DHIS2 (:8080)"]
    DHIS2 -- "route: chap" --> CHAP["chap-core (:8000)"]
    CHAP --> Worker["worker + models"]
```

## How these guides work

Every guide follows the same rhythm:

1. **Read the step** - a short explanation of what you are about to do and why.
2. **Do the assignment** - the highlighted boxes are the parts you do yourself.
3. **Confirm it worked** - check the result before moving on.

!!! note "Assignment"
    Assignment boxes look like this. When you see one, pause and complete it before
    continuing - the later guides build on each step working.

We run everything with **Docker**, so you do not install DHIS2, databases, or Python
toolchains by hand. You only need a few base tools, below.

## Prerequisites

You need these installed before the first guide. If you have never used Docker, this is the
part to do now - the rest of the guides assume these commands work.

| Tool | Why | Check it |
|------|-----|----------|
| **Docker** | Runs DHIS2 and CHAP as containers. | `docker --version` |
| **Docker Compose** v2.20+ | Orchestrates the multi-container stacks. The CHAP overlays use the `include` directive, which older `docker-compose` does not support. | `docker compose version` |
| **git** | To clone the setup repositories. | `git --version` |
| **jq** | To read JSON from the DHIS2 and CHAP APIs in the `curl` examples. | `jq --version` |

### Installing the tools

=== "macOS"
    Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
    (includes Docker Compose). `git` comes with the Xcode command-line tools, and `jq` is
    easiest via [Homebrew](https://brew.sh):

    ```bash
    xcode-select --install
    brew install jq
    ```

=== "Windows"
    Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
    with the WSL 2 backend. Run the guide commands from a **WSL 2 (Ubuntu)** terminal, and
    install the rest there:

    ```bash
    sudo apt install git jq
    ```

=== "Linux"
    Install [Docker Engine](https://docs.docker.com/engine/install/) and the
    [Compose plugin](https://docs.docker.com/compose/install/linux/). The rest come from your
    package manager:

    ```bash
    sudo apt install git jq
    ```

!!! tip "Can't install jq?"
    `jq` only makes the JSON output easier to read. If you can't install it, pipe to Python
    instead - it ships with most systems and pretty-prints JSON:

    ```bash
    curl -s http://localhost:8000/health | python3 -m json.tool
    ```

    For a quick check you can also just `grep` for a field, e.g. `... | grep status`. The
    guides use `jq`, but any of these work.

!!! warning "Windows users: work inside WSL 2"
    Every command in these guides (`docker`, `curl`, `jq`, ...) assumes a Unix-style shell.
    On Windows, run them all from your **WSL 2 (Ubuntu)** terminal - not PowerShell or the
    Command Prompt. Clone the repositories *inside* WSL too (your Linux home, e.g.
    `~/dac`), not under `/mnt/c`, so Docker file sharing stays fast.

!!! tip "Give Docker enough memory"
    DHIS2 plus CHAP needs a few GB of RAM. In Docker Desktop, raise the memory limit under
    **Settings -> Resources** to at least **6-8 GB**. If a container is killed mid-startup,
    this is usually why.

## Confirm your setup

!!! note "Assignment: verify the base tools"
    Run each command and confirm you get a version back (exact numbers may differ):

    ```bash
    docker --version          # Docker 24+ recommended
    docker compose version    # v2.20 or newer
    git --version
    jq --version
    docker run --rm hello-world   # confirms Docker can actually run a container
    ```

    - [ ] All four tools report a version.
    - [ ] `docker run --rm hello-world` prints "Hello from Docker!".
    - [ ] Docker has at least 6 GB of memory available.
    - [ ] Ports `8080` (DHIS2) and `8000` (CHAP) are free on your machine.

    If anything fails here, flag it now - the next guide assumes all of this works.

## What's next

Next you will start DHIS2 with Docker and log in to the climate demo database, then bring up
chap-core and connect the two. More guides are added here as the climate track takes shape.
