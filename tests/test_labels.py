from nil15.labels import first_goal_second, no_goal_first_15, timestamp_seconds


def shot(timestamp: str, outcome: str = "Goal") -> dict:
    return {
        "timestamp": timestamp,
        "period": 1,
        "type": {"name": "Shot"},
        "shot": {"outcome": {"name": outcome}},
    }


def test_timestamp_seconds() -> None:
    assert timestamp_seconds("00:14:59.500") == 899.5


def test_goal_before_boundary_is_early() -> None:
    events = [shot("00:14:59.999")]
    assert first_goal_second(events) == 899.999
    assert no_goal_first_15(events) == 0


def test_goal_at_boundary_is_not_in_window() -> None:
    assert no_goal_first_15([shot("00:15:00.000")]) == 1


def test_missed_shot_is_not_goal() -> None:
    assert no_goal_first_15([shot("00:02:00.000", "Off T")]) == 1


def test_own_goal_counts() -> None:
    event = {
        "timestamp": "00:03:00.000",
        "period": 1,
        "type": {"name": "Own Goal For"},
    }
    assert no_goal_first_15([event]) == 0


def test_second_half_timestamp_cannot_be_an_early_goal() -> None:
    event = shot("00:02:00.000")
    event["period"] = 2
    assert no_goal_first_15([event]) == 1
