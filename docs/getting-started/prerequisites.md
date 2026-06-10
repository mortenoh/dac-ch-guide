# Prepare your machine

This is step 1 of the workshop. Install the base tools and verify that your machine can run
the local DHIS2 and CHAP stack.

## What you need

| Tool | Why | Check it |
|------|-----|----------|
| **Docker** | Runs DHIS2 and CHAP as containers. | `docker --version` |
| **Docker Compose** v2.20+ | Orchestrates the stacks. The CHAP overlays use `include`, which older `docker-compose` does not support. | `docker compose version` |
| **git** | Clones the setup repositories. | `git --version` |
| **jq** | Makes the JSON in the API exercises readable. | `jq --version` |

## Install the tools

=== "macOS"
    Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
    (which includes Docker Compose). Install the remaining tools with the Xcode command-line
    tools and [Homebrew](https://brew.sh):

    ```bash
    xcode-select --install
    brew install jq
    ```

=== "Windows"
    Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
    with the WSL 2 backend. In a **WSL 2 (Ubuntu)** terminal, install the remaining tools:

    ```bash
    sudo apt install git jq
    ```

=== "Linux"
    Install [Docker Engine](https://docs.docker.com/engine/install/) and the
    [Compose plugin](https://docs.docker.com/compose/install/linux/). Then use your package
    manager for the remaining tools:

    ```bash
    sudo apt install git jq
    ```

!!! warning "Windows users: work inside WSL 2"
    Run all guide commands from a **WSL 2 (Ubuntu)** terminal, not PowerShell or Command
    Prompt. Clone repositories inside your Linux home directory, such as `~/dac`, rather than
    under `/mnt/c`, so Docker file sharing stays fast.

!!! tip "Give Docker enough memory"
    DHIS2 plus CHAP needs several GB of RAM. In Docker Desktop, set the memory limit under
    **Settings -> Resources** to at least **6-8 GB**.

!!! tip "If you cannot install jq"
    `jq` only formats and filters JSON. For simple checks, Python can pretty-print a response:

    ```bash
    curl -s http://localhost:8000/health | python3 -m json.tool
    ```

## Verify the setup

!!! note "Assignment: verify the base tools"
    Run each command and confirm it succeeds:

    ```bash
    docker --version
    docker compose version
    git --version
    jq --version
    docker run --rm hello-world
    ```

    Then check memory and that the ports are free:

    ```bash
    # Docker memory (bytes) - want at least ~6 GB, i.e. 6000000000+
    docker info --format '{{.MemTotal}}'

    # Ports 8080 (DHIS2) and 8000 (CHAP) - no output means both are free
    lsof -i :8080 -i :8000        # macOS / Linux / WSL
    # or, if lsof is unavailable:
    ss -tlnp 'sport = :8080 or sport = :8000'
    ```

    - [ ] All four tools report a version.
    - [ ] `docker run --rm hello-world` prints "Hello from Docker!".
    - [ ] `docker info` shows at least ~6 GB of memory (`MemTotal` >= `6000000000`).
    - [ ] Ports `8080` (DHIS2) and `8000` (CHAP) are free (the checks above print nothing).

## Next step

Continue to [step 2: start DHIS2](start-dhis2.md).

!!! tip "New to Docker?"
    The optional [Docker basics primer](docker-intro.md) builds and runs one tiny container from
    scratch - a good 10-minute warm-up before the workshop brings up whole stacks of them.
