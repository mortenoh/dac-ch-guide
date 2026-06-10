# Evaluate and predict through the API

Everything the Modelling App does, it does by calling APIs - so you can drive the same
evaluation and prediction from the command line. This mirrors the [UI walkthrough](with-ui.md)
using the [shared configuration](index.md), and is handy for scripting and automation.

!!! note "Before you start"
    DHIS2 + chap-core are running and connected ([step 5: install the apps](../getting-started/install-apps.md)),
    and you have **`curl`** and **`jq`** (from [step 1](../getting-started/prerequisites.md)). The
    exact org units, periods, and data items come from the [shared configuration](index.md) (step 6).

Two APIs are involved:

- the **DHIS2 analytics API** (`/api/analytics`) - where the data comes from;
- the **chap API**, reached through the DHIS2 route (`/api/routes/chap/run/...`) - which runs
  the model.

chap-core has no login of its own; you authenticate to **DHIS2**, which proxies to chap.

```bash
export DHIS2="http://localhost:8080/api"
export CHAP="$DHIS2/routes/chap/run/v1"
export AUTH="admin:district"
```

## Step 1 - Find the model

```bash
curl -fsS -u "$AUTH" "$CHAP/crud/configured-models" \
  | jq -r '.[] | "\(.id)\t\(.name)\t\(.displayName)"'
```

```text
12   chapkit-ewars-model   CHAP-EWARS Model (chapkit)
```

## Step 2 - Get the data from the analytics API

