"""
feature_extraction.py — Stage 4a: Convert parsed logs into numerical feature vectors.

Features used for anomaly detection:
  - log level (encoded as integer)
  - cluster ID frequency
  - hour of day (from timestamp if available)
  - template length (proxy for message complexity)
"""

import re
from collections import Counter

LEVEL_MAP = {
    "DEBUG": 0,
    "INFO": 1,
    "WARN": 2,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "FATAL": 4,
}


def extract_level(raw: str) -> int:
    """Extract log level as an integer from a raw log line."""
    upper = raw.upper()
    for level, code in LEVEL_MAP.items():
        if level in upper:
            return code
    return 1  # default to INFO


def extract_hour(raw: str) -> int:
    """Extract hour of day from common timestamp formats (0-23), or -1 if not found."""
    match = re.search(r"\b(\d{2}):\d{2}:\d{2}\b", raw)
    return int(match.group(1)) if match else -1


def build_features(logs: list[dict]) -> list[dict]:
    """
    Add a 'features' key to each log dict containing a numeric feature vector.

    Feature vector layout (index -> meaning):
        0 — log level      : int 0–4 (DEBUG … CRITICAL/FATAL)
        1 — cluster freq   : int, how many times this cluster_id appears in the batch
        2 — hour of day    : int 0–23, or -1 when no timestamp is found
        3 — template length: int, word count of the Drain3 template

    Args:
        logs: List of parsed log dicts, each containing at minimum:
              'raw' (str), 'template' (str), 'cluster_id' (int).

    Returns:
        Same list with 'features' key added in-place to each entry.
    """
    if not logs:
        return logs

    cluster_counts = Counter(log.get("cluster_id", -1) for log in logs)

    for log in logs:
        cid = log.get("cluster_id", -1)
        raw = log.get("raw", "")
        template = log.get("template", raw)
        
        level = extract_level(raw)
        log["log_level"] = level
        
        log["features"] = [
            level,
            cluster_counts[cid],
            extract_hour(raw),
            len(template.split()),
        ]

    return logs
