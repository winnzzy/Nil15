from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from nil15.config import ARTIFACT_DIR

FEATURES = [
    "home_no_goal_rate_10",
    "away_no_goal_rate_10",
    "competition_no_goal_rate_100",
    "home_history_count",
    "away_history_count",
]
TARGET = "no_goal_first_15"


def train_chronological(
    frame: pd.DataFrame, artifact_dir: Path = ARTIFACT_DIR, train_fraction: float = 0.8
) -> tuple[Pipeline, dict[str, Any]]:
    if len(frame) < 20:
        raise ValueError("At least 20 matches are required for a chronological train/test split.")
    split = max(1, min(len(frame) - 1, int(len(frame) * train_fraction)))
    train, test = frame.iloc[:split], frame.iloc[split:]
    if train[TARGET].nunique() < 2:
        raise ValueError("Training data must include both early-goal and no-early-goal matches.")

    pipeline = Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=1000))])
    pipeline.fit(train[FEATURES], train[TARGET])
    probability = pipeline.predict_proba(test[FEATURES])[:, 1]
    prediction = (probability >= 0.5).astype(int)
    observed, predicted = calibration_curve(
        test[TARGET], probability, n_bins=5, strategy="quantile"
    )
    metrics: dict[str, Any] = {
        "train_matches": len(train),
        "test_matches": len(test),
        "positive_rate_test": float(test[TARGET].mean()),
        "accuracy": float(accuracy_score(test[TARGET], prediction)),
        "brier_score": float(brier_score_loss(test[TARGET], probability)),
        "log_loss": float(log_loss(test[TARGET], probability, labels=[0, 1])),
        "calibration": [
            {"predicted": float(p), "observed": float(o)} for p, o in zip(predicted, observed)
        ],
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, artifact_dir / "nil15_baseline.joblib")
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return pipeline, metrics