The model needs the four data items across the 18 provinces and the 24 months. That is one
call to the DHIS2 [**analytics API**](https://docs.dhis2.org/en/develop/using-the-api/dhis-core-version-242/analytics.html),
with the `dx` (data), `ou` (org units), and `pe` (periods) dimensions:

```bash
OUS="W6sNfkJcXGC;YvLOmtTQD6b;XKGgynPS1WZ;rO2RVJWHpCe;FRmrFTE63D0;MBZYTqkEgwf;hdeC7uX9Cko;RdNV4tTRNEo;VWGSudnonm5;quFXhkOJGB4;vBWtCmNNnCG;c4HrGRJoarj;pFCZqWnXtoU;TOgZ99Jv0bN;dOhqCNenSjS;sv6c7CpPcrc;hRQsZhmvqgS;K27JzTKmBKh"
PES="202301;202302;202303;202304;202305;202306;202307;202308;202309;202310;202311;202312;202401;202402;202403;202404;202405;202406;202407;202408;202409;202410;202411;202412"
DXS="SK9a8nJJTAI;D8Q6nNeQ7i3;DZte8CXJ6zJ;Pjd8Rn6mTb0"   # disease cases, population, rainfall, temperature

curl -fsS -u "$AUTH" \
  "$DHIS2/analytics.json?dimension=dx:$DXS&dimension=ou:$OUS&dimension=pe:$PES&skipMeta=true" \
  -o analytics.json

jq '{headers:[.headers[].name], rowCount:(.rows|length)}' analytics.json
```

```json
{ "headers": ["dx", "ou", "pe", "value"], "rowCount": 1656 }
```

Each row is `[dataElement, orgUnit, period, value]`. Note the count: the three covariates have
a value for every province-month (432 rows each), but the **disease-cases target has fewer**
(360) - some province-months simply have no reported cases. That is expected; CHAP handles the
missing target observations, so you pass the data through as-is.

## Step 3 - Get the org-unit geometry

The run also needs each province's polygon, which DHIS2 serves alongside the org units (see the
[metadata / organisation units API](https://docs.dhis2.org/en/develop/using-the-api/dhis-core-version-242/metadata.html)):

```bash
curl -fsS -u "$AUTH" \
  "$DHIS2/organisationUnits.json?filter=level:eq:2&fields=id,geometry&paging=false" \
  -o orgunits.json
```

## Step 4 - Build the chap request

Reshape the analytics rows into chap **observations** (mapping each dataElement to its model
feature) and wrap the geometry into a GeoJSON `FeatureCollection`:

```bash
jq -n --slurpfile a analytics.json --slurpfile o orgunits.json '
  {SK9a8nJJTAI:"disease_cases", D8Q6nNeQ7i3:"population",
   DZte8CXJ6zJ:"rainfall",     Pjd8Rn6mTb0:"mean_temperature"} as $map
  | {
      name: "EWARS - Laos provinces 2023-2024",
      modelId: "chapkit-ewars-model",
      dataSources: [
        {covariate:"disease_cases",    dataElementId:"SK9a8nJJTAI"},
        {covariate:"population",       dataElementId:"D8Q6nNeQ7i3"},
        {covariate:"rainfall",         dataElementId:"DZte8CXJ6zJ"},
        {covariate:"mean_temperature", dataElementId:"Pjd8Rn6mTb0"}
      ],
      providedData: [ $a[0].rows[]
        | {orgUnit:.[1], period:.[2], featureName:$map[.[0]], value:(.[3]|tonumber)} ],
      dataToBeFetched: [],
      geojson: { type:"FeatureCollection", features: [ $o[0].organisationUnits[]
        | select(.geometry) | {type:"Feature", id:.id, properties:{id:.id}, geometry:.geometry} ] }
    }' > request.json
```

`providedData` is the data you supply; `dataToBeFetched` stays empty because you are providing
everything. `dataSources` records which dataElement backs each feature.

## Step 5 - Validate, then create the evaluation

First do a **dry run**. It validates the data for all 18 provinces *synchronously* (no model
run), which is worth doing before a multi-minute evaluation - especially in a workshop:

```bash
curl -fsS -u "$AUTH" -X POST "$CHAP/analytics/create-backtest-with-data/?dryRun=true" \
  -H 'Content-Type: application/json' -d @request.json
```

```json
{ "id": null, "importedCount": 18, "rejected": [] }
```

`rejected: []` and `importedCount: 18` means every province validated. Now run it for real and
**capture the job id** it returns:

```bash
JOB_ID=$(curl -fsS -u "$AUTH" -X POST "$CHAP/analytics/create-backtest-with-data/" \
  -H 'Content-Type: application/json' -d @request.json | jq -r '.id')
echo "$JOB_ID"
```

!!! tip "Use `-fsS`, not `-s`"
    `curl -fsS` fails loudly on an HTTP error (and shows the message) instead of printing an
    error body that `jq` then chokes on - so a `422` or `500` does not masquerade as malformed
    JSON. Worth it on every `POST`.

## Step 6 - Wait for the job, then read the result

A job's status is a plain JSON string. It moves through `"PENDING"` (queued) ->
`"STARTED"` (the worker is running the model) -> `"SUCCESS"`; a `"FAILURE"` means the run
broke - read its log (see [Find and diagnose failures](../operations/logs.md)). Poll it
until it reads `"SUCCESS"`:

```bash
curl -fsS -u "$AUTH" "$CHAP/jobs/$JOB_ID"
```

```json
"SUCCESS"
```

Then read the evaluation - metrics and all - straight from the finished job:

```bash
curl -fsS -u "$AUTH" "$CHAP/jobs/$JOB_ID/evaluation_result" \
  | jq '.aggregateMetrics | {mae, rmse, crps, coverage_10_90}'
```

```json
{ "mae": 35.48, "rmse": 57.94, "crps": 26.71, "coverage_10_90": 0.70 }
```

Lower MAE / RMSE / CRPS is better; `coverage_10_90` near `0.8` means the 10-90% interval is
well-calibrated.

!!! warning "Your numbers will differ - that is fine"
    EWARS is a Bayesian model and the demo target has gaps, so metrics move noticeably between
    runs. MAE in the **low-to-mid 30s** is typical here, but a run at 29 or 38 is just as valid.
    Judge a model by **comparing runs**, not against a fixed number - a successful run with
    different metrics is not wrong.

## Predicting: the prediction setup

In the Modelling App, forecasts run from a **prediction setup** - a saved, reusable object
created from an evaluation - and the API works the same way. This is the primary path: you
create a setup once from your backtest, then run forecasts from it (now, or later as new data
arrives). The one-shot `make-prediction` call is still available as a shortcut - see the tip at
the end.

### Step 1 - Find the backtest id

Your evaluation from Step 5 is stored as a **backtest**. Resolve its id by the name you gave it:

```bash
BACKTEST_ID=$(curl -fsS -u "$AUTH" "$CHAP/crud/backtests" \
  | jq -r --arg n "EWARS - Laos provinces 2023-2024" '.[] | select(.name==$n) | .id' | head -1)
echo "$BACKTEST_ID"
```

### Step 2 - Create the prediction setup

`POST` the backtest id and a name; the setup **inherits the model, organisation units, periods,
and data mapping** from the backtest, so you do not re-send any of that. A backtest can have only
**one** setup, so reuse an existing one if there is one and create only when there is not - this
makes the block safe to re-run:

```bash
# reuse the setup for this backtest if it exists...
SETUP_ID=$(curl -fsS -u "$AUTH" "$CHAP/crud/prediction-setups" \
  | jq -r --argjson b "$BACKTEST_ID" 'map(select(.backtestId == $b))[0].id // empty')

# ...otherwise create it
if [ -z "$SETUP_ID" ]; then
  SETUP_ID=$(curl -fsS -u "$AUTH" -X POST "$CHAP/crud/prediction-setups" \
    -H 'Content-Type: application/json' \
    -d "{\"backtestId\": $BACKTEST_ID, \"name\": \"EWARS - Laos provinces 2023-2024\"}" \
    | jq -r '.id')
fi
echo "$SETUP_ID"
```

!!! note "Why look up first"
    A bare `POST` for a backtest that **already** has a setup returns **HTTP 409**, and with
    `curl -fsS` that leaves `$SETUP_ID` empty - which then breaks the run below. The lookup above
    avoids that by resolving the existing setup (by its `backtestId`) before creating one.

### Step 3 - Run a forecast from the setup

Running supplies the **data to forecast from** - the same observations and geometry as the
evaluation, so reuse `request.json` - plus `nPeriods`. The forecast covers the periods *after*
the data's last month, so with data through `2024-12` and `nPeriods: 3` you get `2025-01` to
`2025-03`:

```bash
jq '{name:"EWARS - Laos provinces 2023-2024", geojson:.geojson, providedData:.providedData, nPeriods:3}' \
  request.json > run-request.json

PRED_JOB=$(curl -fsS -u "$AUTH" -X POST "$CHAP/crud/prediction-setups/$SETUP_ID/run" \
  -H 'Content-Type: application/json' -d @run-request.json | jq -r '.id')
```

Poll the job as before, then read the forecast from its `prediction_result`:

```bash
curl -fsS -u "$AUTH" "$CHAP/jobs/$PRED_JOB"                      # "SUCCESS"
curl -fsS -u "$AUTH" "$CHAP/jobs/$PRED_JOB/prediction_result" \
  | jq '{name, modelId, nPeriods, orgUnits:(.orgUnits|length)}'
```

Re-running the setup (Step 3 again, with newer data) produces another forecast under the same
setup - which is the point of keeping it.

!!! tip "Quick one-shot: make-prediction"
    To forecast once without a setup, post the **full** request (as in Step 4, plus `nPeriods`)
    straight to `…/analytics/make-prediction`; it returns a job the same way:

    ```bash
    jq '. + {nPeriods: 3}' request.json > prediction-request.json
    curl -fsS -u "$AUTH" -X POST "$CHAP/analytics/make-prediction" \
      -H 'Content-Type: application/json' -d @prediction-request.json | jq -r '.id'
    ```

    Prefer the setup flow above for anything you will repeat - it mirrors the app and keeps each
    run under one named, re-runnable setup.

!!! note "Scheduling is external"
    A setup also accepts `scheduleCronExpression` / `scheduleEnabled`, but chap does **not** run
    the cron itself - those fields only record a schedule for an **external** trigger (a cron job,
    CI, an orchestrator) to call the `…/run` endpoint on. In these guides you run it on demand.

!!! note "Assignment: drive chap from curl"
    - [ ] Fetch the data from the analytics API and build `request.json`.
    - [ ] Dry-run it (`?dryRun=true`), then create the evaluation, capturing the `JOB_ID`.
    - [ ] Poll `…/jobs/$JOB_ID` to `"SUCCESS"` and read `…/jobs/$JOB_ID/evaluation_result`.
    - [ ] Resolve the `BACKTEST_ID`, create a **prediction setup**, run it (`nPeriods: 3`), and
      read the run's `prediction_result`.

## Next step

Continue to [step 7: configure a model](configured-models-curl.md), or return to the
[Modelling App walkthrough](with-ui.md) to see the same workflow in the UI.
