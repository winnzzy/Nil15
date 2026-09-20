from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import pandas as pd

from nil15.config import PROCESSED_DIR, RAW_DIR
from nil15.labels import first_goal_second, no_goal_first_15


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _match_rows(raw_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match_file in sorted((raw_root / "matches").glob("*/*.json")):
        competition_id = int(match_file.parent.name)
        season_id = int(match_file.stem)
        for match in _load_json(match_file):
            match_id = int(match["match_id"])
            event_file = raw_root / "events" / f"{match_id}.json"
            if not event_file.exists():
                continue
            events = _load_json(event_file)
            rows.append(
                {
                    "match_id": match_id,
                    "match_date": match["match_date"],
                    "kick_off": match.get("kick_off") or "00:00:00",
                    "competition_id": competition_id,
                    "season_id": season_id,
                    "home_team_id": int(match["home_team"]["home_team_id"]),
                    "away_team_id": int(match["away_team"]["away_team_id"]),
                    "home_team": match["home_team"]["home_team_name"],
                    "away_team": match["away_team"]["away_team_name"],
                    "first_goal_second": first_goal_second(events),
                    "no_goal_first_15": no_goal_first_15(events),
                }
            )
    return rows


def build_dataset(raw_root: Path = RAW_DIR, output_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    frame = pd.DataFrame(_match_rows(raw_root))
    if frame.empty:
        raise ValueError("No synced StatsBomb matches found. Run `nil15 sync` first.")

    frame["match_datetime"] = pd.to_datetime(
        frame["match_date"] + " " + frame["kick_off"], errors="coerce", utc=True
    )
    frame = frame.sort_values(["match_datetime", "match_id"]).reset_index(drop=True)

    team_history: dict[int, deque[int]] = defaultdict(lambda: deque(maxlen=10))
    league_history: dict[int, deque[int]] = defaultdict(lambda: deque(maxlen=100))
    feature_rows: list[dict[str, float]] = []

    for row in frame.itertuples(index=False):
        home_history = team_history[row.home_team_id]
        away_history = team_history[row.away_team_id]
        competition_history = league_history[row.competition_id]
        feature_rows.append(
            {
                "home_no_goal_rate_10": sum(home_history) / len(home_history)
                if home_history
                else 0.5,
                "away_no_goal_rate_10": sum(away_history) / len(away_history)
                if away_history
                else 0.5,
                "competition_no_goal_rate_100": (
                    sum(competition_history) / len(competition_history)
                    if competition_history
                    else 0.5
                ),
                "home_history_count": float(len(home_history)),
                "away_history_count": float(len(away_history)),
            }
        )
        target = int(row.no_goal_first_15)
        home_history.append(target)
        away_history.append(target)
        competition_history.append(target)

    result = pd.concat([frame, pd.DataFrame(feature_rows)], axis=1)
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / "matches.csv", index=False)
    return result
