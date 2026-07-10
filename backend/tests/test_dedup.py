"""
test_dedup.py — Unit tests for pipeline/deduplication.py
Run with: pytest tests/test_dedup.py -v
"""

import pytest
from pipeline.deduplication import build_lsh, make_minhash, deduplicate_chunk

# Simulated parsed log dicts (as produced by parser.py)
IDENTICAL_TEMPLATE_LOGS = [
    {"raw": "INFO server started port 8080", "template": "INFO server started port <NUM>", "cluster_id": 1, "parameters": []},
    {"raw": "INFO server started port 9090", "template": "INFO server started port <NUM>", "cluster_id": 1, "parameters": []},
    {"raw": "INFO server started port 3000", "template": "INFO server started port <NUM>", "cluster_id": 1, "parameters": []},
]

UNIQUE_LOGS = [
    {"raw": "INFO  Server started on port 8080",              "template": "INFO server started port <NUM>",       "cluster_id": 1, "parameters": []},
    {"raw": "ERROR Connection refused at node 192.168.1.55",  "template": "ERROR connection refused at node <IP>","cluster_id": 2, "parameters": []},
    {"raw": "CRITICAL DISK USAGE EXCEEDED 95%",               "template": "CRITICAL disk usage exceeded <NUM>%",  "cluster_id": 3, "parameters": []},
]

MIXED_LOGS = IDENTICAL_TEMPLATE_LOGS + [UNIQUE_LOGS[1], UNIQUE_LOGS[2]]


# --- build_lsh tests ---

def test_build_lsh_returns_object():
    lsh = build_lsh()
    assert lsh is not None

def test_build_lsh_custom_threshold():
    lsh = build_lsh(threshold=0.9, num_perm=128)
    assert lsh is not None


# --- make_minhash tests ---

def test_minhash_returns_object():
    mh = make_minhash("INFO server started port <NUM>")
    assert mh is not None

def test_identical_texts_have_equal_minhash():
    mh1 = make_minhash("INFO server started port <NUM>")
    mh2 = make_minhash("INFO server started port <NUM>")
    assert mh1.jaccard(mh2) == 1.0

def test_different_texts_have_lower_jaccard():
    mh1 = make_minhash("INFO server started port <NUM>")
    mh2 = make_minhash("CRITICAL disk full on node <IP>")
    assert mh1.jaccard(mh2) < 0.5


# --- deduplicate_chunk tests ---

def test_identical_template_logs_deduplicated():
    """Three lines with same template -> only 1 should survive."""
    lsh = build_lsh(threshold=0.8)
    unique = deduplicate_chunk(lsh, IDENTICAL_TEMPLATE_LOGS)
    assert len(unique) == 1

def test_all_unique_logs_are_kept():
    """Three completely different templates -> all 3 should survive."""
    lsh = build_lsh(threshold=0.8)
    unique = deduplicate_chunk(lsh, UNIQUE_LOGS)
    assert len(unique) == 3

def test_mixed_logs_correct_count():
    """3 duplicates + 2 unique -> should keep 3 total."""
    lsh = build_lsh(threshold=0.8)
    unique = deduplicate_chunk(lsh, MIXED_LOGS)
    assert len(unique) == 3

def test_output_dicts_have_all_required_keys():
    """All 4 contract keys must be present in output dicts."""
    lsh = build_lsh(threshold=0.8)
    unique = deduplicate_chunk(lsh, UNIQUE_LOGS)
    for u in unique:
        assert "raw"        in u
        assert "template"   in u
        assert "cluster_id" in u
        assert "parameters" in u

def test_critical_log_always_kept():
    """CRITICAL entry is unique — must never be removed."""
    lsh = build_lsh(threshold=0.8)
    unique = deduplicate_chunk(lsh, MIXED_LOGS)
    templates = [u["template"] for u in unique]
    assert any("CRITICAL" in t for t in templates), "CRITICAL log was incorrectly removed"

def test_empty_input_returns_empty():
    lsh = build_lsh()
    unique = deduplicate_chunk(lsh, [])
    assert unique == []

def test_single_entry_always_kept():
    lsh = build_lsh()
    unique = deduplicate_chunk(lsh, [UNIQUE_LOGS[0]])
    assert len(unique) == 1

def test_lsh_persists_across_two_calls():
    """Same LSH index used twice — second chunk's duplicates still caught."""
    lsh = build_lsh(threshold=0.8)
    chunk1 = IDENTICAL_TEMPLATE_LOGS[:1]
    chunk2 = IDENTICAL_TEMPLATE_LOGS[1:]
    unique1 = deduplicate_chunk(lsh, chunk1)
    unique2 = deduplicate_chunk(lsh, chunk2)
    assert len(unique1) + len(unique2) == 1, (
        "LSH should persist across chunks — cross-chunk duplicates must be caught"
    )

def test_stricter_threshold_keeps_more():
    """threshold=0.95 is strict -> fewer entries removed than threshold=0.5."""
    lsh_strict = build_lsh(threshold=0.95)
    unique_strict = deduplicate_chunk(lsh_strict, IDENTICAL_TEMPLATE_LOGS)

    lsh_loose = build_lsh(threshold=0.5)
    unique_loose = deduplicate_chunk(lsh_loose, IDENTICAL_TEMPLATE_LOGS)

    assert len(unique_strict) >= len(unique_loose)