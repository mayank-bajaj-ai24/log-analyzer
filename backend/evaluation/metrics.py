"""
metrics.py — Evaluation helpers for memory, time, compression, and accuracy.

"""

import os
import time
import tracemalloc
from contextlib import contextmanager


@contextmanager
def track_memory():
    """
    Context manager that tracks peak RAM usage in MB.

    Usage:
        with track_memory() as mem:
            run_something()
        print(mem['peak_mb'])
    """
    tracemalloc.start()
    result = {}
    try:
        yield result
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result["current_mb"] = round(current / 1024 / 1024, 3)
        result["peak_mb"] = round(peak / 1024 / 1024, 3)


@contextmanager
def track_time():
    """
    Context manager that measures elapsed wall-clock time in seconds.

    Usage:
        with track_time() as t:
            run_something()
        print(t['elapsed_s'])
    """
    result = {}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["elapsed_s"] = round(time.perf_counter() - start, 3)


def compression_ratio(original_path: str, compressed_path: str) -> float:
    """
    Compute compression ratio: original_size / compressed_size.

    Args:
        original_path: Path to the raw log file.
        compressed_path: Path to the Parquet output file.

    Returns:
        Compression ratio as a float. > 1.0 means compression saved space.
    """
    orig = os.path.getsize(original_path)
    comp = os.path.getsize(compressed_path)
    if comp == 0:
        return float("inf")
    return round(orig / comp, 2)


def f1_score(true_labels: list[int], pred_labels: list[int]) -> dict:
    """
    Compute precision, recall, and F1 for anomaly detection.
    Labels: 1 = anomaly, 0 = normal.

    Args:
        true_labels: Ground-truth binary labels.
        pred_labels: Predicted binary labels from the model.

    Returns:
        Dict with keys: precision, recall, f1.
    """
    tp = sum(t == 1 and p == 1 for t, p in zip(true_labels, pred_labels))
    fp = sum(t == 0 and p == 1 for t, p in zip(true_labels, pred_labels))
    fn = sum(t == 1 and p == 0 for t, p in zip(true_labels, pred_labels))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def dedup_reduction(original_count: int, deduped_count: int) -> float:
    """
    Compute the percentage of entries removed by deduplication.

    Args:
        original_count: Number of entries before dedup.
        deduped_count: Number of entries after dedup.

    Returns:
        Reduction percentage (0-100).
    """
    if original_count == 0:
        return 0.0
    return round((1 - deduped_count / original_count) * 100, 2)
