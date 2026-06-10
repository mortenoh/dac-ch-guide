# Evaluation & prediction

This is step 6 of the workshop. The configuration on this page is the single reference used
by both walkthroughs, so switch between them without re-entering a different scenario.

With DHIS2, chap-core, and the apps running, you can now put a model to work. There are two
things you typically do with a model:

- **Evaluate (backtest)** - run the model over *historical* data and compare its predictions
  to what actually happened, to see how well it performs.
- **Predict** - run the model on the latest data to **forecast** the coming periods.

Choose how you want to drive the same workflow:

- **[In the Modelling App](with-ui.md)** - click through the screens.
- **[Through the API](with-curl.md)** - drive the run against the CHAP API through the DHIS2
  route, so you can script it.

Both use the **same configuration**, described below. Because everyone is working from the
same Laos climate demo database, you can copy these exact values.

## The model

| | |
|---|---|
| **Model** | CHAP-EWARS Model (chapkit) |
| **Configured model** | `chapkit-ewars-model` - always refer to it by this **canonical name**; the numeric id (e.g. `12`) is assigned by your database and differs per install |
| **What it is** | A Bayesian hierarchical model (WHO EWARS) implemented with INLA, packaged as a chapkit model. |
| **Target** | `disease_cases` |
| **Required covariate** | `population` |
| **Extra covariates** | `rainfall`, `mean_temperature` |
| **Period type** | Monthly |

## The data (Laos demo)

We model **monthly dengue cases** across the **18 provinces** of Lao PDR, using climate
covariates. The model's features map to these DHIS2 data items:

| Model feature | DHIS2 data item | dataElement id |
|---|---|---|
| Disease cases (target) | Dengue Cases (Any) - Weekly | `SK9a8nJJTAI` |
| Population | LSB: Population (Estimated-single age) | `D8Q6nNeQ7i3` |
| Rainfall | CCH - Precipitation (CHIRPS) | `DZte8CXJ6zJ` |
| Mean temperature | CCH - Air temperature (ERA5-Land) | `Pjd8Rn6mTb0` |

| | |
|---|---|
| **Organisation units** | Province level (level 2) - all 18 provinces |
| **Period range** | `2023-01` to `2024-12` (Monthly) |
| **Prediction horizon** | 3 months (the default `n_periods`; forecasts `2025-01` to `2025-03`) |

??? note "The 18 province org-unit IDs"
    ```
    W6sNfkJcXGC  01 Vientiane Capital   YvLOmtTQD6b  02 Phongsali
    XKGgynPS1WZ  03 Louangnamtha        rO2RVJWHpCe  04 Oudomxai
    FRmrFTE63D0  05 Bokeo               MBZYTqkEgwf  06 Louangphabang
    hdeC7uX9Cko  07 Houaphan            RdNV4tTRNEo  08 Xainyabouli
    VWGSudnonm5  09 Xiangkhouang        quFXhkOJGB4  10 Vientiane
    vBWtCmNNnCG  11 Bolikhamxai         c4HrGRJoarj  12 Khammouan
    pFCZqWnXtoU  13 Savannakhet         TOgZ99Jv0bN  14 Salavan
    dOhqCNenSjS  15 Xekong              sv6c7CpPcrc  16 Champasak
    hRQsZhmvqgS  17 Attapu              K27JzTKmBKh  18 Xaisomboun
    ```

## How DHIS2, the app, and chap fit together

The Modelling App (and your curl commands) reach chap-core **through the DHIS2 route** you set
up earlier. The chap API lives under:

```text
http://localhost:8080/api/routes/chap/run/v1/...
```

with the pieces you will use:

- `…/v1/crud/configured-models` - the models, e.g. id `12`
- `…/v1/crud/backtests` - evaluations
- `…/v1/crud/prediction-setups` - reusable prediction configs (created from a backtest, then run)
- `…/v1/crud/predictions` - the forecasts a setup run produces
- `…/v1/jobs` - the running/finished jobs

!!! note "Before you start"
    DHIS2 + chap-core are running and connected ([Connect CHAP](../getting-started/chap-setup.md)),
    and the **Modelling App** is installed ([Install the apps](../getting-started/install-apps.md)).

## Choose a walkthrough

Start with the [Modelling App walkthrough](with-ui.md) for the main workshop path. Use the
[API walkthrough](with-curl.md) when you want to understand or automate the same requests.
