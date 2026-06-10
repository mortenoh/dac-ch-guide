# Configure a model

This is step 7 of the workshop. It changes the model configuration while reusing the
evaluation and prediction workflow from step 6.

A **configured model** is a **model template** plus a chosen set of **options** - a
ready-to-run variant. The stock models you used earlier (like *CHAP-EWARS Model (chapkit)*) are
configured models; here you create your own variant.

!!! info "Why curl here"
    The Modelling App also has a **New model** screen, but this guide configures the model over
    the **API on purpose**: it is scriptable, shows exactly which template, options, and
    covariates go into the request, and hands back the canonical name you run the model by.
    Models created over the API appear in the app immediately and are usable for evaluations and
    predictions straight away.

We will build a variant of the chapkit EWARS model that turns on **region-specific seasonal
effects** and uses the climate covariates. Reuse the connection from the
[evaluation curl page](with-curl.md):

```bash
export CHAP="http://localhost:8080/api/routes/chap/run/v1"
export AUTH="admin:district"
```

## Step 1 - Pick a model template

List the templates to find the one to build on (we use **chapkit-ewars-model**):

```bash
curl -fsS -u "$AUTH" "$CHAP/crud/model-templates" \
  | jq -r '.[] | "\(.id)\t\(.name)\t\(.displayName)"'
```

```text
11   chapkit-ewars-model   CHAP-EWARS Model (chapkit)
...
```

The numeric ids are assigned by your database, so resolve the one you want **by name** rather
than hard-coding it:

```bash
TEMPLATE_ID=$(curl -fsS -u "$AUTH" "$CHAP/crud/model-templates" \
  | jq -r '.[] | select(.name=="chapkit-ewars-model") | .id')
```

Inspect what that template lets you set - its required covariates and its options:

```bash
curl -fsS -u "$AUTH" "$CHAP/crud/model-templates" \
  | jq --argjson t "$TEMPLATE_ID" '.[] | select(.id==$t) | {requiredCovariates, userOptions: (.userOptions | keys)}'
```

```json
{ "requiredCovariates": ["population"],
  "userOptions": ["n_lags", "precision", "region_seasonal"] }
```

So `population` is always required, and you can tune `n_lags`, `precision`, and
`region_seasonal`.

## Step 2 - Create the configured model

`POST` the template id, a name, the option values, and any **additional** covariates (beyond
the required `population`). Build the body with `jq` so `$TEMPLATE_ID` is filled in, and
**capture the canonical name** from the response - that string is how you run the model later:

```bash
MODEL_NAME=$(jq -n --argjson t "$TEMPLATE_ID" '{
    name: "EWARS climate + region-seasonal",
    modelTemplateId: $t,
    userOptionValues: { n_lags: [3], precision: 0.01, region_seasonal: true },
    additionalContinuousCovariates: ["rainfall", "mean_temperature"]
  }' \
  | curl -fsS -u "$AUTH" -X POST "$CHAP/crud/configured-models" \
      -H 'Content-Type: application/json' -d @- \
  | jq -r '.name')

echo "$MODEL_NAME"
```

```text
chapkit-ewars-model:EWARS climate + region-seasonal
```

!!! tip "n_lags is per covariate"
    `n_lags` is a list, one entry per additional covariate (in order). A single-element list
    like `[3]` broadcasts to all of them.

!!! note "Creating is idempotent"
    Re-running the same `POST` returns the **existing** model (same id) rather than creating a
    duplicate, so it is safe to repeat.

## Step 3 - Confirm and use it

It now appears alongside the built-in models (find it by name - the id depends on your
database):

```bash
curl -fsS -u "$AUTH" "$CHAP/crud/configured-models" \
  | jq -r --arg n "$MODEL_NAME" '.[] | select(.name==$n) | "\(.id)\t\(.displayName)"'
```

```text
13   CHAP-EWARS Model (chapkit) [Ewars climate + region-seasonal]
```

Your variant now appears **everywhere the stock models do**, so run it however you ran step 6:

- **In the Modelling App** - it shows up in the model picker (Evaluate -> New evaluation ->
  Select model) under its display name *CHAP-EWARS Model (chapkit) [Ewars climate +
  region-seasonal]*. Pick it and run it exactly as in the [UI walkthrough](with-ui.md) - no curl
  needed.
- **Through the API** - build a request as on the [evaluation curl page](with-curl.md), with the
  `modelId` set to this **canonical name**:

  ```json
  "modelId": "chapkit-ewars-model:EWARS climate + region-seasonal"
  ```

!!! warning "modelId is a string, not the numeric id"
    The API run endpoints want the model's canonical **name**. Passing the numeric id (e.g. `13`)
    returns **HTTP 422** - use `$MODEL_NAME` from Step 2.

!!! note "Where the predictions land"
    This variant targets **disease cases** (dengue), so its forecasts import into the existing
    `CHAP Dengue Cases (Any) - Weekly Quantile …` data elements - the same outputs the stock
    model uses. A model with a **different target** would need its own output data elements in
    DHIS2 first.

!!! note "Assignment: configure your own model"
    - [ ] Resolve the `chapkit-ewars-model` template id by name.
    - [ ] Create a variant with `region_seasonal: true` and the climate covariates, capturing
      its canonical name.
    - [ ] Confirm it appears (in `crud/configured-models`, or the Modelling App's model picker),
      then run an evaluation with it - in the app, or with its name as the `modelId` via the API.

## Where to go next

You have completed the main workshop path. Run the custom variant with the
[shared demo workflow](index.md), or jump to the [reference guides](../index.md#jump-to-a-task)
to diagnose jobs, inspect stored results, back up data, or upgrade CHAP.
