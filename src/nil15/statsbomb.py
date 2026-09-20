from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from nil15.config import RAW_DIR, STATSBOMB_RAW_BASE


class StatsBombOpenData:
    """Small, cache-first client for StatsBomb's public JSON repository."""

    def __init__(self, root: Path = RAW_DIR, timeout: float = 60.0) -> None:
        self.root = root
        self.timeout = timeout

    def _download_json(self, relative_path: str, destination: Path) -> Any:
        if destination.exists():
            return json.loads(destination.read_text(encoding="utf-8"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        url = f"{STATSBOMB_RAW_BASE}/{relative_path}"
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        payload = response.json()
        destination.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def competitions(self) -> list[dict[str, Any]]:
        return self._download_json("competitions.json", self.root / "competitions.json")

    def matches(self, competition_id: int, season_id: int) -> list[dict[str, Any]]:
        relative = f"matches/{competition_id}/{season_id}.json"
        return self._download_json(relative, self.root / relative)

    def events(self, match_id: int) -> list[dict[str, Any]]:
        relative = f"events/{match_id}.json"
        return self._download_json(relative, self.root / relative)

    def sync(self, competition_id: int, season_id: int) -> int:
        matches = self.matches(competition_id, season_id)
        missing = [
            int(match["match_id"])
            for match in matches
            if not (self.root / "events" / f"{match['match_id']}.json").exists()
        ]
        (self.root / "events").mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            for match_id in missing:
                response = client.get(f"{STATSBOMB_RAW_BASE}/events/{match_id}.json")
                response.raise_for_status()
                (self.root / "events" / f"{match_id}.json").write_text(
                    json.dumps(response.json()), encoding="utf-8"
                )
        return len(matches)
