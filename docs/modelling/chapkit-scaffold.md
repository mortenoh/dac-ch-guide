# Scaffold and run a chapkit model

This is step 7a of the workshop, and the start of the **modeller** track: building your own
model. CHAP can run models packaged in more than one way. The classic kind is a git repo with
an **`MLproject`** file (the MLflow standard) that declares the model's train/predict entry
points and environment; CHAP clones and runs it directly, seeding it as a model template from
its own `default.yaml` registry. **chapkit** is a different approach: a toolkit that turns your
training and prediction code into a small web service that runs and self-registers with CHAP.
The *CHAP-EWARS Model (chapkit)* you used earlier is built this way, and it is the approach this
guide teaches. Here you scaffold one, make it do something, run it, and test it - all on its
own, before any chap-core wiring (that is [step 7b](chapkit-register.md)).

!!! note "Before you start"
    You need **Docker** (from [step 1](../getting-started/prerequisites.md)) and
    [**uv**](https://docs.astral.sh/uv/) - the Python tool that runs `chapkit`. `uvx` (bundled
    with uv) runs `chapkit` without installing it.

## Step 1 - Scaffold the project

One command generates a complete, runnable model project. We use the **`shell-py`** template -
your model logic lives in plain Python scripts:

```bash
uvx chapkit init my-model --template shell-py
cd my-model
```

It generates:

```text
my-model/
├── main.py                    # the service wrapper - Config + which scripts to run + model metadata
├── scripts/
│   ├── train_model.py         # YOUR training logic
│   └── predict_model.py       # YOUR prediction logic
├── pyproject.toml             # Python dependencies
├── Dockerfile                 # FROM ghcr.io/dhis2-chap/chapkit-py
├── compose.yml                # runs the service on http://localhost:9090
├── README.md
└── .gitignore / .python-version
```

