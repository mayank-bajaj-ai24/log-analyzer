"""
tests/test_anomaly.py — Member 3 (Roshan George) test suite.

Tests for:
  - pipeline/feature_extraction.py  (build_features, extract_level, extract_hour)
  - pipeline/anomaly_detector.py    (train_model, score_logs, print_anomaly_summary)

Run independently with:
    pytest tests/test_anomaly.py -v

All tests use synthetic log dicts — no dependency on other members' modules.
"""

import math
import pytest

from pipeline.feature_extraction import build_features, extract_level, extract_hour
from pipeline.anomaly_detector import train_model, score_logs, print_anomaly_summary


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_LOGS = [
    {"raw": "INFO normal operation", "template": "INFO normal operation", "cluster_id": 1},
    {"raw": "INFO normal operation", "template": "INFO normal operation", "cluster_id": 1},
    {"raw": "CRITICAL SYSTEM FAILURE DISK FULL NODE 3", "template": "CRITICAL SYSTEM FAILURE", "cluster_id": 99},
]

# Larger fixture: 20 INFO + 1 CRITICAL so Isolation Forest has enough contrast
LARGE_LOGS = (
    [{"raw": "INFO 09:00:01 heartbeat ok", "template": "INFO heartbeat ok", "cluster_id": 1}] * 20
    + [{"raw": "CRITICAL 03:17:45 SYSTEM HALT memory exhausted", "template": "CRITICAL SYSTEM HALT", "cluster_id": 99}]
)


def _make_model(logs, contamination=0.1):
    """Helper: build_features + train in one call."""
    logs = build_features(logs)
    return train_model([l["features"] for l in logs], contamination=contamination), logs


# ---------------------------------------------------------------------------
# extract_level
# ---------------------------------------------------------------------------

class TestExtractLevel:
    def test_info(self):
        assert extract_level("INFO server started") == 1

    def test_debug(self):
        assert extract_level("DEBUG tracing variable x") == 0

    def test_warn(self):
        assert extract_level("WARN disk usage high") == 2

    def test_warning_alias(self):
        assert extract_level("WARNING threshold exceeded") == 2

    def test_error(self):
        assert extract_level("ERROR connection refused") == 3

    def test_critical(self):
        assert extract_level("CRITICAL meltdown imminent") == 4

    def test_fatal(self):
        assert extract_level("FATAL kernel panic") == 4

    def test_unknown_defaults_to_info(self):
        assert extract_level("some random text with no level") == 1

    def test_case_insensitive(self):
        assert extract_level("critical disk full") == 4


# ---------------------------------------------------------------------------
# extract_hour
# ---------------------------------------------------------------------------

class TestExtractHour:
    def test_standard_timestamp(self):
        assert extract_hour("2024-01-01 14:32:55 INFO ok") == 14

    def test_midnight(self):
        assert extract_hour("00:00:00 boot") == 0

    def test_no_timestamp(self):
        assert extract_hour("INFO no timestamp here") == -1

    def test_end_of_day(self):
        assert extract_hour("23:59:59 shutdown") == 23


# ---------------------------------------------------------------------------
# build_features
# ---------------------------------------------------------------------------

class TestBuildFeatures:
    def test_adds_features_key(self):
        logs = [{"raw": "INFO ok", "template": "INFO ok", "cluster_id": 1}]
        result = build_features(logs)
        assert "features" in result[0]

    def test_feature_vector_length_is_four(self):
        logs = [{"raw": "ERROR 12:34:56 disk fail", "template": "ERROR disk fail", "cluster_id": 5}]
        build_features(logs)
        assert len(logs[0]["features"]) == 4

    def test_cluster_frequency_counted_correctly(self):
        logs = [
            {"raw": "INFO ok", "template": "INFO ok", "cluster_id": 1},
            {"raw": "INFO ok", "template": "INFO ok", "cluster_id": 1},
            {"raw": "ERROR fail", "template": "ERROR fail", "cluster_id": 2},
        ]
        build_features(logs)
        # cluster_id=1 appears twice, cluster_id=2 once
        assert logs[0]["features"][1] == 2
        assert logs[2]["features"][1] == 1

    def test_hour_extracted(self):
        logs = [{"raw": "INFO 08:30:00 startup", "template": "INFO startup", "cluster_id": 1}]
        build_features(logs)
        assert logs[0]["features"][2] == 8

    def test_template_length_word_count(self):
        logs = [{"raw": "INFO ok", "template": "INFO normal heartbeat ok", "cluster_id": 1}]
        build_features(logs)
        assert logs[0]["features"][3] == 4  # four words in template

    def test_empty_list_returns_empty(self):
        assert build_features([]) == []

    def test_missing_cluster_id_uses_minus_one(self):
        logs = [{"raw": "INFO ok", "template": "INFO ok"}]
        result = build_features(logs)
        assert len(result[0]["features"]) == 4

    def test_all_feature_values_are_numeric(self):
        logs = build_features([
            {"raw": "WARN 11:00:00 threshold", "template": "WARN threshold", "cluster_id": 3}
        ])
        assert all(isinstance(v, (int, float)) for v in logs[0]["features"])


