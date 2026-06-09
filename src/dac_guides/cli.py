"""Command-line interface for dac-guides."""

import typer

app = typer.Typer(
    name="dac-guides",
    help="Supporting scripts for the DHIS2 Annual Conference climate track.",
    no_args_is_help=True,
)


@app.callback()
def root() -> None:
    """Supporting scripts for the DHIS2 Annual Conference climate track."""


@app.command()
def hello(name: str = "world") -> None:
    """Print a greeting. Placeholder command until real scripts land here."""
    typer.echo(f"Hello from dac-guides, {name}!")


def main() -> None:
    """Console-script entrypoint."""
    app()
