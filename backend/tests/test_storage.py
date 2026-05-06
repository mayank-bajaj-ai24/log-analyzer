"""
test_storage.py — Unit tests for pipeline/storage.py
Run with: pytest tests/test_storage.py -v

Author: Mayank Bajaj (1RV24CI066)
"""

import os
import math
import tempfile
import pytest
from pipeline.storage import save_parquet, load_parquet


# ── 10 hardcoded dicts for the roundtrip test ──────────────────────────────
HARDCODED_LOGS = [
    {
        "raw": "2024-01-15 08:00:01 INFO Server started on port 8080",
        "template": "<TIMESTAMP> INFO Server started on port <NUM>",
        "cluster_id": 1,
        "anomaly_score": 0.12,
        "is_anomaly": False,
        "features": [1, 3, 8, 5],
    },
    {
        "raw": "2024-01-15 08:00:02 INFO Database connection established at 192.168.1.10",
        "template": "<TIMESTAMP> INFO Database connection established at <IP>",
        "cluster_id": 2,
        "anomaly_score": 0.08,
        "is_anomaly": False,
        "features": [1, 2, 8, 6],
    },
    {
        "raw": "2024-01-15 08:00:03 DEBUG Loading configuration from config.yaml",
        "template": "<TIMESTAMP> DEBUG Loading configuration from <*>",
        "cluster_id": 3,
        "anomaly_score": 0.15,
        "is_anomaly": False,
        "features": [0, 1, 8, 5],
    },
    {
        "raw": "2024-01-15 08:00:04 WARNING Cache miss for key user_session_99",
        "template": "<TIMESTAMP> WARNING Cache miss for key <*>",
        "cluster_id": 4,
        "anomaly_score": 0.05,
        "is_anomaly": False,
        "features": [2, 1, 8, 7],
    },
    {
        "raw": "2024-01-15 08:00:05 ERROR Connection refused at node 172.16.0.3",
        "template": "<TIMESTAMP> ERROR Connection refused at node <IP>",
        "cluster_id": 5,
        "anomaly_score": -0.21,
        "is_anomaly": True,
        "features": [3, 2, 8, 7],
    },
    {
        "raw": "2024-01-15 08:00:06 INFO Request processed in 120ms",
        "template": "<TIMESTAMP> INFO Request processed in <NUM>ms",
        "cluster_id": 6,
        "anomaly_score": 0.11,
        "is_anomaly": False,
        "features": [1, 4, 8, 6],
    },
    {
        "raw": "2024-01-15 08:00:07 CRITICAL DISK USAGE EXCEEDED 95%",
        "template": "<TIMESTAMP> CRITICAL DISK USAGE EXCEEDED <NUM>%",
        "cluster_id": 7,
        "anomaly_score": -0.34,
        "is_anomaly": True,
        "features": [4, 1, 8, 6],
    },
    {
        "raw": "2024-01-15 08:00:08 INFO User login successful for user_42",
        "template": "<TIMESTAMP> INFO User login successful for <*>",
        "cluster_id": 8,
        "anomaly_score": 0.09,
        "is_anomaly": False,
        "features": [1, 2, 8, 6],
    },
    {
        "raw": "2024-01-15 08:00:09 WARNING Memory threshold exceeded: 89%",
        "template": "<TIMESTAMP> WARNING Memory threshold exceeded: <NUM>%",
        "cluster_id": 9,
        "anomaly_score": -0.02,
        "is_anomaly": False,
        "features": [2, 1, 8, 5],
    },
    {
        "raw": "2024-01-15 08:00:10 INFO Scheduled job cron_cleanup completed",
        "template": "<TIMESTAMP> INFO Scheduled job <*> completed",
        "cluster_id": 10,
        "anomaly_score": 0.13,
        "is_anomaly": False,
        "features": [1, 1, 8, 5],
    },
]


# ── Smaller sample used by legacy tests ────────────────────────────────────
SAMPLE_LOGS = [
    {
        "raw": "2024-01-15 08:00:01 INFO Server started on port 8080",
        "template": "<TIMESTAMP> INFO Server started on port <NUM>",
        "cluster_id": 1,
        "anomaly_score": 0.12,
        "is_anomaly": False,
        "features": [1, 3, 8, 5],
    },
    {
        "raw": "2024-01-15 08:00:14 CRITICAL DISK USAGE EXCEEDED 95%",
        "template": "<TIMESTAMP> CRITICAL DISK USAGE EXCEEDED <NUM>%",
        "cluster_id": 9,
        "anomaly_score": -0.34,
        "is_anomaly": True,
        "features": [4, 1, 8, 6],
    },
    {
        "raw": "2024-01-15 08:00:10 ERROR Connection refused at node 192.168.1.55",
        "template": "<TIMESTAMP> ERROR Connection refused at node <IP>",
        "cluster_id": 6,
        "anomaly_score": -0.21,
        "is_anomaly": True,
        "features": [3, 2, 8, 7],
    },
]


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


# ═══════════════════════════════════════════════════════════════════════════
#  Core roundtrip test — save 10 hardcoded dicts, reload, verify match
# ═══════════════════════════════════════════════════════════════════════════

