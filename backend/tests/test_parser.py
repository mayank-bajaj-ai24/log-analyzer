"""
test_parser.py — Unit tests for pipeline/parser.py
Run with: pytest tests/test_parser.py -v
"""

import pytest
from pipeline.parser import build_parser, parse_chunk, parse_line

SAMPLE_LOGS = [
    "2024-01-15 08:00:01 INFO  Server started on port 8080",
    "2024-01-15 08:00:02 INFO  Server started on port 9090",
    "2024-01-15 08:00:03 ERROR Connection refused at node 192.168.1.55 port 5432",
    "2024-01-15 08:00:04 DEBUG Heartbeat sent to coordinator node",
    "2024-01-15 08:00:05 DEBUG Heartbeat sent to coordinator node",
    "2024-01-15 08:00:06 CRITICAL DISK USAGE EXCEEDED 95% ON NODE worker-3",
]


# --- Output structure tests ---

def test_parse_chunk_returns_list_of_dicts():
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS)
    assert isinstance(results, list)
    assert len(results) == len(SAMPLE_LOGS)

def test_every_dict_has_required_keys():
    """Contract for Member 3: every dict must have exactly these 4 keys."""
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS)
    for r in results:
        assert "raw"        in r, "missing key: raw"
        assert "template"   in r, "missing key: template"
        assert "cluster_id" in r, "missing key: cluster_id"
        assert "parameters" in r, "missing key: parameters"

def test_raw_is_original_line():
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS)
    for r, original in zip(results, SAMPLE_LOGS):
        assert r["raw"] == original

def test_cluster_id_is_int():
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS)
    for r in results:
        assert isinstance(r["cluster_id"], int)

def test_template_is_string():
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS)
    for r in results:
        assert isinstance(r["template"], str)
        assert len(r["template"]) > 0

def test_parameters_is_list():
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS)
    for r in results:
        assert isinstance(r["parameters"], list)


# --- Clustering correctness tests ---

def test_similar_logs_share_same_template():
    """Server started on port 8080 and 9090 must cluster together."""
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS[:2])
    assert results[0]["template"] == results[1]["template"], (
        "Similar lines should produce the same template"
    )

def test_similar_logs_share_same_cluster_id():
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS[:2])
    assert results[0]["cluster_id"] == results[1]["cluster_id"]

def test_different_logs_get_different_cluster_ids():
    miner = build_parser()
    results = parse_chunk(miner, SAMPLE_LOGS)
    ids = [r["cluster_id"] for r in results]
    assert len(set(ids)) > 1, "All lines got the same cluster — parser is not discriminating"

def test_identical_lines_get_same_cluster():
    """Heartbeat lines are identical — must be same cluster."""
    miner = build_parser()
    heartbeats = [SAMPLE_LOGS[3], SAMPLE_LOGS[4]]
    results = parse_chunk(miner, heartbeats)
    assert results[0]["cluster_id"] == results[1]["cluster_id"]

def test_template_masks_ip_addresses():
    miner = build_parser()
    result = parse_line(miner, "2024-01-15 08:00:03 ERROR Connection refused at node 192.168.1.55 port 5432")
    assert "192.168.1.55" not in result["template"], "IP address should be masked in template"

def test_template_masks_port_numbers():
    miner = build_parser()
    result = parse_line(miner, "2024-01-15 08:00:01 INFO Server started on port 8080")
    assert "8080" not in result["template"], "Port number should be masked in template"

def test_empty_chunk_returns_empty_list():
    miner = build_parser()
    results = parse_chunk(miner, [])
    assert results == []

def test_single_line_chunk():
    miner = build_parser()
    results = parse_chunk(miner, [SAMPLE_LOGS[0]])
    assert len(results) == 1
    assert results[0]["raw"] == SAMPLE_LOGS[0]