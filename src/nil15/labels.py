from __future__ import annotations

from typing import Any

WINDOW_END_SECONDS = 15 * 60


def timestamp_seconds(timestamp: str) -> float:
    hours, minutes, seconds = timestamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def is_valid_goal(event: dict[str, Any]) -> bool:
    if event.get("type", {}).get("name") == "Own Goal For":
        return True
    if event.get("type", {}).get("name") != "Shot":
        return False
    return event.get("shot", {}).get("outcome", {}).get("name") == "Goal"


def first_goal_second(events: list[dict[str, Any]]) -> float | None:
    goal_times = [
        timestamp_seconds(event["timestamp"])
        for event in events
        if is_valid_goal(event) and event.get("period") == 1
    ]
    return min(goal_times) if goal_times else None


def no_goal_first_15(events: list[dict[str, Any]]) -> int:
    first_goal = first_goal_second(events)
    return int(first_goal is None or first_goal >= WINDOW_END_SECONDS)
