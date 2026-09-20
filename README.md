# Nil15

Nil15 is a research prototype that estimates the probability that a football match remains
**0-0 from kickoff through 14:59**. It currently uses the free
[StatsBomb Open Data](https://github.com/hudl/open-data) dataset.

## What works now

- downloads the StatsBomb competition catalogue, match lists, and event files;
- labels each match without future-data leakage;
- creates rolling home/away/team and competition features;
- trains a calibrated logistic-regression baseline using a chronological split;
- reports accuracy, Brier score, log loss, and calibration buckets;
- saves a reusable model artifact.

StatsBomb Open Data covers selected historical competitions. It is excellent for research and
model development, but it does not provide a complete upcoming-fixtures or bookmaker-odds feed.
Those will be separate adapters later.

## Definition

`no_goal_first_15 = 1` when no valid goal has a StatsBomb timestamp earlier than `00:15:00`.
A goal at exactly `00:15:00` is outside the target window. Own goals count; disallowed shots do not.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

nil15 competitions
nil15 sync 9 281
nil15 build
nil15 train
```

The `competitions` command shows valid IDs. The sync example is illustrative; available seasons
can change as StatsBomb expands its public dataset.

Downloaded source files are cached under `data/raw/statsbomb`, processed training data is written
to `data/processed`, and fitted models are written to `artifacts`. These generated files are ignored
by Git.

## Responsible use

This software produces uncertain probabilities, not guaranteed outcomes or financial advice.
Evaluate it chronologically on unseen data before considering any real-world use.
