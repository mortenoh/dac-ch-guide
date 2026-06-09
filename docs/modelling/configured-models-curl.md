# Configure a model (curl)

A **configured model** is a **model template** plus a chosen set of **options** - a
ready-to-run variant. The stock models you used earlier (like *CHAP-EWARS Model (chapkit)*) are
configured models; here you create your own variant.

!!! info "Why curl here"
    The Modelling App has a **New model** screen for this, but at the time of writing it is
    being updated to match a chap-core API change, so this guide uses the API directly. The UI
    walkthrough will be added once the app fix lands. (Models you create over the API show up in
    the app and can be used for evaluations and predictions straight away.)

We will build a variant of the chapkit EWARS model that turns on **region-specific seasonal
effects** and uses the climate covariates. Reuse the connection from the
[evaluation curl page](with-curl.md):

```bash
export CHAP="http://localhost:8080/api/routes/chap/run/v1"
export AUTH="admin:district"
```

## Step 1 - Pick a model template

List the templates and find the one to build on. We use **chapkit-ewars-model** (id `11`):

```bash
curl -s -u "$AUTH" "$CHAP/crud/model-templates" \
  | jq -r '.[] | "\(.id)\t\(.name)\t\(.displayName)"'
```

```text
11   chapkit-ewars-model   CHAP-EWARS Model (chapkit)
...
```

Inspect what that template lets you set - its required covariates and its options:

```bash
curl -s -u "$AUTH" "$CHAP/crud/model-templates" \
  | jq '.[] | select(.id==11) | {requiredCovariates, userOptions: (.userOptions | keys)}'
```

```json
{ "requiredCovariates": ["population"],
  "userOptions": ["n_lags", "precision", "region_seasonal"] }
```

So `population` is always required, and you can tune `n_lags`, `precision`, and
`region_seasonal`.

## Step 2 - Create the configured model

`POST` the template id, a name, the option values, and any **additional** covariates (beyond
the required `population`):

```bash
curl -s -u "$AUTH" -X POST "$CHAP/crud/configured-models" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "EWARS climate + region-seasonal",
    "modelTemplateId": 11,
    "userOptionValues": { "n_lags": [3], "precision": 0.01, "region_seasonal": true },
    "additionalContinuousCovariates": ["rainfall", "mean_temperature"]
  }' | jq '{id, name, usesChapkit, userOptionValues, additionalContinuousCovariates}'
```

```json
{
  "id": 13,
  "name": "chapkit-ewars-model:EWARS climate + region-seasonal",
  "usesChapkit": true,
  "userOptionValues": { "n_lags": [3], "precision": 0.01, "region_seasonal": true },
  "additionalContinuousCovariates": ["rainfall", "mean_temperature"]
}
```

The new model gets an **id** (here `13`) - that is what you reference when running it.

!!! tip "n_lags is per covariate"
    `n_lags` is a list, one entry per additional covariate (in order). A single-element list
    like `[3]` broadcasts to all of them.

## Step 3 - Confirm and use it

It now appears alongside the built-in models:

```bash
curl -s -u "$AUTH" "$CHAP/crud/configured-models" \
  | jq -r '.[] | select(.id==13) | "\(.id)\t\(.displayName)"'
```

```text
13   CHAP-EWARS Model (chapkit) [Ewars climate + region-seasonal]
```

Run it exactly like the stock model - build a request as in the
[evaluation curl page](with-curl.md), but set `"modelId": 13` (or the name) when you create the
backtest or prediction.

!!! note "Where the predictions land"
    This variant targets **disease cases** (dengue), so its forecasts import into the existing
    `CHAP Dengue Cases (Any) - Weekly Quantile …` data elements - the same outputs the stock
    model uses. A model with a **different target** would need its own output data elements in
    DHIS2 first.

!!! note "Assignment: configure your own model"
    - [ ] List the model templates and pick `chapkit-ewars-model` (id `11`).
    - [ ] Create a variant with `region_seasonal: true` and the climate covariates.
    - [ ] Confirm it appears in `crud/configured-models`, then run an evaluation against its id.

## What's next

You have a custom model variant. Next in the climate track: comparing models - run several
variants over the same data and compare their metrics.
