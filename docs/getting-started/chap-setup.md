# Choose how to run CHAP

This is the only branch in the core setup. Pick **one** route; both end with DHIS2 connected
to the same CHAP API, so the rest of the workshop is identical.

| Path | Choose it when | What runs |
|------|----------------|-----------|
| **[Quick setup (bundled)](add-chap-core.md)** | You want to complete the workshop with the least setup. | Released CHAP images are added to the DHIS2 Compose stack. |
| **[Development setup (source)](chap-core-from-source.md)** | You plan to change chap-core or develop models. | CHAP is built from a separate local clone. |

!!! warning "Run only one CHAP setup"
    Both paths use port `8000`. Do not run them at the same time.

Whichever path you choose, finish by checking:

- CHAP reports healthy.
- The EWARS model is registered.
- DHIS2 can reach CHAP through its `chap` route.

Then continue to [step 4: install the apps](install-apps.md).
