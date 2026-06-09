# DAC Climate and Health

Climate and health workshop guides for the **DHIS2 Annual Conference (DAC)**.

The guides are built as a [MkDocs](https://www.mkdocs.org/) site using the
[Material](https://squidfunk.github.io/mkdocs-material/) theme. Each guide is a short,
hands-on walkthrough - roughly 5-10 minutes of active work - with assignments to confirm your
setup as you go. Waiting time is separate and can be substantial: image pulls, DHIS2 startup,
analytics generation, model builds, and evaluations each take minutes on their own.

## Getting started

```bash
make install      # install dependencies with uv
make docs-serve   # serve the docs locally at http://127.0.0.1:8765
```

## Common tasks

| Command | Description |
| --- | --- |
| `make install` | Install dependencies |
| `make docs` / `make docs-serve` | Serve the docs locally with live reload |
| `make docs-build` | Build the static site into `site/` |
| `make lint` | Format and auto-fix with ruff |
| `make check` | Run ruff, mypy, and pyright without making changes |
| `make clean` | Remove caches and build artifacts |

## Contributing

Guides live under `docs/`. Add a new page there and register it in the `nav` section of
`mkdocs.yml`. All git activity follows
[Conventional Commits](https://www.conventionalcommits.org/).
