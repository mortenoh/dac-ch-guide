# Inspecting logs

This is a reference page. Use it whenever a job is slow or fails; it is not a required step
in the workshop.

When an evaluation or prediction fails - or just takes longer than you expect - the logs tell
you why. There are two levels:

- the **per-job log** - the model's own account of what it did;
- the **container logs** - the services around it (worker, API, DHIS2).

Start with the per-job log; drop to the container logs when you need more.

```bash
export CHAP="http://localhost:8080/api/routes/chap/run/v1"
export AUTH="admin:district"
```

## The per-job log (start here)

Every backtest and prediction runs as a **job**. Read that job's log straight from chap. You
get the job id from the `POST` that created the run, or grab the most recent one:

```bash
JOB_ID=$(curl -fsS -u "$AUTH" "$CHAP/jobs" | jq -r 'sort_by(.start_time) | last | .id')

# the endpoint returns the log as a JSON string; jq -r renders the real newlines
curl -fsS -u "$AUTH" "$CHAP/jobs/$JOB_ID/logs" | jq -r .
```

```text
2026-06-09 14:55:48  Starting backtest for model 'chapkit-ewars-model' on dataset ID 8
2026-06-09 14:55:49  Validating dataset with 18 locations
2026-06-09 14:55:49  Running 7 evaluation splits with prediction length 3
2026-06-09 14:57:23  Backtest completed successfully. Results saved with ID 6
```

This is the model narrating its own run - on a failure it shows the step it stopped at. The
job's **status** is a separate one-liner:

```bash
curl -fsS -u "$AUTH" "$CHAP/jobs/$JOB_ID"     # "SUCCESS", "STARTED", or a failure status
```

!!! tip "From the Modelling App"
    The app's **Jobs** page lists the same jobs with their status, so you can spot a failed run
    there first, then pull its log with the command above.

## The container logs

A run spans several containers. When the job log is not enough - for example the worker died
before it could log - look at the containers with `docker compose`. From the
**docker-dhis2-core** folder (the bundled stack), use the `compose.chapkit.yml` umbrella you
started in [Connect CHAP](../getting-started/add-chap-core.md) - it sees every service,
including the `chap-ewars` model:

```bash
docker compose -f compose.chapkit.yml logs -f chap-ewars    # the EWARS model itself (INLA/R) — model errors and R tracebacks land here
docker compose -f compose.chapkit.yml logs -f chap-worker   # orchestrates the run: queues the job, calls the model's train/predict
docker compose -f compose.chapkit.yml logs -f chap          # the chap-core API
docker compose -f compose.chapkit.yml logs -f dhis2-web     # DHIS2 itself
```

- **chap-ewars** is where the model actually runs. The chapkit EWARS model executes INLA/R inside
  its own container, so a model that errors or produces bad output shows its **R traceback here** -
  look here first for model-level failures.
- **chap-worker** *orchestrates* the run (a Celery task that picks up the job, calls the model's
  `$train` / `$predict` over HTTP, and assembles the result). A model failure surfaces here only
  as a failed call or a failed job status; the detail is in `chap-ewars`. Watch it to follow a
  run's progress or to catch queue/orchestration problems.
- `--tail=50` limits the output, `-f` follows it live; drop both for the full history.
- Tail both together: `docker compose -f compose.chapkit.yml logs -f chap-ewars chap-worker`.
- `chap-ewars` is defined in the `compose.ewars.yml` overlay, so it only shows up under the
  `compose.chapkit.yml` umbrella - `-f compose.chap.yml` (chap-core only) does not know it.

!!! note "Running chap from source?"
    The [from-source stack](../getting-started/chap-core-from-source.md) uses different file
    flags and service names. From the **chap-core** folder the model service is `ewars` and the
    worker is just `worker`:

    ```bash
    docker compose -f compose.yml -f compose.chapkit.yml logs -f ewars worker
    ```

## A debugging recipe

1. Find the failing run's **job id** (the create response, or `…/jobs`).
2. `curl …/jobs/$JOB_ID` - is the status a failure rather than `SUCCESS`?
3. `curl …/jobs/$JOB_ID/logs` - what did the model say, and at which step did it stop?
4. Still unclear - `docker compose -f compose.chapkit.yml logs chap-ewars` for the model's own
   traceback (INLA/R), and `chap-worker` for the orchestration around it.

!!! note "Assignment: read the logs"
    - [ ] Read the per-job log of your last evaluation or prediction.
    - [ ] Tail the model and the worker while a run is in progress and watch it execute - the
      model runs in **chap-ewars**, the worker orchestrates. **Bundled**:
      `docker compose -f compose.chapkit.yml logs -f chap-ewars chap-worker`; **source**:
      `docker compose -f compose.yml -f compose.chapkit.yml logs -f ewars worker`.

## What's next

Logs tell you *what* happened; the next operational topics - inspecting the database, and
upgrading or restoring chap - let you dig into the data behind a run.