def test_roundtrip_10_hardcoded_dicts(tmp_dir):
    """Save 10 hardcoded log dicts to Parquet and reload — they must match."""
    path = save_parquet(HARDCODED_LOGS, tmp_dir, "roundtrip.parquet")
    loaded = load_parquet(path)

    assert len(loaded) == 10, f"Expected 10 records, got {len(loaded)}"

    for original, reloaded in zip(HARDCODED_LOGS, loaded):
        assert reloaded["raw"] == original["raw"]
        assert reloaded["template"] == original["template"]
        assert reloaded["cluster_id"] == original["cluster_id"]
        assert reloaded["is_anomaly"] == original["is_anomaly"]
        # float32 loses precision, so use approximate comparison
        assert math.isclose(
            reloaded["anomaly_score"],
            original["anomaly_score"],
            abs_tol=1e-3,
        ), f"Score mismatch: {reloaded['anomaly_score']} vs {original['anomaly_score']}"


# ═══════════════════════════════════════════════════════════════════════════
#  save_parquet tests
# ═══════════════════════════════════════════════════════════════════════════

def test_save_creates_file(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    assert os.path.exists(path)

def test_save_returns_valid_path(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    assert path.endswith(".parquet")

def test_save_creates_output_dir_if_missing(tmp_dir):
    new_dir = os.path.join(tmp_dir, "nested", "output")
    path = save_parquet(SAMPLE_LOGS, new_dir)
    assert os.path.exists(path)

def test_saved_file_is_nonzero(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    assert os.path.getsize(path) > 0

def test_save_custom_filename(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir, filename="custom.parquet")
    assert path.endswith("custom.parquet")
    assert os.path.exists(path)


# ═══════════════════════════════════════════════════════════════════════════
#  load_parquet tests
# ═══════════════════════════════════════════════════════════════════════════

def test_load_returns_list(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    loaded = load_parquet(path)
    assert isinstance(loaded, list)

def test_load_returns_correct_count(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    loaded = load_parquet(path)
    assert len(loaded) == len(SAMPLE_LOGS)

def test_load_preserves_raw(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    loaded = load_parquet(path)
    raws = [l["raw"] for l in loaded]
    for original in SAMPLE_LOGS:
        assert original["raw"] in raws

def test_load_preserves_template(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    loaded = load_parquet(path)
    templates = [l["template"] for l in loaded]
    for original in SAMPLE_LOGS:
        assert original["template"] in templates

def test_load_preserves_cluster_id(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    loaded = load_parquet(path)
    ids = [l["cluster_id"] for l in loaded]
    for original in SAMPLE_LOGS:
        assert original["cluster_id"] in ids

def test_load_preserves_is_anomaly(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    loaded = load_parquet(path)
    anomaly_flags = [l["is_anomaly"] for l in loaded]
    assert True in anomaly_flags
    assert False in anomaly_flags

def test_load_preserves_anomaly_score(tmp_dir):
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    loaded = load_parquet(path)
    for l in loaded:
        assert isinstance(l["anomaly_score"], float)

def test_load_preserves_log_level(tmp_dir):
    """log_level column (extracted from features[0]) must survive roundtrip."""
    path = save_parquet(SAMPLE_LOGS, tmp_dir)
    loaded = load_parquet(path)
    for l in loaded:
        assert "log_level" in l
        assert isinstance(l["log_level"], int)


# ═══════════════════════════════════════════════════════════════════════════
#  Edge-case tests
# ═══════════════════════════════════════════════════════════════════════════

def test_save_empty_list(tmp_dir):
    path = save_parquet([], tmp_dir)
    loaded = load_parquet(path)
    assert loaded == []

def test_save_single_record(tmp_dir):
    path = save_parquet([SAMPLE_LOGS[0]], tmp_dir)
    loaded = load_parquet(path)
    assert len(loaded) == 1
    assert loaded[0]["raw"] == SAMPLE_LOGS[0]["raw"]

def test_missing_fields_get_defaults(tmp_dir):
    """Dicts with missing keys should get safe defaults, not crash."""
    sparse = [{"raw": "bare minimum log line"}]
    path = save_parquet(sparse, tmp_dir)
    loaded = load_parquet(path)
    assert len(loaded) == 1
    assert loaded[0]["raw"] == "bare minimum log line"
    assert loaded[0]["template"] == ""
    assert loaded[0]["cluster_id"] == -1
    assert loaded[0]["is_anomaly"] is False

def test_compression_reduces_size(tmp_dir):
    """Parquet file should be smaller than naive estimate of raw text size."""
    big_logs = SAMPLE_LOGS * 100
    path = save_parquet(big_logs, tmp_dir)
    parquet_size = os.path.getsize(path)
    raw_size = sum(len(l["raw"].encode()) for l in big_logs)
    assert parquet_size < raw_size

def test_overwrite_existing_file(tmp_dir):
    """Saving twice to the same path should overwrite cleanly."""
    path1 = save_parquet(SAMPLE_LOGS[:1], tmp_dir)
    path2 = save_parquet(SAMPLE_LOGS, tmp_dir)
    assert path1 == path2
    loaded = load_parquet(path2)
    assert len(loaded) == len(SAMPLE_LOGS)