# ---------------------------------------------------------------------------
# train_model
# ---------------------------------------------------------------------------

class TestTrainModel:
    def test_returns_isolation_forest(self):
        from sklearn.ensemble import IsolationForest
        logs = build_features(SAMPLE_LOGS.copy())
        model = train_model([l["features"] for l in logs])
        assert isinstance(model, IsolationForest)

    def test_model_fitted(self):
        logs = build_features(SAMPLE_LOGS.copy())
        model = train_model([l["features"] for l in logs])
        # sklearn sets estimators_ only after fit
        assert hasattr(model, "estimators_")


# ---------------------------------------------------------------------------
# score_logs
# ---------------------------------------------------------------------------

class TestScoreLogs:
    def test_adds_anomaly_score_key(self):
        model, logs = _make_model(SAMPLE_LOGS.copy())
        scored = score_logs(model, logs)
        assert all("anomaly_score" in l for l in scored)

    def test_adds_is_anomaly_key(self):
        model, logs = _make_model(SAMPLE_LOGS.copy())
        scored = score_logs(model, logs)
        assert all("is_anomaly" in l for l in scored)

    def test_anomaly_scores_are_floats(self):
        model, logs = _make_model(SAMPLE_LOGS.copy())
        scored = score_logs(model, logs)
        assert all(isinstance(l["anomaly_score"], float) for l in scored)

    def test_is_anomaly_is_bool(self):
        model, logs = _make_model(SAMPLE_LOGS.copy())
        scored = score_logs(model, logs)
        assert all(isinstance(l["is_anomaly"], bool) for l in scored)

    def test_anomaly_scores_are_finite(self):
        model, logs = _make_model(SAMPLE_LOGS.copy())
        scored = score_logs(model, logs)
        assert all(math.isfinite(l["anomaly_score"]) for l in scored)

    def test_empty_logs_returns_empty(self):
        # Train on real data, score on empty list
        logs = build_features(SAMPLE_LOGS.copy())
        model = train_model([l["features"] for l in logs])
        result = score_logs(model, [])
        assert result == []

    def test_critical_log_flagged_as_anomaly(self):
        """
        With 20 normal INFO entries vs 1 CRITICAL entry, the CRITICAL entry
        must be flagged as anomalous by Isolation Forest.
        This is the key functional requirement for Member 3.
        """
        import copy
        logs = copy.deepcopy(LARGE_LOGS)
        model, scored_logs = _make_model(logs, contamination=0.1)
        scored = score_logs(model, scored_logs)
        critical = scored[-1]  # the CRITICAL entry is last
        assert critical["is_anomaly"] is True, (
            f"CRITICAL log was not flagged. score={critical['anomaly_score']}"
        )

    def test_critical_has_lower_score_than_info(self):
        """Anomaly score for a CRITICAL outlier must be lower than routine INFO entries."""
        import copy
        logs = copy.deepcopy(LARGE_LOGS)
        model, scored_logs = _make_model(logs, contamination=0.1)
        scored = score_logs(model, scored_logs)
        info_scores = [l["anomaly_score"] for l in scored if "CRITICAL" not in l["raw"]]
        critical_score = scored[-1]["anomaly_score"]
        assert critical_score < min(info_scores), (
            "CRITICAL entry should have the lowest anomaly score"
        )

    def test_score_count_matches_log_count(self):
        model, logs = _make_model(SAMPLE_LOGS.copy())
        scored = score_logs(model, logs)
        assert len(scored) == len(SAMPLE_LOGS)


# ---------------------------------------------------------------------------
# print_anomaly_summary
# ---------------------------------------------------------------------------

class TestPrintAnomalySummary:
    def test_runs_without_error(self, capsys):
        model, logs = _make_model(SAMPLE_LOGS.copy())
        scored = score_logs(model, logs)
        print_anomaly_summary(scored)  # must not raise
        captured = capsys.readouterr()
        assert "Stage 4" in captured.out

    def test_shows_total_count(self, capsys):
        model, logs = _make_model(SAMPLE_LOGS.copy())
        scored = score_logs(model, logs)
        print_anomaly_summary(scored)
        captured = capsys.readouterr()
        assert str(len(SAMPLE_LOGS)) in captured.out

    def test_empty_logs_no_crash(self, capsys):
        print_anomaly_summary([])
        captured = capsys.readouterr()
        assert "No logs" in captured.out

