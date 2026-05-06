"""
anomaly_detector.py — Stage 4b: Anomaly detection using Isolation Forest.

No labelled data required. Each log entry is scored; entries with
scores below the threshold are flagged as anomalous.

Public API
----------
train_model(feature_matrix, contamination) -> IsolationForest
score_logs(model, logs)                    -> list[dict]
print_anomaly_summary(logs)                -> None
"""

import numpy as np
from sklearn.ensemble import IsolationForest


def train_model(
    feature_matrix: list[list[float]],
    contamination: float = 0.05,
) -> IsolationForest:
    """
    Train an Isolation Forest model on extracted log features.

    Args:
        feature_matrix: List of feature vectors (one per log entry).
        contamination:  Estimated fraction of anomalies in the dataset.
                        Tune upward (e.g. 0.10) for noisier logs.

    Returns:
        Trained IsolationForest model ready for scoring.
    """
    model = IsolationForest(
        n_estimators=100,       # 100 isolation trees — robust default
        contamination=contamination,
        random_state=42,        # reproducible results
        n_jobs=-1,              # use all available CPU cores
    )
    model.fit(feature_matrix)
    return model


def score_logs(model: IsolationForest, logs: list[dict]) -> list[dict]:
    """
    Assign anomaly scores and labels to each log entry.

    Adds two keys in-place to every dict:
        'anomaly_score' (float) — higher means more normal; negative -> suspicious.
        'is_anomaly'    (bool)  — True when Isolation Forest predicts -1.

    Args:
        model: Trained IsolationForest model.
        logs:  List of log dicts with 'features' key populated by build_features().

    Returns:
        Same list with 'anomaly_score' and 'is_anomaly' keys added.
    """
    if not logs:
        return logs

    X = np.array([log["features"] for log in logs])
    scores = model.decision_function(X)   # higher = more normal
    predictions = model.predict(X)        # -1 = anomaly, 1 = normal

    for log, score, pred in zip(logs, scores, predictions):
        log["anomaly_score"] = round(float(score), 4)
        log["is_anomaly"] = bool(pred == -1)

    return logs


def print_anomaly_summary(logs: list[dict]) -> None:
    """
    Print a terminal summary of anomaly detection results for Stage 4.

    Shows total entries scored, number and percentage flagged as anomalous,
    and the top-5 most anomalous entries (lowest decision-function score).

    Args:
        logs: Scored log dicts — must have 'anomaly_score' and 'is_anomaly' keys.
    """
    if not logs:
        print("\n[Stage 4] No logs to summarise.")
        return

    total = len(logs)
    flagged = [l for l in logs if l.get("is_anomaly")]
    pct = 100.0 * len(flagged) / total if total else 0.0

    print("\n" + "=" * 60)
    print("[Stage 4] Feature extraction + anomaly detection complete.")
    print(f"  Total entries scored : {total:,}")
    print(f"  Anomalies flagged    : {len(flagged):,}  ({pct:.1f}%)")

    if flagged:
        top5 = sorted(flagged, key=lambda x: x["anomaly_score"])[:5]
        print("  Top anomalies (lowest score):")
        for entry in top5:
            raw_preview = entry.get("raw", "")[:80]
            print(f"    score={entry['anomaly_score']:>8.4f}  {raw_preview}")
    print("=" * 60)
