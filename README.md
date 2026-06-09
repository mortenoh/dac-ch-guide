# DAC Guides

Guides for the **DHIS2 Annual Conference (DAC)** and its **climate track**.

The guides are built as a [MkDocs](https://www.mkdocs.org/) site using the
[Material](https://squidfunk.github.io/mkdocs-material/) theme. Each guide is a short,
hands-on walkthrough (around 5-6 minutes) with assignments to confirm your setup as you go.

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
