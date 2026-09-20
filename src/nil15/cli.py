from __future__ import annotations

import json

import pandas as pd
import typer

from nil15.config import PROCESSED_DIR
from nil15.dataset import build_dataset
from nil15.model import train_chronological
from nil15.statsbomb import StatsBombOpenData

app = typer.Typer(no_args_is_help=True, help="Nil15 research CLI")


@app.command()
def competitions() -> None:
    """List StatsBomb Open Data competitions and seasons."""
    rows = StatsBombOpenData().competitions()
    for item in rows:
        typer.echo(
            f"{item['competition_id']:>4}  {item['season_id']:>4}  "
            f"{item['country_name']} — {item['competition_name']} — {item['season_name']}"
        )


@app.command()
def sync(competition_id: int, season_id: int) -> None:
    """Download and cache one public competition-season."""
    count = StatsBombOpenData().sync(competition_id, season_id)
    typer.echo(f"Synced {count} matches and their event files.")


@app.command("build")
def build_command() -> None:
    """Build the leakage-safe modelling table from cached events."""
    frame = build_dataset()
    typer.echo(f"Built {len(frame)} labelled matches at {PROCESSED_DIR / 'matches.csv'}")


@app.command()
def train() -> None:
    """Train and evaluate the chronological baseline."""
    path = PROCESSED_DIR / "matches.csv"
    if not path.exists():
        raise typer.BadParameter("Processed data is missing. Run `nil15 build` first.")
    _, metrics = train_chronological(pd.read_csv(path))
    typer.echo(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    app()