!!! tip "Other templates"
    `shell-py` is the simplest. There are others for different needs - pass `--template`:

    | Template | For |
    |----------|-----|
    | `fn-py` | model logic as Python functions inside `main.py` (no `scripts/`) |
    | `shell-py` | Python scripts (this guide) |
    | `shell-r` | R scripts on a minimal R base |
    | `shell-r-tidyverse` | R scripts with the tidyverse / forecasting stack |
    | `shell-r-inla` | R scripts with INLA (what EWARS uses) |

    The `shell-*` templates run scripts in **any** language - the base image is what changes.
    Those images come from [chapkit-images](https://github.com/dhis2-chap/chapkit-images)
    (`chapkit-py`, `chapkit-r`, `chapkit-r-tidyverse`, `chapkit-r-inla`); to switch, change the
    `FROM` line in the `Dockerfile`.

## Step 2 - Implement train and predict

The two scripts in `scripts/` are where you write real work. They exchange files with chapkit
on fixed paths in a per-run workspace:

- **`train_model.py`** reads `config.yml` (your settings) and the training data (`--data` CSV),
  trains, and writes a **`model.pickle`**.
- **`predict_model.py`** loads `model.pickle`, reads the future data (`--future` CSV), and
  writes a predictions CSV (`--output`) with a **`sample_0`** column (add `sample_1`, `sample_2`,
  … for multiple probabilistic samples).

These exact file names, paths, and config layouts are chapkit's
[shell-runner contract](https://dhis2-chap.github.io/chapkit/guides/shell-runner-contract/).

The scaffold ships a trivial example (it predicts the training mean). Replace the logic with
your model. You usually also edit `main.py` to:

- add fields to the **`Config`** class (your hyperparameters - they arrive in `config.yml`);
- fill in **`MLServiceInfo`** - your name, contact, `period_type` (`monthly`/`weekly`), required
  covariates, and prediction-horizon bounds.

## Step 3 - Run it

The Docker build needs a lock file, so generate it once, then start the service. Run it
**detached** (`-d`) so your terminal stays free for the next steps:

```bash
uv lock                       # writes uv.lock (the build needs it)
docker compose up -d --build  # -d runs the service in the background
```

Check it is alive, and open its interactive API docs:

```bash
curl -s http://localhost:9090/health     # {"status":"healthy",...}
```

```text
http://localhost:9090/docs
```

## Step 4 - Test it with `chapkit test`

Before wiring anything to CHAP, sanity-check the model on its own. chapkit has a **built-in
[tester](https://dhis2-chap.github.io/chapkit/guides/testing-ml-services/)** that generates
synthetic data and drives a full **config → train → predict** cycle against your running
service, checking the endpoints and response shapes:

```bash
uvx chapkit test --verbose
```

```text
Running 1 training job(s)...    [OK] Training ...: Job completed successfully
Running 1 prediction job(s)...  [OK] Prediction ...: verified
Result: ALL TESTS PASSED
```

Green means the service trains and predicts correctly. Turn up the load to exercise it harder:

```bash
uvx chapkit test --configs 2 --trainings 2 --predictions 5 --rows 250 --verbose
```

!!! note "Assignment: a working model service"
    - [ ] Scaffold a `shell-py` model and read `scripts/train_model.py` / `predict_model.py`.
    - [ ] Make **one observable change** to the prediction logic - e.g. in `predict_model.py`
      forecast the target's mean scaled by a constant, or a fixed value - so the output is
      clearly yours, not the untouched example.
    - [ ] In `main.py`, declare at least one covariate in `MLServiceInfo`
      (`required_covariates=["population"]`) - step 7b's evaluation predicts the target from a
      future covariate, so a model with none cannot be backtested.
    - [ ] `uv lock`, then `docker compose up -d --build`; confirm `/health` and open `/docs`.
    - [ ] Run `uvx chapkit test --verbose` and get **ALL TESTS PASSED** - the tester drives a
      full config -> train -> predict cycle, so a pass means your changed predict code ran end
      to end.

!!! tip "Seeing your forecast values"
    `chapkit test` confirms the cycle works but does not print the numbers. To eyeball the
    actual `sample_0` values your change produces, use the interactive **`/docs`**: call the
    train endpoint, then the predict endpoint, and read `sample_0` in the JSON response.

## Advanced - explore the running service

Optional, beyond the assignment. The service is more than two endpoints: it **persists every
run** and exposes a small REST API over the results. `chapkit test` already populated it.

### Where state lives - the SQLite file

chapkit keeps its **configs, jobs, and artifacts** in a single SQLite file at `data/chapkit.db`
inside the container (the default `DATABASE_URL=sqlite+aiosqlite:///data/chapkit.db`). The
scaffold's `compose.yml` puts that `data/` directory in a **named volume**, so the database
survives `docker compose restart` and `up`:

```bash
docker compose exec my-model ls -lh data/chapkit.db
```

That file lives **inside the container's volume**, not on your host. To read it with the CLI
directly, copy it out first:

```bash
docker compose cp my-model:/work/data/chapkit.db ./chapkit.db
uvx chapkit artifact list --database ./chapkit.db
```

Point `DATABASE_URL` at a different file - or at a hosted Postgres - to move that state
elsewhere (for example when deploying next to chap-core).

### Artifacts - every train and predict is saved

Each training run stores a **model artifact**; each prediction stores a **prediction artifact**
linked to the model it came from (a parent -> child lineage). The hierarchy, artifact types, and
retention are covered in chapkit's
[Artifact Storage](https://dhis2-chap.github.io/chapkit/guides/artifact-storage/) guide. List
what `chapkit test` produced against the running service (or from a copied-out db file, as
above):

```bash
uvx chapkit artifact list --url http://localhost:9090
```

Filter by type, and download a run's full **workspace** (its inputs, scripts, logs, and outputs)
as a ZIP:

```bash
uvx chapkit artifact list --url http://localhost:9090 --type ml_training_workspace
uvx chapkit artifact download <artifact-id> --url http://localhost:9090 --extract
```

### The REST API behind it

All of that is plain HTTP - browse it interactively at `/docs`, or curl it. The `$train` and
`$predict` endpoints, the job lifecycle, and the artifact responses are documented in chapkit's
[ML Workflows](https://dhis2-chap.github.io/chapkit/guides/ml-workflows/) guide:

```bash
curl -s http://localhost:9090/api/v1/configs   | jq   # configs available to train against
curl -s http://localhost:9090/api/v1/artifacts | jq   # every model and prediction
curl -s http://localhost:9090/api/v1/jobs      | jq   # train/predict job history
# the lineage under one model - its predictions:
curl -s "http://localhost:9090/api/v1/artifacts/<artifact-id>/\$tree" | jq
```

!!! note "This is the API chap-core uses"
    After you register the model ([step 7b](chapkit-register.md)), chap-core drives these exact
    endpoints for you: it pushes a config, calls `$train`, then `$predict`, and reads back the
    artifacts. Running them by hand here is just doing manually what chap automates.

!!! tip "More in the chapkit docs"
    Other topics, each on its own page:
    [scaffolding and templates](https://dhis2-chap.github.io/chapkit/guides/cli-scaffolding/),
    [configuration management](https://dhis2-chap.github.io/chapkit/guides/configuration-management/),
    [monitoring (`/metrics`)](https://dhis2-chap.github.io/chapkit/guides/monitoring/),
    [database migrations](https://dhis2-chap.github.io/chapkit/guides/database-migrations/),
    [migrating an existing `MLproject`](https://dhis2-chap.github.io/chapkit/guides/mlproject-migrate/),
    and the full [API reference](https://dhis2-chap.github.io/chapkit/api-reference/) -
    indexed at [dhis2-chap.github.io/chapkit](https://dhis2-chap.github.io/chapkit/).

## What's next

Your model runs and passes its own tests. Next, [register it with CHAP](chapkit-register.md) so
it shows up in chap-core and the Modelling App alongside the built-in models.
