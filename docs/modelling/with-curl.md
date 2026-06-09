# With curl

Everything the Modelling App does, it does by calling APIs - so you can drive the same
evaluation and prediction from the command line. This mirrors the [UI walkthrough](with-ui.md)
using the [shared configuration](index.md), and is handy for scripting and automation.

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
curl -s -u "$AUTH" "$CHAP/crud/configured-models" \
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

curl -s -u "$AUTH" \
  "$DHIS2/analytics.json?dimension=dx:$DXS&dimension=ou:$OUS&dimension=pe:$PES&skipMeta=true" \
  -o analytics.json

jq '{headers:[.headers[].name], rowCount:(.rows|length)}' analytics.json
```

```json
{ "headers": ["dx", "ou", "pe", "value"], "rowCount": 1656 }
```

Each row is `[dataElement, orgUnit, period, value]`.

## Step 3 - Get the org-unit geometry

The run also needs each province's polygon, which DHIS2 serves alongside the org units (see the
[metadata / organisation units API](https://docs.dhis2.org/en/develop/using-the-api/dhis-core-version-242/metadata.html)):

```bash
curl -s -u "$AUTH" \
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

## Step 5 - Create the evaluation

`POST` the request. The endpoint returns a **job** that runs the model in the background:

```bash
curl -s -u "$AUTH" -X POST "$CHAP/analytics/create-backtest-with-data/" \
  -H 'Content-Type: application/json' -d @request.json
```

```json
{ "id": "64662ca5-7196-4e48-aad0-6bafb5fce341", "importedCount": 18, "rejected": [] }
```

## Step 6 - Wait for the job, then read the result

Poll the jobs until yours reaches `SUCCESS`; its `result` is the new backtest id:

```bash
curl -s -u "$AUTH" "$CHAP/jobs" \
  | jq -r '.[] | "\(.status)\t\(.type)\t\(.name)"'
```

```text
SUCCESS   create_backtest_from_data   EWARS - Laos provinces 2023-2024
```

Read its metrics (lower error is better; coverage near the interval width is well-calibrated):

```bash
curl -s -u "$AUTH" "$CHAP/crud/backtests/<id>" | jq '.aggregateMetrics | {mae, rmse, crps, coverage_10_90}'
```

```json
{ "mae": 29.26, "rmse": 50.18, "crps": 21.95, "coverage_10_90": 0.69 }
```

!!! note
    EWARS is a Bayesian model, so exact metric values vary a little from run to run - expect
    numbers in this range rather than identical ones.

## Predicting instead

A forecast uses the **same data**, posted to a different endpoint with how many future periods
to predict. Build the request exactly as in Step 4 (you can reuse `request.json`), add
`"nPeriods": 3`, and `POST`:

```bash
jq '. + {nPeriods: 3}' request.json > prediction-request.json

curl -s -u "$AUTH" -X POST "$CHAP/analytics/make-prediction" \
  -H 'Content-Type: application/json' -d @prediction-request.json
```

Poll the job as before, then read the forecast:

```bash
curl -s -u "$AUTH" "$CHAP/crud/predictions/<id>" \
  | jq '{id, name, modelId, nPeriods, orgUnits:(.orgUnits|length)}'
```

!!! note "Assignment: drive chap from curl"
    - [ ] Fetch the data from the analytics API and build `request.json`.
    - [ ] `POST` it to create an evaluation and watch the job reach `SUCCESS`.
    - [ ] Read its `aggregateMetrics`, then create a prediction (`nPeriods: 3`) the same way.

## What's next

You have now run the full model workflow both ways - through the app and over the API. From
here the climate track moves into configuring your own models and comparing them.
